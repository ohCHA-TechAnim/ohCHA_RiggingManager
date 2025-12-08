/*
Project:      ohCHA Rig Manager - Paint Session Manager
Description:  [v1.3.5 Refactor] Fixed Envelope Selection logic.
              - Force Modify Mode and correct object selection for bone highlighting.
*/
print ">>> [MS Paint] 1. 'ohcha_paint_session.ms' 파싱 시작..."
struct ohCHAPaintSession_Struct
(
    skinMod = undefined,

    fn _applySkinSettings theSkinMod =
    (
        try
        (
            theSkinMod.mirrorEnabled = off
            theSkinMod.filter_vertices = on
            toolMode.coordsys #view
        )
        catch()
    ),

    fn _safeEnterModPanel obj theSkinMod =
    (
        try
        (
            if (getCommandPanelTaskMode() != #modify) do max modify mode
            if (selection.count != 1 or selection[1] != obj) do select obj
            if (modPanel.getCurrentObject() != theSkinMod) do modPanel.setCurrentObject theSkinMod
            windows.processPostedMessages()
            return true
        )
        catch ( return false )
    ),

    fn start obj boneIdToSelect =
    (
        skinMod = for m in obj.modifiers where classof m == Skin collect m
        if skinMod.count == 0 do return false
        skinMod = skinMod[1]

        if not (_safeEnterModPanel obj skinMod) do return false

        try
        (
            _applySkinSettings skinMod
            if boneIdToSelect != undefined and boneIdToSelect > 0 do
            (
                skinOps.selectBone skinMod boneIdToSelect
            )
            subobjectlevel = 1
            skinOps.paintWeightsButton skinMod
            return true
        )
        catch ( return false )
    ),

    fn commit =
    (
        if skinMod == undefined do return false
        try
        (
            if (skinOps.isWeightToolOpen skinMod) do skinOps.closeWeightTool skinMod
            subobjectlevel = 0
            return true
        )
        catch ( return false )
    ),

    fn enterManualEditMode obj =
    (
        local theSkinMod = undefined
        for m in obj.modifiers where classof m == Skin do (theSkinMod = m; break)
        if theSkinMod == undefined do return false
        if not (_safeEnterModPanel obj theSkinMod) do return false
        try
        (
            _applySkinSettings theSkinMod
            subobjectlevel = 1
            -- Toggle trick to force refresh
            if subobjectlevel != 1 do ( subobjectlevel = 0; subobjectlevel = 1 )
            redrawViews()
            return (subobjectlevel == 1)
        )
        catch ( return false )
    ),

    -- ⭐️ [FIX] Robust Envelope Selection
    fn selectEnvelope obj boneId =
    (
        if not (isValidNode obj) do return false
        local theSkinMod = undefined
        for m in obj.modifiers where classof m == Skin do (theSkinMod = m; break)
        if theSkinMod == undefined do return false
        
        try
        (
            -- 1. Ensure Modify Panel & Object Selection
            if (getCommandPanelTaskMode() != #modify) do max modify mode
            if (selection.count != 1 or selection[1] != obj) do select obj
            
            -- 2. Ensure Skin Modifier is active
            if (modPanel.getCurrentObject() != theSkinMod) do modPanel.setCurrentObject theSkinMod
            
            -- 3. Ensure SubObject Level (Vertex)
            if (subobjectLevel != 1) do subobjectLevel = 1
            
            -- 4. Select Bone
            skinOps.selectBone theSkinMod boneId
            redrawViews()
            return true
        )
        catch(
            print ("❌ [SelectEnvelope Error] " + getCurrentException())
            return false
        )
    ),

    fn enterVertexSelectMode obj =
    (
        local theSkinMod = undefined
        for m in obj.modifiers where classof m == Skin do (theSkinMod = m; break)
        if theSkinMod == undefined do return false
        if not (_safeEnterModPanel obj theSkinMod) do return false
        try
        (
            _applySkinSettings theSkinMod
            subobjectlevel = 1
            return true
        )
        catch(return false)
    ),

    fn getPaintedWeights obj =
    (
        local theSkinMod = undefined
        for m in obj.modifiers where classof m == Skin do (theSkinMod = m; break)
        if theSkinMod == undefined do return #()
        
        local allWeightsData = #()
        local numVerts = skinOps.GetNumberVertices theSkinMod
        
        for v = 1 to numVerts do
        (
            local influenceCount = skinOps.GetVertexWeightCount theSkinMod v
            if influenceCount > 0 then
            (
                local boneIndices = #()
                local weightValues = #()
                for i = 1 to influenceCount do ( 
                    append boneIndices (skinOps.GetVertexWeightBoneID theSkinMod v i)
                    append weightValues (skinOps.GetVertexWeight theSkinMod v i)
                )
                append allWeightsData #(v, boneIndices, weightValues)
            )
        )
        return allWeightsData
    )
)
if (globalVars.get "ohCHA_PaintSession" == undefined) then ( global ohCHA_PaintSession = ohCHAPaintSession_Struct() )
print ">>> [MS Paint] 2. 'ohCHA_PaintSession' (Global) 인스턴스 생성 완료."