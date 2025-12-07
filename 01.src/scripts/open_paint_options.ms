/*
================================================================================
  Project:      ohCHA Rig Manager - Open Paint Options
  Description:  [v0.67] Converted to standard 'fn...; global...' syntax
                to prevent auto-run and parse errors.
================================================================================
*/

-- ⭐️ [v0.67] 'global fn ... =' 구문 대신
-- 표준적인 'fn...; global...' 선언으로 변경
fn ohCHA_OpenPaintOptions =
(
    print "    [MS-DEBUG] ohCHA_OpenPaintOptions() 실행"
    try
    (
        if (selection.count == 1) do
        (
            local skinMod = selection[1].modifiers[#Skin]
            if (skinMod != undefined) do
            (
                skinOps.paintOptionsButton skinMod
            )
        )
    )
    catch (
        print ("    ❌ [MS-DEBUG] ohCHA_OpenPaintOptions() 실패: " + getCurrentException())
    )
)
-- ⭐️ [v0.67] 함수를 전역으로 노출
global ohCHA_OpenPaintOptions