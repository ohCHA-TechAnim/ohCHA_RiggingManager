/*
================================================================================
  Project:      ohCHA Rig Manager - Layer Logic
  Description:  [v2.2] Hierarchy Fix.
                - setLayerParent: Distinguish between "Root" (undefined) and "Layer 0".
                - Allows layers to be siblings of Layer 0.
================================================================================
*/

struct OhchaLayerLogic_Struct
(
    -- [1] Get Hierarchy Data #(Name, ParentName)
    fn getLayerHierarchyData = (
        local count = LayerManager.count
        local data = #()

        for i = 0 to count-1 do (
            local layer = LayerManager.getLayer i
            local layerName = layer.name
            local parentName = ""

            local parentLayer = layer.getParent()
            if parentLayer != undefined do parentName = parentLayer.name

            append data #(layerName, parentName)
        )
        return data
    ),

    -- [2] Create Layer
    fn createLayer newName parentName = (
        if (LayerManager.getLayerFromName newName) != undefined do return false
        local newL = LayerManager.newLayerFromName newName

        if parentName != undefined and parentName != "" do (
            local pLayer = LayerManager.getLayerFromName parentName
            if pLayer != undefined do newL.setParent pLayer
        )
        return true
    ),

    -- [3] Rename Layer
    fn renameLayer oldName newName = (
        if oldName == "0" do return false
        local layer = LayerManager.getLayerFromName oldName
        if layer == undefined do return false
        if (LayerManager.getLayerFromName newName) != undefined do return false
        layer.setname newName
        return true
    ),

    -- [4] Delete Layer
    fn deleteLayer layerName = (
        if layerName == "0" do return false
        local layer = LayerManager.getLayerFromName layerName
        if layer == undefined do return false

        -- Move children objects to default layer
        local layerNodes = undefined
        layer.nodes &layerNodes
        local defaultLayer = LayerManager.getLayerFromName "0"
        if layerNodes.count > 0 do (
            for n in layerNodes do defaultLayer.addNode n
        )

        LayerManager.deleteLayerByName layerName
        return true
    ),

    -- [5] Set Parent (Hierarchy Fix)
    fn setLayerParent childName parentName = (
        if childName == "0" do return false
        local child = LayerManager.getLayerFromName childName
        if child == undefined do return false

        if parentName == "" or parentName == undefined then (
             -- ⭐️ FIX: Move to Root (Top Level), NOT Layer 0
             child.setParent undefined
        ) else (
            local parent = LayerManager.getLayerFromName parentName
            if parent != undefined do (
                child.setParent parent
            )
        )
        return true
    ),

    -- [6] Add Nodes
    fn addNodesToLayer layerName nodeHandles = (
        local layer = LayerManager.getLayerFromName layerName
        if layer == undefined do return false
        undo "Add to Layer" on (
            for h in nodeHandles do (
                local obj = maxOps.getNodeByHandle (h as integer)
                if isValidNode obj do layer.addNode obj
            )
        )
        return true
    ),
    
    -- [7] Select Objects
    fn selectLayerObjects layerName = (
        local layer = LayerManager.getLayerFromName layerName
        if layer == undefined do return false
        local layerNodes = undefined
        layer.nodes &layerNodes
        select layerNodes
        return true
    )
)

global ohCHA_LayerLogic = OhchaLayerLogic_Struct()