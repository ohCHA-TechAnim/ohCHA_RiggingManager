--- START OF FILE ohcha_bone_logic.txt ---

/*
================================================================================
  Project:      ohCHA Rig Manager - Bone Logic Module
  Description:  [v21.42] STRETCH STABILITY FIX.
                - CRITICAL FIX: Changed Hashtable to store Handles instead of Nodes
                  to prevent 'Deleted scene node' System.Object error.
================================================================================
*/

global ohCHA_BoneLogic = undefined
global ohCHA_PoseBuffer = #()
gc light:true

struct OhchaBoneLogic_Struct
(
    fn _checkShapeUtils = (
        if (globalVars.get "ohCHA_ShapeUtils") == undefined do (
            print "❌ [BoneLogic] Dependency Error: 'ohCHA_ShapeUtils' not loaded."
            return false
        )
        return true
    ),

    fn _collectHierarchy node arr = (
        if isValidNode node do (
            append arr node
            for c in node.children do _collectHierarchy c arr
        )
    ),

    -- ============================================================================
    -- [1] Twist Bone Logic
    -- ============================================================================
    fn createTwistBoneChain targetNode count namePrefix isChildDriven =
    (
        if not isValidNode targetNode do return false
        local children = targetNode.children
        if children.count == 0 do return false
        local endNode = children[1]
        local parentNode = targetNode.parent
        if not isValidNode parentNode do return false

        local p1 = targetNode.transform.pos
        local p2 = endNode.transform.pos
        local vec = p2 - p1
        local fullLen = length vec
        local segLen = fullLen / count
        local prevBone = undefined
        local isLeg = (findString targetNode.name "Thigh" != undefined) or (findString targetNode.name "Calf" != undefined) or (findString targetNode.name "Leg" != undefined)

        undo "Create Twist Bones" on (
            for i = 1 to count do (
                local startPos = p1 + (normalize vec) * (segLen * (i-1))
                local endPos = p1 + (normalize vec) * (segLen * i)
                local zAxis = targetNode.transform.row3
                local newBone = boneSys.createBone startPos endPos zAxis
                newBone.name = namePrefix + "_" + (i as string)
                newBone.width = 4; newBone.height = 4
                newBone.wirecolor = targetNode.wirecolor

                newBone.rotation.controller = rotation_list()
                newBone.rotation.controller[1].controller = Euler_XYZ()
                local scriptCtrl = rotation_script()
                newBone.rotation.controller.available.controller = scriptCtrl

                if i == 1 then (
                    scriptCtrl.addNode "SrcNode" targetNode
                    scriptCtrl.addNode "ParNode" parentNode
                    if isLeg then (
                         scriptCtrl.addNode "AimTgt" endNode
                         scriptCtrl.script = "dir = normalize (AimTgt.transform.pos - SrcNode.transform.pos)\nupRef = ParNode.transform.row3\nside = cross upRef dir\nif (length side < 0.001) then side = cross [0,1,0] dir\nside = normalize side\nstableUp = normalize (cross dir side)\nstableMat = matrix3 dir side stableUp SrcNode.transform.pos\nstableMat.rotation * inverse SrcNode.transform.rotation"
                    ) else (
                        scriptCtrl.script = "relTM = SrcNode.transform * inverse ParNode.transform\ndir = normalize relTM.row1\naxis = cross dir [1,0,0]\nif (length axis < 0.0001) then axis = [0,0,1] else axis = normalize axis\nang = acos (dot dir [1,0,0])\nnoRollQuat = (angleaxis ang axis) as quat\nnoRollQuat * inverse relTM.rotation"
                    )
                ) else (
                    local bone1Name = namePrefix + "_1"
                    scriptCtrl.addNode "Anchor" (getNodeByName bone1Name)
                    local weightVal = 1.0 / ((count - 1) as float)
                    if isChildDriven and i == count do weightVal = 1.0
                    scriptCtrl.addConstant "W" weightVal
                    scriptCtrl.addNode "TgtNode" (if isChildDriven then endNode else targetNode)

                    if isLeg then (
                        scriptCtrl.script = "relZ = TgtNode.transform.row3 * inverse Anchor.transform.rotation\nprojZ = normalize [0, relZ.y, relZ.z]\ntotalAng = atan2 projZ.y projZ.z\n(angleaxis (totalAng * W) [1,0,0]) as quat"
                    ) else (
                        scriptCtrl.addNode "RefBone" prevBone
                        scriptCtrl.script = "relQ = TgtNode.transform.rotation * inverse Anchor.transform.rotation\nif (W > 0.99) then relQ = TgtNode.transform.rotation * inverse RefBone.transform.rotation\ntwistQ = normalize (quat relQ.x 0 0 relQ.w)\nslerp (quat 0 0 0 1) twistQ W"
                    )
                )

                if prevBone != undefined then newBone.parent = prevBone else newBone.parent = targetNode
                prevBone = newBone
            )
        )
        return true
    ),

    -- ============================================================================
    -- [2] Stretch Logic (Chain Aware & Auto End-Bone)
    -- ============================================================================
    fn applyStretchToSelection ctrlSize =
    (
        if not (this._checkShapeUtils()) do return false
        local sel = selection as array
        if sel.count == 0 do ( print "⚠️ No bones selected."; return false )

        -- Store EndPins created for each bone: Key=BoneHandle(String), Value=EndPinHandle(Integer)
        -- ⭐️ FIX: Storing Handles instead of Nodes to prevent crash
        local endPinMap = dotNetObject "System.Collections.Hashtable"

        undo "Apply Stretch" on
        (
            for bn in sel do
            (
                if not (isValidNode bn) do continue
                
                local size = if ctrlSize != undefined then ctrlSize else 20.0
                local childBn = undefined
                
                -- [Check Children]
                if bn.children.count > 0 then (
                    childBn = bn.children[1]
                ) else (
                    -- [Create End Bone] If no children exist
                    format "ℹ️ Creating End Bone for '%'\n" bn.name
                    
                    local len = 0.0
                    try (len = bn.length) catch()
                    if len == undefined or len < 0.1 do len = size 
                    
                    local tm = bn.transform
                    local p1 = tm.pos
                    local p2 = p1 + (normalize tm.row1 * len)
                    
                    childBn = boneSys.createBone p1 p2 tm.row3
                    childBn.name = bn.name + "_end"
                    childBn.width = bn.width * 0.7
                    childBn.height = bn.height * 0.7
                    childBn.taper = 90
                    childBn.wirecolor = bn.wirecolor
                    childBn.parent = bn
                    
                    childBn.transform = tm
                    in coordsys local move childBn [len, 0, 0]
                )

                local startPin = undefined
                local isChainStart = true

                -- [Check Chain] If parent was processed, reuse its EndPin as StartPin
                if isValidNode bn.parent do (
                    local pHandle = bn.parent.handle as string
                    if endPinMap.ContainsKey pHandle do (
                        -- ⭐️ Retrieve Node from Handle
                        local pinHandle = endPinMap.Item[pHandle]
                        local foundPin = maxOps.getNodeByHandle (pinHandle as integer)
                        
                        if isValidNode foundPin do (
                            startPin = foundPin
                            isChainStart = false
                            format "🔗 Link: % -> %\n" bn.name startPin.name
                        )
                    )
                )

                -- [3] Create Start Pin (Only if not linked from parent)
                if isChainStart do (
                    startPin = ohCHA_ShapeUtils.createPinShape size
                    startPin.name = "Ctrl_" + bn.name + "_Start"
                    startPin.transform = bn.transform
                    startPin.wirecolor = yellow
                    if isValidNode bn.parent do startPin.parent = bn.parent
                    
                    -- [5] Constraint 1: Bone -> Start Pin (Position)
                    bn.position.controller = Position_Constraint()
                    bn.position.controller.appendTarget startPin 100.0
                )

                -- [4] Create End Pin
                local endPin = ohCHA_ShapeUtils.createPinShape size
                endPin.name = "Ctrl_" + bn.name + "_End"
                endPin.transform = childBn.transform
                endPin.wirecolor = yellow
                
                -- Link End to Start
                if isValidNode startPin do endPin.parent = startPin 

                -- ⭐️ Store Handle for next link
                endPinMap.Add (bn.handle as string) (endPin.handle)

                -- [6] Constraint 2: Bone -> End Pin (LookAt)
                bn.rotation.controller = LookAt_Constraint()
                bn.rotation.controller.appendTarget endPin 100.0
                if isValidNode startPin do bn.rotation.controller.pickUpNode = startPin 
                bn.rotation.controller.upnode_world = off
                bn.rotation.controller.viewline_length_abs = off

                -- [7] Constraint 3: Child -> End Pin (Position)
                childBn.position.controller = Position_Constraint()
                childBn.position.controller.appendTarget endPin 100.0

                -- [8] Freeze Length OFF
                bn.boneFreezeLength = false
                
                format "✅ Stretch Done: %\n" bn.name
            )
        )
        return true
    ),

    -- ============================================================================
    -- [3] Custom Chain
    -- ============================================================================
    fn createCustomBoneChain posList nameBase w h t sideFin frontFin backFin =
    (
        if posList.count < 2 do return false
        undo "Create Bone Chain" on (
            local prevBone = undefined
            local bones = #()
            for i = 1 to (posList.count - 1) do (
                local p1 = posList[i]
                local p2 = posList[i+1]
                local zAxis = [0,0,1]
                if (distance p1 p2) < 0.001 do continue
                local bn = boneSys.createBone p1 p2 zAxis
                if isValidNode bn then (
                    bn.name = nameBase + "_" + (i as string)
                    bn.width = w; bn.height = h; bn.taper = t
                    try (
                        if sideFin do ( bn.sidefins = on; bn.sidefinssize = w * 0.8 )
                        if frontFin do ( bn.frontfin = on; bn.frontfinheight = h * 0.8 )
                        if backFin do ( bn.backfin = on; bn.backfinheight = h * 0.8 )
                    ) catch()
                    if prevBone != undefined do bn.parent = prevBone
                    prevBone = bn
                    append bones bn
                )
            )
            select bones
        )
    ),

    -- ============================================================================
    -- [4] Mirror Gizmo Creation
    -- ============================================================================
    fn createMirrorGizmo sizeVal =
    (
        local finalSize = sizeVal
        if finalSize == undefined or finalSize < 0.1 do finalSize = 20.0
        undo "Create Mirror Gizmo" on (
            local duplicates = for o in objects where o.name == "Helper_Mirror_Plane" collect o
            for o in duplicates do delete o
            local p = Point()
            p.pos = [0,0,0]
            p.transform = matrix3 1
            p.name = "Helper_Mirror_Plane"
            p.size = finalSize
            p.box = true
            p.cross = false 
            p.axisTripod = true
            p.centerMarker = false
            p.wirecolor = (color 255 0 0)
            p.renderable = false
            p.isHidden = false
            p.isFrozen = false
            select p
            redrawViews()
            p 
        )
    ),

    -- ============================================================================
    -- [5] Mirror Logic
    -- ============================================================================
    fn _getMirrorMatrix nCenter nBefore axis =
    (
        local tempPoint = Point pos:[0,0,0]
        tempPoint.transform = nBefore.transform * inverse nCenter.transform
        local row1 = tempPoint.transform.row1
        local row2 = tempPoint.transform.row2
        local row3 = tempPoint.transform.row3
        local row4 = tempPoint.transform.row4

        if axis == "X" then ( row1 *= [-1,1,1]; row2 *= [1,-1,-1]; row3 *= [-1,1,1]; row4 *= [-1,1,1] )
        else if axis == "Y" then ( row1 *= [1,-1,1]; row2 *= [-1,1,-1]; row3 *= [1,-1,1]; row4 *= [1,-1,1] )
        else if axis == "Z" then ( row1 *= [1,1,-1]; row2 *= [-1,-1,1]; row3 *= [1,1,-1]; row4 *= [1,1,-1] )
        else if axis == "XY" then ( row1 *= [-1,-1,1]; row2 *= [-1,-1,1]; row3 *= [-1,-1,1]; row4 *= [-1,-1,1] )
        else if axis == "YZ" then ( row1 *= [1,-1,-1]; row2 *= [1,-1,-1]; row3 *= [1,-1,-1]; row4 *= [1,-1,-1] )
        else if axis == "ZX" then ( row1 *= [-1,1,-1]; row2 *= [-1,1,-1]; row3 *= [-1,1,-1]; row4 *= [-1,1,-1] )

        local newLocalTm = matrix3 row1 row2 row3 row4
        delete tempPoint
        return newLocalTm * nCenter.transform
    ),

    fn mirrorBonesAdvanced sourceNodes gizmoObj axisMode flipMode offsetVal = (
        if not isValidNode gizmoObj do ( print "❌ [BoneLogic] Gizmo invalid."; return false )
        undo "Mirror Bones" on (
            maxOps.cloneNodes sourceNodes cloneType:#copy newNodes:&newBones
            local nodeMap = dotNetObject "System.Collections.Hashtable"
            for i = 1 to sourceNodes.count do ( if isValidNode newBones[i] do nodeMap.Add (sourceNodes[i].handle as string) (newBones[i].handle) )

            for i = 1 to newBones.count do (
                local obj = newBones[i]; local orig = sourceNodes[i]
                if matchPattern orig.name pattern:"*L_*" then obj.name = substituteString orig.name "L_" "R_"
                else if matchPattern orig.name pattern:"*R_*" then obj.name = substituteString orig.name "R_" "L_"
                else obj.name = orig.name + "_Mirrored"

                if (classof orig == BoneGeometry) do obj.boneEnable = orig.boneEnable
                local mirroredTM = this._getMirrorMatrix gizmoObj orig axisMode
                if axisMode == "X" then mirroredTM.pos.x += offsetVal
                else if axisMode == "Y" then mirroredTM.pos.y += offsetVal
                else if axisMode == "Z" then mirroredTM.pos.z += offsetVal
                obj.transform = mirroredTM

                if flipMode == "Y" then ( in coordsys local rotate obj (eulerAngles 0 180 0) )
                else if flipMode == "Z" then ( in coordsys local rotate obj (eulerAngles 0 0 180) )

                if (isValidNode orig.parent) do (
                    local parentHandle = orig.parent.handle as string
                    if (nodeMap.ContainsKey parentHandle) do (
                        local newParent = maxOps.getNodeByHandle (nodeMap.Item[parentHandle] as integer)
                        if isValidNode newParent do obj.parent = newParent
                    )
                )
            )
            select newBones
        )
    ),

    -- ============================================================================
    -- [6] Color & Pose
    -- ============================================================================
    fn colorNodeList nodes startCol endCol = (
        local count = nodes.count
        if count == 0 do return false
        undo "Color List" on (
            for i = 1 to count do (
                local ratio = 0.0
                if count > 1 do ratio = ((i-1) as float) / ((count-1) as float)
                local r = startCol.r * (1.0 - ratio) + endCol.r * ratio
                local g = startCol.g * (1.0 - ratio) + endCol.g * ratio
                local b = startCol.b * (1.0 - ratio) + endCol.b * ratio
                if isValidNode nodes[i] do nodes[i].wirecolor = color r g b
            )
        )
    ),

    fn colorHierarchy rootNode startCol endCol = (
        local allNodes = #()
        this._collectHierarchy rootNode allNodes
        this.colorNodeList allNodes startCol endCol
    ),

    fn copyPose nodes = (
        ohCHA_PoseBuffer = #()
        for obj in nodes do (
            if isValidNode obj do append ohCHA_PoseBuffer #(obj.name, obj.transform)
        )
        print ("📋 Copied " + (ohCHA_PoseBuffer.count as string) + " poses.")
    ),

    fn pastePose nodes = (
        if ohCHA_PoseBuffer.count == 0 do return false
        undo "Paste Pose" on (
            for obj in nodes do (
                for data in ohCHA_PoseBuffer do ( if data[1] == obj.name do ( obj.transform = data[2]; exit ) )
            )
        )
        print "✅ Paste Done."
    ),

    fn pasteMirrorPose nodes axis = (
        if ohCHA_PoseBuffer.count == 0 do return false
        undo "Mirror Paste Pose" on (
            for obj in nodes do (
                local targetName = ""
                if matchPattern obj.name pattern:"*L_*" then targetName = substituteString obj.name "L_" "R_"
                else if matchPattern obj.name pattern:"*R_*" then targetName = substituteString obj.name "R_" "L_"
                else targetName = obj.name
                for data in ohCHA_PoseBuffer do (
                    if data[1] == targetName do (
                        local sourceTM = data[2]
                        local mTM = matrix3 1
                        if axis == "X" then mTM.row1 = [-1,0,0] else if axis == "Y" then mTM.row2 = [0,-1,0]
                        local mirroredTM = sourceTM * mTM
                        preRotateY mirroredTM 180
                        obj.transform = mirroredTM
                        exit
                    )
                )
            )
        )
        print "✅ Mirror Paste Done."
    )
)
global ohCHA_BoneLogic = OhchaBoneLogic_Struct()
print "✅ [Module] BoneLogic Loaded (Handle Safe)."