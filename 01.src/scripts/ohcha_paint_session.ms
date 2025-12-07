/*
Project:      ohCHA Rig Manager - Paint Session Manager
Description:  [v1.3.2 Stable] Ensured data capture integrity.
*/
print ">>> [MS Paint] 1. 'ohcha_paint_session.ms' 파일 파싱 시작..."
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
            max modify mode
            select obj
            modPanel.setCurrentObject theSkinMod
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
            if subobjectlevel != 1 do ( subobjectlevel = 0; subobjectlevel = 1 )
            redrawViews()
            return (subobjectlevel == 1)
        )
        catch ( return false )
    ),

    fn selectEnvelope obj boneId =
    (
        local theSkinMod = undefined
        for m in obj.modifiers where classof m == Skin do (theSkinMod = m; break)
        if theSkinMod == undefined do return false
        try
        (
            if modPanel.getCurrentObject() != theSkinMod do modPanel.setCurrentObject theSkinMod
            if (skinOps.isWeightToolOpen theSkinMod) then ( skinOps.selectBone theSkinMod boneId )
            else ( if subobjectlevel != 1 do subobjectlevel = 1; skinOps.selectBone theSkinMod boneId )
            return true
        )
        catch(return false)
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