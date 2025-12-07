/*
================================================================================
  Project:      ohCHA Rig Manager - Naming Logic
  Description:  [v1.0] Batch Rename Logic.
                - renameObjects: Renames objects by handles with Undo support.
================================================================================
*/

struct OhchaNamingLogic_Struct
(
    fn renameObjects handles newNames =
    (
        if handles.count != newNames.count do return false

        undo "Batch Rename" on
        (
            for i = 1 to handles.count do
            (
                local obj = maxOps.getNodeByHandle (handles[i] as integer)
                if isValidNode obj do
                (
                    obj.name = newNames[i]
                )
            )
        )
        return true
    )
)
global ohCHA_NamingLogic = OhchaNamingLogic_Struct()