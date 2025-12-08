-- ohCHA_RigManager/01/src/scripts/ohcha_skin_logic.ms
/*
Project:      ohCHA Rig Manager - Skin Logic Module
Description:  [v2.6.2] Restored original logic + Added Auto Edit_Poly support.
*/
struct OhchaSkinLogic_Struct
(
    fn _getSkinSelectionBitArray skinMod =
    (
        if not (isValidNode (refs.dependentNodes skinMod)[1]) do return #{}
        local numVerts = skinOps.GetNumberVertices skinMod
        if numVerts == 0 do return #{}
        local selIndices = skinOps.GetSelectedVertices skinMod
        local ba = #{}
        ba.count = numVerts
        for i in selIndices do ba[i] = true
        ba
    ),

    fn _findNearestBone skinMod obj vertIdx excludeID =
    (
        local vertPos = [0,0,0]
        if (isKindOf obj Editable_Poly) then (
            vertPos = polyop.getVert obj vertIdx
        ) else (
            try ( vertPos = getVert obj vertIdx )
            catch ( return -1 )
        )
        local boneCount = skinOps.GetNumberBones skinMod
        local minDist = 1.0e9
        local nearestID = -1

        for i = 1 to boneCount do
        (
            if i == excludeID do continue
            local bNode = skinOps.GetBoneNode skinMod i
            if isValidNode bNode do
            (
                local dist = distance vertPos bNode.transform.pos
                if dist < minDist do ( minDist = dist; nearestID = i )
            )
        )
        return nearestID
    ),

    fn _processModifier polyMod selVerts type unselected =
    (
        modPanel.setCurrentObject polyMod
        subobjectLevel = 1
        if type == "vertex" and unselected then selVerts = -selVerts
        polyMod.SetSelection #Vertex #{}
        polyMod.Select #Vertex selVerts
        if type == "vertex" then ( polyMod.ButtonOp #HideVertex )
        else if type == "face" then (
            polyMod.ConvertSelection #Vertex #Face
            if unselected do ( subobjectLevel = 4; actionMan.executeAction 0 "40044" )
            polyMod.ButtonOp #HideFace
        )
        else if type == "element" then (
            polyMod.ConvertSelection #Vertex #Element
            if unselected do ( subobjectLevel = 5; actionMan.executeAction 0 "40044" )
            polyMod.ButtonOp #HideFace
        )
        subobjectLevel = 0
    ),

    fn _processBaseObject obj selVerts type unselected =
    (
        local base = obj.baseobject
        if type == "vertex" then (
            if unselected then selVerts = -selVerts
            polyop.setVertSelection base selVerts
            polyop.setHiddenVerts base selVerts
        )
        else (
            local faceSel = polyop.getFacesUsingVert base selVerts
            if type == "element" do (
                modPanel.setCurrentObject base; subobjectLevel = 4; polyop.setFaceSelection base faceSel
                try ( obj.ConvertSelection #Face #Element ) catch ()
                faceSel = polyop.getFaceSelection base; subobjectLevel = 0
            )
            if unselected do faceSel = -faceSel
            polyop.setFaceSelection base faceSel
            polyop.setHiddenFaces base faceSel
        )
    ),

    fn hideSelection typeName isUnselected =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        local skinMod = undefined
        local targetPoly = undefined
        local isBaseObj = false

        -- 1. Skin 찾기
        for m in obj.modifiers do (
            if classof m == Skin do skinMod = m
            if skinMod != undefined and classof m == Edit_Poly do ( targetPoly = m; break )
        )

        -- 2. Base Object 확인
        if targetPoly == undefined and classof obj.baseobject == Editable_Poly do ( targetPoly = obj; isBaseObj = true )

        -- ⭐️ [FIX] Sphere 등 Primitive일 경우 Edit Poly 자동 추가
        if skinMod != undefined and targetPoly == undefined do (
            local skinIdx = modPanel.getModifierIndex obj skinMod
            -- Skin 바로 아래에 추가 (Skin이 최상단이면 index 1, 그 아래에 추가하려면 index를 활용)
            -- MaxScript에서 addModifier는 기본적으로 맨 위에 쌓임. before 옵션 필요.
            -- Skin Index가 N이면, Skin 바로 아래는 N (addModifier ... before:N)
            
            if skinIdx > 0 do (
                local newPoly = Edit_Poly()
                newPoly.name = "ohCHA_Hide_Poly"
                addModifier obj newPoly before:skinIdx
                targetPoly = newPoly
                print "✨ [ohCHA] Primitive detected. Added 'Edit Poly' for hiding."
            )
        )

        if skinMod == undefined or targetPoly == undefined do ( 
            print "⚠️ [ohCHA] Skin 혹은 대상 Poly를 찾을 수 없습니다."
            return false 
        )

        disableSceneRedraw()
        try (
            undo "ohCHA Mesh Hide" on (
                -- Skin에서 선택된 버텍스 가져오기
                modPanel.setCurrentObject skinMod
                local selVerts = _getSkinSelectionBitArray(skinMod)
                
                -- Hide 적용
                if isBaseObj then ( _processBaseObject obj selVerts typeName isUnselected )
                else ( _processModifier targetPoly selVerts typeName isUnselected )
                
                -- 다시 Skin으로 포커스 및 버텍스 선택 해제 (깔끔하게)
                modPanel.setCurrentObject skinMod
                subobjectLevel = 1
                -- skinOps.SelectVertices skinMod #{} -- 선택 유지 원할시 주석 처리
            )
        ) catch ( format "❌ [Error] %\n" (getCurrentException()) )
        enableSceneRedraw(); redrawViews(); true
    ),

    fn unhideAll =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        undo "ohCHA Unhide All" on (
            if classof obj.baseobject == Editable_Poly do (
                polyop.unHideAllVerts obj.baseobject; polyop.unHideAllFaces obj.baseobject
            )
            for m in obj.modifiers do (
                if classof m == Edit_Poly do ( m.ButtonOp #UnhideAllFace; m.ButtonOp #UnhideAllVertex )
            )
        )
        redrawViews(); true
    ),

    fn removeUnusedBones =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        local skinMod = for m in obj.modifiers where isKindOf m Skin collect m
        if skinMod.count == 0 do return false
        skinMod = skinMod[1]

        local usedBoneIds = dotNetObject "System.Collections.Hashtable"
        local numVerts = skinOps.GetNumberVertices skinMod

        for v = 1 to numVerts do
        (
            local influenceCount = skinOps.GetVertexWeightCount skinMod v
            for i = 1 to influenceCount do
            (
                local boneId = skinOps.GetVertexWeightBoneID skinMod v i
                local weight = skinOps.GetVertexWeight skinMod v i
                if weight > 0.0001 and not (usedBoneIds.ContainsKey boneId) do usedBoneIds.add boneId true
            )
        )
        local bonesToRemoveIndices = #()
        local numBones = skinOps.GetNumberBones skinMod
        for i = 1 to numBones do ( if not (usedBoneIds.ContainsKey i) do append bonesToRemoveIndices i )
        if bonesToRemoveIndices.count > 0 then
        (
            sort bonesToRemoveIndices
            undo "Remove Unused Bones" on
            (
                for i = bonesToRemoveIndices.count to 1 by -1 do (
                    local boneIndexToDelete = bonesToRemoveIndices[i]
                    if boneIndexToDelete <= skinOps.GetNumberBones skinMod then skinOps.removeBone skinMod boneIndexToDelete
                )
            )
            format "✅ Removed % unused bones.\n" bonesToRemoveIndices.count
            return true
        ) else ( return true )
    ),

    fn transferWeights sourceBoneId targetBoneId =
    (
        local obj = selection[1]
        if obj == undefined or sourceBoneId == undefined or targetBoneId == undefined do return false
        local skinMod = obj.modifiers[#Skin]
        if skinMod == undefined do return false
        local selVerts = skinOps.GetSelectedVertices skinMod
        if selVerts.count == 0 do ( print "⚠️ 선택된 버텍스가 없습니다."; return false )
        undo "Transfer Weights" on
        (
            for v = selVerts do (
                local influenceCount = skinOps.GetVertexWeightCount skinMod v
                local boneIds = #(); local weights = #()
                for i = 1 to influenceCount do ( append boneIds (skinOps.GetVertexWeightBoneID skinMod v i); append weights (skinOps.GetVertexWeight skinMod v i) )
                local sourceIdx = 0; local targetIdx = 0; local transferVal = 0.0
                for i = 1 to boneIds.count do ( if boneIds[i] == sourceBoneId do ( sourceIdx = i; transferVal = weights[i]; break ) )
                if sourceIdx > 0 and transferVal > 0.0 then (
                    for i = 1 to boneIds.count do ( if boneIds[i] == targetBoneId do targetIdx = i )
                    if targetIdx > 0 then ( weights[targetIdx] = weights[targetIdx] + transferVal ) else ( append boneIds targetBoneId; append weights transferVal )
                    weights[sourceIdx] = 0.0
                    skinOps.ReplaceVertexWeights skinMod v boneIds weights
                )
            )
        )
        return true
    ),

    fn modifySelection action =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        local skinMod = undefined
        for m in obj.modifiers do (if classof m == Skin do (skinMod = m; break))
        if skinMod == undefined do return false

        try (
            if (getCommandPanelTaskMode() != #modify) do max modify mode
            if (modPanel.getCurrentObject() != skinMod) do modPanel.setCurrentObject skinMod
            if (subobjectLevel != 1) do subobjectLevel = 1

            if action == "grow" then skinOps.growSelection skinMod
            else if action == "shrink" then skinOps.shrinkSelection skinMod
            else if action == "loop" then skinOps.loopSelection skinMod
            else if action == "ring" then skinOps.ringSelection skinMod

            redrawViews()
            return true
        ) catch (
            print ("❌ modifySelection Fail: " + getCurrentException())
            return false
        )
    ),

    fn applyWeightOperation targetBoneId val operation =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        local skinMod = undefined
        for m in obj.modifiers do (if classof m == Skin do (skinMod = m; break))
        if skinMod == undefined do return false

        local selVerts = skinOps.GetSelectedVertices skinMod
        if selVerts.count == 0 do return false

        if (getCommandPanelTaskMode() != #modify) do max modify mode
        if (modPanel.getCurrentObject() != skinMod) do modPanel.setCurrentObject skinMod

        local reassignedCount = 0

        undo "Weight Operation" on
        (
            for v in selVerts do
            (
                local influenceCount = skinOps.GetVertexWeightCount skinMod v
                local boneIds = #()
                local weights = #()
                local currentTargetWeight = 0.0
                local targetIndex = 0

                for i = 1 to influenceCount do (
                    local bid = skinOps.GetVertexWeightBoneID skinMod v i
                    local w = skinOps.GetVertexWeight skinMod v i
                    append boneIds bid
                    append weights w
                    if bid == targetBoneId do ( currentTargetWeight = w; targetIndex = i )
                )

                if targetIndex == 0 and (operation == "set" or operation == "add") and val > 0.001 do (
                    append boneIds targetBoneId; append weights 0.0; targetIndex = weights.count
                )

                if targetIndex > 0 then (
                    local newTargetWeight = currentTargetWeight
                    if operation == "set" then newTargetWeight = val
                    else if operation == "add" then newTargetWeight = currentTargetWeight + val
                    else if operation == "subtract" then newTargetWeight = currentTargetWeight - val

                    if newTargetWeight < 0.0 do newTargetWeight = 0.0
                    if newTargetWeight > 1.0 do newTargetWeight = 1.0

                    local sumOthers = 0.0
                    for i = 1 to weights.count do ( if i != targetIndex do sumOthers += weights[i] )

                    -- Smart Fallback
                    if (newTargetWeight < 0.001 and sumOthers < 0.001) then (
                        local fallbackID = _findNearestBone skinMod obj v targetBoneId
                        if fallbackID > 0 then (
                            skinOps.ReplaceVertexWeights skinMod v #(fallbackID) #(1.0)
                            reassignedCount += 1
                            continue
                        )
                        continue
                    )

                    weights[targetIndex] = newTargetWeight
                    local remainingTotal = 1.0 - newTargetWeight

                    if sumOthers > 0.0001 then (
                        local scaleRatio = remainingTotal / sumOthers
                        for i = 1 to weights.count do ( if i != targetIndex do weights[i] *= scaleRatio )
                    ) else (
                        for i = 1 to weights.count do ( if i != targetIndex do weights[i] = 0.0 )
                    )
                    skinOps.ReplaceVertexWeights skinMod v boneIds weights
                )
            )
        )
        if reassignedCount > 0 do ( format "✅ [Smart Remove] Reassigned % vertices.\n" reassignedCount )
        return true
    ),

    fn pasteWeightData targetBoneIds targetWeights =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        local skinMod = undefined
        for m in obj.modifiers do (if classof m == Skin do (skinMod = m; break))
        if skinMod == undefined do return false

        local selVerts = skinOps.GetSelectedVertices skinMod
        if selVerts.count == 0 do return false

        if (getCommandPanelTaskMode() != #modify) do max modify mode
        if (modPanel.getCurrentObject() != skinMod) do modPanel.setCurrentObject skinMod

        undo "Paste Weights" on
        (
            for v = selVerts do ( skinOps.ReplaceVertexWeights skinMod v targetBoneIds targetWeights )
        )
        return true
    ),

    fn pruneWeights threshold =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        local skinMod = undefined
        for m in obj.modifiers do (if classof m == Skin do (skinMod = m; break))
        if skinMod == undefined do return false

        local numVerts = skinOps.GetNumberVertices skinMod
        local prunedCount = 0

        undo "Prune Weights" on
        (
            for v = 1 to numVerts do
            (
                local cnt = skinOps.GetVertexWeightCount skinMod v
                if cnt > 0 then
                (
                    local boneIds = #()
                    local weights = #()
                    local totalW = 0.0
                    local hasChanges = false

                    for i = 1 to cnt do
                    (
                        local w = skinOps.GetVertexWeight skinMod v i
                        local bid = skinOps.GetVertexWeightBoneID skinMod v i
                        if w > threshold then ( append boneIds bid; append weights w; totalW += w )
                        else ( hasChanges = true )
                    )

                    if hasChanges and totalW > 0.0 do
                    (
                        for k = 1 to weights.count do weights[k] /= totalW
                        skinOps.ReplaceVertexWeights skinMod v boneIds weights
                        prunedCount += 1
                    )
                )
            )
        )
        if prunedCount > 0 do format "✅ Pruned weights for % vertices.\n" prunedCount
        return true
    ),

    fn openSaveSkinDialog =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        local skinMod = undefined
        for m in obj.modifiers do (if classof m == Skin do (skinMod = m; break))
        if skinMod == undefined do return false
        try ( max modify mode; if selection[1] != obj do select obj; modPanel.setCurrentObject skinMod; skinOps.saveEnvelope skinMod; return true )
        catch ( return false )
    ),

    fn openLoadSkinDialog =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        local skinMod = undefined
        for m in obj.modifiers do (if classof m == Skin do (skinMod = m; break))
        if skinMod == undefined do return false
        try ( max modify mode; if selection[1] != obj do select obj; modPanel.setCurrentObject skinMod; skinOps.loadEnvelope skinMod; return true )
        catch ( return false )
    ),

    fn addBonesToSkin boneNameArray =
    (
        if selection.count != 1 do return false
        local obj = selection[1]
        local skinMod = undefined
        for m in obj.modifiers do (if classof m == Skin do (skinMod = m; break))
        if skinMod == undefined do return false
        max modify mode
        modPanel.setCurrentObject skinMod
        local addedCount = 0
        undo "Add Bones to Skin" on
        (
            for n in boneNameArray do
            (
                local boneNode = getNodeByName n
                if isValidNode boneNode do ( try ( skinOps.addBone skinMod boneNode 1; addedCount += 1 ) catch() )
            )
        )
        return addedCount
    ),

    -- ⭐️ [Optimization] Apply Weights in Bulk (No Python Loop)
    fn applyBulkSkinData skinMod vertIDs boneIDsList weightsList =
    (
        if (skinMod == undefined) do return false
        try (
            for i = 1 to vertIDs.count do (
                local v = vertIDs[i]
                local bones = boneIDsList[i]
                local weights = weightsList[i]
                skinOps.ReplaceVertexWeights skinMod v bones weights
            )
            return true
        )
        catch (
            format "❌ [Bulk Error] %\n" (getCurrentException())
            return false
        )
    )
)
global ohCHA_SkinLogic = OhchaSkinLogic_Struct()