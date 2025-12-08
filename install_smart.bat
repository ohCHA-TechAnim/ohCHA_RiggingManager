<# :
@echo off
setlocal
cd /d "%~dp0"

:: 콘솔 창 숨기기 위해 VBScript를 거치더라도,
:: 배치 파일 자체에서 에러 출력을 막고 PowerShell로 바로 넘깁니다.
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((Get-Content '%~f0' -Encoding Default) -join \"`n\")"
goto :eof
#>

# ============================================================
#  ohCHA Rig Manager Silent Installer
# ============================================================

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# 1. 언어 매핑
$LangCodeMap = @{ "English"="en"; "Korean"="kr"; "Japanese"="jp"; "Chinese"="cn" }
$LangDict = @{
    "English" = @{ "Title"="Installer"; "SelectLang"="Select Language:"; "ConfirmMsg"="Install ohCHA Rig Manager?"; "Success"="Done!"; "NextStep"="Please restart 3ds Max."; "NoMax"="Error: 3ds Max not found." };
    "Korean" = @{ "Title"="설치"; "SelectLang"="언어 선택:"; "ConfirmMsg"="ohCHA Rig Manager를 설치하시겠습니까?"; "Success"="설치 완료!"; "NextStep"="3ds Max를 재시작해주세요."; "NoMax"="오류: 3ds Max를 찾을 수 없습니다." };
    "Japanese" = @{ "Title"="インスト?ラ?"; "SelectLang"="言語選?:"; "ConfirmMsg"="インスト?ルしますか？"; "Success"="完了!"; "NextStep"="3ds Maxを再起動してください。"; "NoMax"="エラ?: 3ds Maxが見つかりません。" };
    "Chinese" = @{ "Title"="安?程序"; "SelectLang"="???言:"; "ConfirmMsg"="安? ohCHA Rig Manager？"; "Success"="完成!"; "NextStep"="?重? 3ds Max。"; "NoMax"="??: 未?到 3ds Max。" }
}

# 2. GUI 생성 (항상 맨 위에 표시)
$Form = New-Object System.Windows.Forms.Form
$Form.Text = "ohCHA Setup"
$Form.Size = New-Object System.Drawing.Size(300, 160)
$Form.StartPosition = "CenterScreen"
$Form.FormBorderStyle = "FixedDialog"
$Form.MaximizeBox = $false
$Form.TopMost = $true 

$Lbl = New-Object System.Windows.Forms.Label
$Lbl.Text = "Language / 언어"
$Lbl.Location = New-Object System.Drawing.Point(20, 20)
$Form.Controls.Add($Lbl)

$Combo = New-Object System.Windows.Forms.ComboBox
$Combo.Location = New-Object System.Drawing.Point(20, 45)
$Combo.Width = 240
$Combo.DropDownStyle = "DropDownList"
$Combo.Items.AddRange(@("English", "Korean", "Japanese", "Chinese"))
$Combo.SelectedIndex = 0
$Form.Controls.Add($Combo)

$BtnOK = New-Object System.Windows.Forms.Button
$BtnOK.Text = "Install"
$BtnOK.Location = New-Object System.Drawing.Point(100, 80)
$BtnOK.DialogResult = [System.Windows.Forms.DialogResult]::OK
$Form.Controls.Add($BtnOK)

# 3. 실행 및 설치
if ($Form.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    $SelectedLang = $Combo.SelectedItem.ToString()
    $Code = $LangCodeMap[$SelectedLang]
    $Txt = $LangDict[$SelectedLang]

    # 설치 로직
    $SourceDir = Get-Location
    $AppDataMax = "$env:LOCALAPPDATA\Autodesk\3dsMax"
    $Count = 0
    
    if (Test-Path $AppDataMax) {
        $MaxFolders = Get-ChildItem -Path $AppDataMax -Directory
        foreach ($F in $MaxFolders) {
            if ($F.Name -match "(\d{4})") {
                if ([int]$matches[1] -ge 2025) {
                    $LangDirs = Get-ChildItem -Path $F.FullName -Directory
                    foreach ($L in $LangDirs) {
                        if ($L.Name -in @("ENU", "KOR", "JPN", "CHS")) {
                            $Dest = Join-Path $L.FullName "scripts\ohCHA_RigManager"
                            
                            # 복사 (오류 무시하고 덮어쓰기)
                            try {
                                if (Test-Path $Dest) { Remove-Item $Dest -Recurse -Force -ErrorAction SilentlyContinue }
                                New-Item -ItemType Directory -Force -Path $Dest | Out-Null
                                Copy-Item -Path "$SourceDir\01.src" -Destination $Dest -Recurse -Force
                                Copy-Item -Path "$SourceDir\03.assets" -Destination $Dest -Recurse -Force
                                Copy-Item -Path "$SourceDir\data" -Destination $Dest -Recurse -Force
                                
                                # 매크로/아이콘 복사
                                Copy-Item "$SourceDir\ohcha_loader.mcr" (Join-Path $L.FullName "usermacros") -Force
                                $IconDest = Join-Path $L.FullName "usericons"
                                Get-ChildItem "$SourceDir\03.assets\icons\ohCHALogo*.png" | Copy-Item -Destination $IconDest -Force

                                # 설정 파일 생성
                                $JsonPath = Join-Path $Dest "data\settings.json"
                                Set-Content -Path $JsonPath -Value "{ `"language`": `"$Code`" }" -Encoding UTF8
                                $Count++
                            } catch {}
                        }
                    }
                }
            }
        }
    }

    # 결과 메시지 (성공시에만 띄움, 실패 시 조용히 종료하거나 필요하면 띄움)
    if ($Count -gt 0) {
        [System.Windows.Forms.MessageBox]::Show($Txt["Success"] + "`n" + $Txt["NextStep"], "ohCHA", 0, 64)
    } else {
        [System.Windows.Forms.MessageBox]::Show($Txt["NoMax"] + " (2025+)", "Error", 0, 16)
    }
}