-- ohCHA_RigManager/01/src/scripts/ohcha_data_utils.ms
/*
Project:      ohCHA Rig Manager - Data Utilities
Description:  [v2.5.2] Added Bulk Read functions to boost performance (Edit/Smooth).
*/
print ">>> [MS-DEBUG] 1. 'ohcha_data_utils.ms' 파싱 시작..."
struct ohCHA_DataUtil_Struct
(
    fn _findNativeSkinModifier obj = ( if not (isValidNode obj) do return undefined; for m in obj.modifiers do ( if (classof m == Skin) do return m ); undefined ),

    fn getBoneIndexMap obj = ( local skinMod = _findNativeSkinModifier(obj); if skinMod == undefined do return #(); local boneMap = #(); local boneCount = skinOps.GetNumberBones skinMod; for i = 1 to boneCount do ( local boneNode = skinOps.GetBoneNode skinMod i; if boneNode != undefined do ( append boneMap #((boneNode.handle as string), i) ) ); return boneMap ),

    fn getBoneDataWithHierarchy obj =
    (
        local skinMod = _findNativeSkinModifier(obj)
        if skinMod == undefined do return #()
        local validBoneHandles = dotNetObject "System.Collections.Hashtable"
        local boneCount = skinOps.GetNumberBones skinMod

        for i = 1 to boneCount do (
            local boneNode = skinOps.GetBoneNode skinMod i
            if isValidNode boneNode do ( validBoneHandles.add (boneNode.handle as string) true )
        )

        local boneDataArray = #()
        local defaultLayerName = (layerManager.getLayer 0).name

        for i = 1 to boneCount do (
            local boneName = skinOps.GetBoneName skinMod i 0
            local boneNode = skinOps.GetBoneNode skinMod i
            local boneHandleStr = ""
            local parentHandleStr = ""
            local layerName = defaultLayerName
            local bonePos = [0,0,0]

            if (isValidNode boneNode) then (
                boneHandleStr = boneNode.handle as string
                bonePos = boneNode.transform.pos

                if boneNode.layer != undefined do layerName = boneNode.layer.name

                local currentParent = boneNode.parent
                while (currentParent != undefined and not (validBoneHandles.ContainsKey (currentParent.handle as string))) do (
                    currentParent = currentParent.parent
                )
                if (currentParent != undefined) do ( parentHandleStr = currentParent.handle as string )
            )
            append boneDataArray #(boneName, i, boneHandleStr, parentHandleStr, layerName, bonePos.x, bonePos.y, bonePos.z)
        )
        return boneDataArray
    ),

    fn getVertexInfluences skinMod vertId = (
        if skinMod == undefined or vertId == undefined do return #()
        local influenceIds = #(); local influenceCount = skinOps.GetVertexWeightCount skinMod vertId
        for i = 1 to influenceCount do ( append influenceIds (skinOps.GetVertexWeightBoneID skinMod vertId i) )
        return influenceIds
    ),

    fn getAllVertexWeights obj =
    (
        local skinMod = _findNativeSkinModifier(obj);
        if skinMod == undefined do return #();
        local numVerts = skinOps.GetNumberVertices skinMod;
        if numVerts == 0 do return #();

        local allWeightsData = #();
        allWeightsData.count = numVerts

        for v = 1 to numVerts do (
            local influenceCount = skinOps.GetVertexWeightCount skinMod v;
            local boneIndices = #();
            local weightValues = #();

            for i = 1 to influenceCount do (
                append boneIndices (skinOps.GetVertexWeightBoneID skinMod v i);
                append weightValues (skinOps.GetVertexWeight skinMod v i)
            );
            allWeightsData[v] = #(v, boneIndices, weightValues)
        );
        return allWeightsData
    ),

    -- ⭐️ [Optimized] Bulk Read for specific vertices
    fn getBulkVertexWeights obj vertIndices =
    (
        local skinMod = _findNativeSkinModifier(obj); 
        if skinMod == undefined do return #();
        
        local bulkData = #()
        bulkData.count = vertIndices.count
        
        for i = 1 to vertIndices.count do (
            local v = vertIndices[i]
            local influenceCount = skinOps.GetVertexWeightCount skinMod v
            local boneIndices = #()
            local weightValues = #()
            
            for k = 1 to influenceCount do (
                append boneIndices (skinOps.GetVertexWeightBoneID skinMod v k)
                append weightValues (skinOps.GetVertexWeight skinMod v k)
            )
            bulkData[i] = #(v, boneIndices, weightValues)
        )
        return bulkData
    ),

    fn commitPaintChanges obj = ( local skinMod = _findNativeSkinModifier(obj); if skinMod == undefined do return false; try ( if (modPanel.getCurrentObject() == skinMod) then ( if (skinOps.isWeightToolOpen skinMod) do skinOps.closeWeightTool skinMod; subobjectlevel = 0 ); return true ) catch ( return false ) ),

    fn getMeshTopology obj =
    (
        if not (isValidNode obj) do return #()
        local tmesh = snapshotAsMesh obj
        local numV = tmesh.numverts
        local numF = tmesh.numfaces
        local adjBits = #()
        adjBits[numV] = #{}
        for i = 1 to numV do adjBits[i] = #{}
        try (
            for f = 1 to numF do (
                local face = getFace tmesh f
                local va = face.x as integer; local vb = face.y as integer; local vc = face.z as integer
                if (va <= numV and vb <= numV and vc <= numV) then (
                    adjBits[va][vb] = true; adjBits[va][vc] = true
                    adjBits[vb][va] = true; adjBits[vb][vc] = true
                    adjBits[vc][va] = true; adjBits[vc][vb] = true
                )
            )
        ) catch ( print ("❌ [Topo Error] " + getCurrentException()) )
        delete tmesh
        local finalAdjList = #()
        for i = 1 to numV do ( append finalAdjList (adjBits[i] as array) )
        return finalAdjList
    ),

    fn getAllVertexPositions obj =
    (
        if not (isValidNode obj) do return #()
        local tmesh = snapshotAsMesh obj
        local numV = tmesh.numverts
        local posArray = #()
        posArray[numV] = [0,0,0]
        local invTm = inverse obj.transform
        try (
            for i = 1 to numV do (
                local worldPos = getVert tmesh i
                posArray[i] = worldPos * invTm
            )
        )
        catch ( print ("❌ [Pos Error] " + getCurrentException()) )
        delete tmesh
        return posArray
    )
)
if (globalVars.get "ohCHA_DataUtil" == undefined) then ( global ohCHA_DataUtil = ohCHA_DataUtil_Struct() )
print ">>> [MS-DEBUG] 4. 'ohcha_data_utils.ms' 파싱 종료."