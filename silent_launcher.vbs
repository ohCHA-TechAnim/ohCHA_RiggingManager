Set WshShell = CreateObject("WScript.Shell")
' 0 = Hide Window, True = Wait until finished
WshShell.Run "install_smart.bat", 0, True