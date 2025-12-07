/* v0.46 - Paint Tool Launcher */
(
    local result = false
    if selection.count == 1 and isValidNode selection[1] do
    (
        local obj = selection[1]
        local skinMod = for m in obj.modifiers where classof m == Skin collect m
        if skinMod.count > 0 do
        (
            skinMod = skinMod[1]
            modPanel.setCurrentObject skinMod
            subobjectlevel = 1
            skinOps.paintWeightsButton skinMod
            result = true
        )
    )
    result
)