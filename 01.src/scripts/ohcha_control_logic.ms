/*
================================================================================
  Project:      ohCHA Rig Manager - Control Logic Module
  Description:  [v21.03] Control Logic Restored.
                - Integrity: Exact copy of original Inspector logic.
================================================================================
*/

global ohCHA_ControlLogic = undefined
gc light:true

struct OhchaControlLogic_Struct
(
    fn _recurseController ctrl parentIndex depth dataArray = (
        if ctrl == undefined do return ()
        local numSubs = ctrl.numSubs
        for i = 1 to numSubs do (
            local subCtrl = ctrl[i].controller
            local subName = getSubAnimName ctrl i
            local ctrlType = "None"
            local isLeaf = true
            if subCtrl != undefined do (
                ctrlType = (classof subCtrl) as string
                if subCtrl.numSubs > 0 do isLeaf = false
            )
            local myIndex = dataArray.count + 1
            append dataArray #(myIndex, parentIndex, subName, ctrlType, depth, i)
            if not isLeaf and subCtrl != undefined do ( _recurseController subCtrl myIndex (depth + 1) dataArray )
        )
    ),

    fn getControllerTree obj = (
        if not (isValidNode obj) do return #()
        local dataArray = #()
        local baseCtrl = obj.controller
        append dataArray #(1, 0, "Transform", (classof baseCtrl) as string, 0, 0)
        _recurseController baseCtrl 1 1 dataArray
        return dataArray
    ),

    fn getNodeInfo obj = (
        if not (isValidNode obj) do return undefined
        local info = dotNetObject "System.Collections.Hashtable"
        info.Add "Name" obj.name
        info.Add "Class" ((classof obj) as string)
        info.Add "Handle" (obj.handle as string)
        info.Add "WireColor" (obj.wirecolor as string)
        info.Add "Pos" (obj.pos as string)
        info.Add "Rot" ((obj.rotation as eulerAngles) as string)
        info.Add "Scale" (obj.scale as string)
        if obj.parent != undefined then info.Add "Parent" obj.parent.name else info.Add "Parent" "None"
        local cn = ""
        for c in obj.children do cn += (c.name + ", ")
        if cn.count > 2 do cn = substring cn 1 (cn.count - 2)
        info.Add "Children" cn
        return info
    ),

    fn _navigateCtrl obj indicesPath = (
        local currentCtrl = obj.controller
        try ( for idx in indicesPath do ( if currentCtrl == undefined do return undefined; currentCtrl = currentCtrl[idx].controller ); return currentCtrl ) catch ( return undefined )
    ),

    fn getControllerDetails obj indicesPath = (
        local ctrl = _navigateCtrl obj indicesPath
        if ctrl == undefined do return undefined
        local cClass = classof ctrl
        local isScript = (cClass == float_script or cClass == position_script or cClass == rotation_script or cClass == scale_script or cClass == transform_script)
        local isExpr = (cClass == float_expression or cClass == position_expression or cClass == rotation_expression or cClass == scale_expression)
        local isConstraint = (cClass == Position_Constraint or cClass == Orientation_Constraint or cClass == LookAt_Constraint)
        local result = dotNetObject "System.Collections.Hashtable"
        result.Add "type" (cClass as string)
        result.Add "is_script" isScript
        result.Add "is_expr" isExpr
        result.Add "is_constraint" isConstraint
        if isScript then ( result.Add "script" (ctrl.script as string) )
        else if isExpr then ( result.Add "expression" (ctrl.getExpression() as string) )
        else if isConstraint then (
            local targets = dotNetObject "System.Collections.ArrayList"
            local count = ctrl.getNumTargets()
            for i = 1 to count do (
                local node = ctrl.getNode i
                local weight = ctrl.getWeight i
                local nodeName = if isValidNode node then node.name else "Deleted"
                targets.Add (nodeName + "|" + (weight as string))
            )
            result.Add "targets" targets
        )
        return result
    ),

    fn assignController obj indicesPath typeStr initialCode = (
        if not (isValidNode obj) do return false
        try (
            local targetSubAnim = obj.controller
            if indicesPath.count == 0 then return false
            for i = 1 to (indicesPath.count - 1) do targetSubAnim = targetSubAnim[indicesPath[i]].controller
            local finalIndex = indicesPath[indicesPath.count]
            if typeStr == "Link_Constraint" and (classof targetSubAnim != PRS) do return false
            local newCtrl = execute (typeStr + "()")
            if initialCode != "" and (hasProperty newCtrl "script") do newCtrl.script = initialCode
            targetSubAnim[finalIndex].controller = newCtrl
            return true
        ) catch ( return false )
    ),

    fn applyScriptText obj indicesPath code = (
        local ctrl = _navigateCtrl obj indicesPath
        if ctrl == undefined do return false
        try (
             local cClass = classof ctrl
             if (cClass == float_script or cClass == position_script or cClass == rotation_script or cClass == scale_script or cClass == transform_script) then ( ctrl.script = code; return true )
             else if (cClass == float_expression or cClass == position_expression or cClass == rotation_expression or cClass == scale_expression) then ( ctrl.SetExpression code; return true )
             return false
        ) catch ( return false )
    ),

    fn addConstraintTarget obj indicesPath targetObj = (
        local ctrl = _navigateCtrl obj indicesPath
        if ctrl == undefined or not (isValidNode targetObj) do return false
        try ( ctrl.appendTarget targetObj 50.0; return true ) catch ( return false )
    ),

    fn removeConstraintTarget obj indicesPath index = (
        local ctrl = _navigateCtrl obj indicesPath
        if ctrl == undefined do return false
        try ( ctrl.deleteTarget index; return true ) catch ( return false )
    ),

    fn setConstraintWeight obj indicesPath index weightVal = (
        local ctrl = _navigateCtrl obj indicesPath
        if ctrl == undefined do return false
        try ( ctrl.setWeight index weightVal; return true ) catch ( return false )
    )
)
global ohCHA_ControlLogic = OhchaControlLogic_Struct()