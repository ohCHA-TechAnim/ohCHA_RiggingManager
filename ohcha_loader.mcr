macroScript ohCHA_Launch_RigManager
category:"ohCHA Tools"
tooltip:"Launch ohCHA Rig Manager v21.22"
iconName:"ohCHALogo"
(
    try
    (
        -- 1. 경로 설정
        local scriptsPath = (pathConfig.getDir #userScripts)
        local projectRoot = scriptsPath + "\\ohCHA_RigManager\\01.src"
        local mainPyFile = projectRoot + "\\rig_manager_core.py"
        local msScriptsDir = projectRoot + "\\scripts\\"

        -- 2. 로드할 모듈 목록 (순서 중요: Utils -> Logic)
        local msUtils = #(
            "ohcha_data_utils",
            "ohcha_skin_logic",
            "ohcha_layer_logic",
            "ohcha_naming_logic",
            "ohcha_paint_session",
            "set_paint_blend",
            "open_paint_options",
            "ohcha_shape_utils",    -- ⭐️ [필수] 스플라인 생성 로직
            "ohcha_biped_logic",
            "ohcha_bone_logic",
            "ohcha_control_logic",
            "create_hashtable",
            "launch_paint_tool"
        )

        print "--- [ohCHA Loader] Loading Modules..."

        for utilName in msUtils do
        (
            local msePath = msScriptsDir + utilName + ".mse"
            local msPath = msScriptsDir + utilName + ".ms"
            local txtPath = msScriptsDir + utilName + ".txt"

            if (doesFileExist msePath) then (
                fileIn msePath
                print ("    ✅ Loaded (.mse): " + utilName)
            )
            else if (doesFileExist msPath) then (
                fileIn msPath
                print ("    ✅ Loaded (.ms): " + utilName)
            )
            else if (doesFileExist txtPath) then (
                fileIn txtPath
                print ("    ✅ Loaded (.txt): " + utilName)
            )
            else (
                print ("    ❌ MISSING Script: " + utilName)
            )
        )

        -- 3. Python 실행
        if (doesFileExist mainPyFile) then
        (
            local pySrcPath = substituteString projectRoot "\\" "\\\\"
            local pathSetupCmd = "import sys; sys.path.insert(0, r'" + pySrcPath + "') if r'" + pySrcPath + "' not in sys.path else None"
            python.execute pathSetupCmd
            python.executeFile mainPyFile
            print "🚀 [ohCHA Loader] Python Tool Launched Successfully."
        )
        else
        (
            messagebox ("Python Entry File not found:\n" + mainPyFile) title:"ohCHA Launch Error"
        )
    )
    catch
    (
        print ("❌ Launch Error: " + getCurrentException())
    )
)