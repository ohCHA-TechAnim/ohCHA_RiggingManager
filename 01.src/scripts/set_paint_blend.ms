/* v0.67 - Set Paint Blend Mode (Safer Global Function Syntax) */
fn ohCHA_SetPaintBlend enabled =
(
    try (
        if (is_interface maxops.paintInterface) do
        (
            maxops.paintInterface.paintBlendMode = enabled
        )
    ) catch ( print ("⚠️ [MS-DEBUG] set_paint_blend.ms (maxops) 실패: " + getCurrentException()) )

    try (
        if (selection.count == 1) do
        (
            local skinMod = selection[1].modifiers[#Skin]
            if (skinMod != undefined) do
            (
                skinMod.paintBlendMode = enabled
            )
        )
    ) catch ( print ("⚠️ [MS-DEBUG] set_paint_blend.ms (skinMod) 실패: " + getCurrentException()) )
)
global ohCHA_SetPaintBlend