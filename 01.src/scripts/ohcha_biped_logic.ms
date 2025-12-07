/*
================================================================================
  Project:      ohCHA Rig Manager - Biped Logic Module
  Description:  [v21.08] STRICT ORIGINAL LOGIC RESTORED.
                - FIXED: fit_clavicle_maxscript now strictly follows the
                  original Figure Mode toggling sequence to prevent twisting.
                - FIXED: fit_bone_aim uses exact vector math from reference.
================================================================================
*/

global ohCHA_BipedLogic = undefined
gc light:true

struct OhchaBipedLogic_Struct
(
    -- ============================================================================
    -- [1] Utility Functions
    -- ============================================================================
    fn _getBipedRootCtrl obj = (
        if not (isValidNode obj) do return undefined
        if (classof obj == Biped_Object) then return obj.controller.rootNode.controller
        else if (classof obj.controller == Vertical_Horizontal_Turn) then return obj.controller
        undefined
    ),

    fn collect_names node lst = (
        if isValidNode node do (
            append lst node.Name
            for c in node.children do collect_names c lst
        )
    ),

    fn cleanupGuides = (
        delete (for o in objects where matchPattern o.name pattern:"Guide_*" collect o)
    ),

    -- ============================================================================
    -- [2] Biped Creation & Structure
    -- ============================================================================

    fn generateAndFitBiped configDict =
    (
        -- 1. Cleanup Old
        local oldBip = getNodeByName "Bip001"
        if isValidNode oldBip do delete oldBip

        -- 2. Create New
        local root = biped.createNew 180 -90 [0,0,173]
        if not (isValidNode root) do return false
        root.name = "Bip001"

        -- 3. Set Structure
        local ctrl = root.controller
        if not ctrl.figureMode do ctrl.figureMode = true

        try (
            ctrl.bodyType = 3
            if (configDict.get "spine") != undefined do ctrl.spineLinks = (configDict.get "spine")
            if (configDict.get "neck") != undefined do ctrl.neckLinks = (configDict.get "neck")
            if (configDict.get "triPelvis") != undefined do ctrl.trianglePelvis = (configDict.get "triPelvis")
            if (configDict.get "triNeck") != undefined do ctrl.triangleNeck = (configDict.get "triNeck")
            if (configDict.get "fingers") != undefined do ctrl.fingers = (configDict.get "fingers")
            if (configDict.get "fingerlinks") != undefined do ctrl.fingerLinks = (configDict.get "fingerlinks")
            if (configDict.get "toes") != undefined do ctrl.toes = (configDict.get "toes")
            if (configDict.get "toelinks") != undefined do ctrl.toeLinks = (configDict.get "toelinks")
            if (configDict.get "leglinks") != undefined do ctrl.legLinks = (configDict.get "leglinks")

            local tailVal = (configDict.get "tail")
            if tailVal != undefined and tailVal > 0 then ctrl.tailLinks = tailVal else ctrl.tailLinks = 0

            local pony1 = (configDict.get "pony1")
            if pony1 != undefined and pony1 > 0 then ( ctrl.ponytail1Exists = true; ctrl.ponytail1Links = pony1 )
            else ctrl.ponytail1Exists = false

            local pony2 = (configDict.get "pony2")
            if pony2 != undefined and pony2 > 0 then ( ctrl.ponytail2Exists = true; ctrl.ponytail2Links = pony2 )
            else ctrl.ponytail2Exists = false

        ) catch ( print ("❌ [Structure Error] " + getCurrentException()) )

        -- 4. Fit & Cleanup
        this.fit_biped_final root
        this.cleanupGuides()

        return true
    ),

    -- ============================================================================
    -- [3] Biped Fitting Logic (Exact Original Algorithms)
    -- ============================================================================

    fn fit_pelvis_scale node = (
        local parts = filterString node.Name " "
        if parts.count < 1 do return ()
        local root_name = parts[1]
        local g_l = getNodeByName ("Guide_" + root_name + " L Thigh")
        local g_r = getNodeByName ("Guide_" + root_name + " R Thigh")
        local b_l = getNodeByName (root_name + " L Thigh")
        local b_r = getNodeByName (root_name + " R Thigh")
        if (isValidNode g_l) and (isValidNode g_r) and (isValidNode b_l) and (isValidNode b_r) do (
            local curr = distance b_l.transform.pos b_r.transform.pos
            local targ = distance g_l.transform.pos g_r.transform.pos
            if curr > 0.001 do (
                local ratio = targ / curr
                local s = biped.getTransform node #scale
                local new_s = [s.x, s.y, s.z * ratio]
                biped.setTransform node #scale new_s true
            )
        )
    ),

    fn fit_limb_scale node = (
        if node.children.count == 0 do return ()
        local child = node.children[1]
        local g_node = getNodeByName ("Guide_" + node.Name)
        local g_child = getNodeByName ("Guide_" + child.Name)
        if (isValidNode g_node) and (isValidNode g_child) do (
            local curr = distance node.transform.pos child.transform.pos
            local targ = distance g_node.transform.pos g_child.transform.pos
            if curr > 0.001 do (
                local ratio = targ / curr
                local s = biped.getTransform node #scale
                local new_s = [s.x * ratio, s.y, s.z]
                biped.setTransform node #scale new_s true
            )
        )
    ),

    -- ⭐️ [Strict Original] Clavicle Logic (Copy/Paste Posture with Mode Toggle)
    fn fit_clavicle_maxscript bone_name guide_name = (
        local b_node = getNodeByName bone_name
        local g_node = getNodeByName guide_name
        if isValidNode b_node and isValidNode g_node do (
            local bip_root = b_node.controller.rootNode.controller
            local gx = normalize g_node.transform.row1
            local gy = normalize g_node.transform.row2
            local gz = normalize g_node.transform.row3
            local target_tm = matrix3 gx gy gz b_node.transform.pos
            local target_quat = target_tm.rotation

            -- Original Logic: Toggle Figure Mode OFF for rotation
            local oldMode = bip_root.figureMode
            bip_root.figureMode = false

            try (
                biped.setTransform b_node #rotation target_quat true
                biped.addNewKey b_node.controller sliderTime

                biped.deleteAllCopyCollections bip_root
                biped.createCopyCollection bip_root "TmpClav"
                select b_node

                local p = biped.copyPosture bip_root #posture true true true

                -- ⭐️ CRITICAL: Turn Figure Mode back ON before pasting
                bip_root.figureMode = true

                if p != undefined do (
                    biped.pastePosture bip_root #posture false p
                )

                biped.setTransform b_node #pos g_node.transform.pos false
                biped.deleteAllCopyCollections bip_root

            ) catch (
                -- Safety Fallback
                bip_root.figureMode = true
            )
        )
    ),

    -- ⭐️ [Strict Original] Bone Aim Logic
    fn fit_bone_aim node guide = (
        if node.children.count == 0 do return ()
        local child_bone = node.children[1]
        local tgt = getNodeByName ("Guide_" + child_bone.Name)
        if not (isValidNode tgt) do return ()

        local p_pos = node.transform.pos
        local t_pos = tgt.transform.pos
        local v_x = normalize (t_pos - p_pos)
        local v_z = node.transform.row3
        local v_y = cross v_z v_x
        if (length v_y) < 0.001 then (
            v_y = normalize node.transform.row2
            local v_z2 = normalize (cross v_x v_y)
            v_y = cross v_z2 v_x
            v_z = v_z2
        ) else (
            v_y = normalize v_y
            v_z = normalize (cross v_x v_y)
        )
        local tm = matrix3 v_x v_y v_z p_pos
        biped.setTransform node #rotation tm.rotation true
    ),

    fn fit_hand_direct node guide = (
        biped.setTransform node #pos guide.transform.pos true
        biped.setTransform node #rotation guide.transform.rotation true

        if node.children.count > 0 then (
            local targetFinger = undefined
            for c in node.children do ( if (matchPattern c.name pattern:"*Finger2*") do ( targetFinger = c; break ) )
            if targetFinger == undefined do ( for c in node.children do ( if (matchPattern c.name pattern:"*Finger1*") do ( targetFinger = c; break ) ) )
            if targetFinger == undefined do targetFinger = node.children[1]
            local g_child = getNodeByName ("Guide_" + targetFinger.name)
            if (isValidNode g_child) do (
                local currDist = distance node.transform.pos targetFinger.transform.pos
                local targDist = distance guide.transform.pos g_child.transform.pos
                if (currDist > 0.001) do (
                    local ratio = targDist / currDist
                    local s = biped.getTransform node #scale
                    local new_s = [s.x * ratio, s.y, s.z]
                    biped.setTransform node #scale new_s true
                )
            )
        )
    ),

    fn fit_finger_direct node guide = (
        biped.setTransform node #pos guide.transform.pos true
        biped.setTransform node #rotation guide.transform.rotation true
        if node.children.count > 0 do (
            local child = node.children[1]
            local g_child = getNodeByName ("Guide_" + child.name)
            if (isValidNode g_child) do (
                local currLen = distance node.transform.pos child.transform.pos
                local targLen = distance guide.transform.pos g_child.transform.pos
                if currLen > 0.001 do (
                    local ratio = targLen / currLen
                    local s = biped.getTransform node #scale
                    local new_s = [s.x * ratio, s.y, s.z]
                    biped.setTransform node #scale new_s true
                )
            )
        )
    ),

    fn fit_biped_final root = (
        if not (isValidNode root) do return false
        local rootCtrl = root.controller
        if (hasProperty rootCtrl "figureMode") do rootCtrl.figureMode = true

        local all_names = #()
        collect_names root all_names

        -- Pass 1: Scale Fitting
        for name in all_names do (
            local node = getNodeByName name
            if not (isValidNode node) do continue
            if (matchPattern name pattern:"*Pelvis*") then ( fit_pelvis_scale node )
            else if (matchPattern name pattern:"*Thigh*") or (matchPattern name pattern:"*Calf*") or \
                    (matchPattern name pattern:"*UpperArm*") or (matchPattern name pattern:"*Forearm*") or \
                    (matchPattern name pattern:"*Clavicle*") or (matchPattern name pattern:"*Spine*") or \
                    (matchPattern name pattern:"*Neck*") or (matchPattern name pattern:"*Tail*") or \
                    (matchPattern name pattern:"*Pony*") or (matchPattern name pattern:"*HorseLink*") do (
                if (matchPattern name pattern:"*Foot*") == false and (matchPattern name pattern:"*Toe*") == false do ( fit_limb_scale node )
            )
        )

        redrawViews()

        -- Pass 2: Position & Rotation Fitting
        for name in all_names do (
            local node = getNodeByName name
            local guide = getNodeByName ("Guide_" + name)
            if not (isValidNode node) or not (isValidNode guide) do continue

            if (matchPattern name pattern:"*Clavicle*") then (
                fit_clavicle_maxscript name guide.name
            )
            else if (matchPattern name pattern:"*Hand*") then (
                fit_hand_direct node guide
            )
            else if (matchPattern name pattern:"*Finger*") then (
                fit_finger_direct node guide
            )
            else if (matchPattern name pattern:"*UpperArm*") or (matchPattern name pattern:"*Forearm*") or \
                    (matchPattern name pattern:"*Thigh*") or (matchPattern name pattern:"*Calf*") or \
                    (matchPattern name pattern:"*HorseLink*") then (
                fit_bone_aim node guide
            )
            else (
                try (
                    biped.setTransform node #pos guide.transform.pos true
                    biped.setTransform node #rotation guide.transform.rotation true
                ) catch()
            )
        )
        return true
    )
)
global ohCHA_BipedLogic = OhchaBipedLogic_Struct()
print "✅ [Module] BipedLogic Loaded (Strict Legacy Logic)."