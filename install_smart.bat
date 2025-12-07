<# :
@echo off
setlocal
cd /d "%~dp0"

:: PowerShell을 관리자 권한으로 실행
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((Get-Content '%~f0' -Raw) -join \"`n\")"
goto :eof
#>

# ============================================================
#  ohCHA Rig Manager Smart Installer (Auto Language Config)
# ============================================================

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# 1. 언어 매핑 (표시 이름 -> 내부 코드)
$LangCodeMap = @{
    "English" = "en";
    "Korean" = "kr";
    "Japanese" = "jp";
    "Chinese" = "cn"
}

$LangDict = @{
    "English" = @{
        "Title" = "ohCHA Rig Manager Installer";
        "SelectLang" = "Select Language:";
        "ConfirmMsg" = "Do you want to install ohCHA Rig Manager?";
        "InstallBtn" = "Install";
        "CancelBtn" = "Cancel";
        "Success" = "Installation Completed!";
        "SuccessDetail" = "Installed to {0} locations.";
        "VerError" = "Error: 3ds Max 2025 or higher is required due to Python version.";
        "NoMax" = "Error: No 3ds Max installation found.";
        "NextStep" = "Please restart 3ds Max and check 'ohCHA Tools' category."
    };
    "Korean" = @{
        "Title" = "ohCHA Rig Manager 설치";
        "SelectLang" = "언어를 선택하세요:";
        "ConfirmMsg" = "ohCHA Rig Manager를 설치하시겠습니까?";
        "InstallBtn" = "설치";
        "CancelBtn" = "취소";
        "Success" = "설치가 완료되었습니다!";
        "SuccessDetail" = "{0}개 경로에 설치됨.";
        "VerError" = "오류: Python 버전 호환 문제로 3ds Max 2025 이상에서만 작동합니다!";
        "NoMax" = "오류: 3ds Max 설치 폴더를 찾을 수 없습니다.";
        "NextStep" = "3ds Max를 재시작하고 'ohCHA Tools' 카테고리를 확인하세요."
    };
    "Japanese" = @{
        "Title" = "ohCHA Rig Manager インストーラー";
        "SelectLang" = "言語を選択してください:";
        "ConfirmMsg" = "インストールしますか？";
        "InstallBtn" = "インストール";
        "CancelBtn" = "キャンセル";
        "Success" = "インストール完了!";
        "SuccessDetail" = "{0} 箇所にインストールされました。";
        "VerError" = "エラー: Pythonバージョンのため、3ds Max 2025以上でのみ動作します!";
        "NoMax" = "エラー: 3ds Maxが見つかりません。";
        "NextStep" = "3ds Maxを再起動して 'ohCHA Tools' カテゴリを確認してください。"
    };
    "Chinese" = @{
        "Title" = "ohCHA Rig Manager 安装程序";
        "SelectLang" = "选择语言:";
        "ConfirmMsg" = "您要安装 ohCHA Rig Manager 吗？";
        "InstallBtn" = "安装";
        "CancelBtn" = "取消";
        "Success" = "安装完成!";
        "SuccessDetail" = "已安装到 {0} 个位置。";
        "VerError" = "错误：由于 Python 版本原因，仅支持 3ds Max 2025 或更高版本！";
        "NoMax" = "错误：未找到 3ds Max 安装文件夹。";
        "NextStep" = "请重启 3ds Max 并检查 'ohCHA Tools' 类别。"
    }
}

# --- GUI 생성 ---
$Form = New-Object System.Windows.Forms.Form
$Form.Text = "Select Language"
$Form.Size = New-Object System.Drawing.Size(300, 180)
$Form.StartPosition = "CenterScreen"
$Form.FormBorderStyle = "FixedDialog"
$Form.MaximizeBox = $false

$Lbl = New-Object System.Windows.Forms.Label
$Lbl.Text = "Select Language / 언어 선택"
$Lbl.Location = New-Object System.Drawing.Point(20, 20)
$Lbl.AutoSize = $true
$Form.Controls.Add($Lbl)

$Combo = New-Object System.Windows.Forms.ComboBox
$Combo.Location = New-Object System.Drawing.Point(20, 50)
$Combo.Width = 240
$Combo.DropDownStyle = "DropDownList"
$Combo.Items.Add("English")
$Combo.Items.Add("Korean")
$Combo.Items.Add("Japanese")
$Combo.Items.Add("Chinese")
$Combo.SelectedIndex = 0
$Form.Controls.Add($Combo)

$BtnOK = New-Object System.Windows.Forms.Button
$BtnOK.Text = "OK"
$BtnOK.Location = New-Object System.Drawing.Point(100, 90)
$BtnOK.DialogResult = [System.Windows.Forms.DialogResult]::OK
$Form.Controls.Add($BtnOK)

$Result = $Form.ShowDialog()

if ($Result -ne [System.Windows.Forms.DialogResult]::OK) {
    exit
}

$SelectedLangName = $Combo.SelectedItem.ToString()
$SelectedCode = $LangCodeMap[$SelectedLangName] # 예: "kr"
$Txt = $LangDict[$SelectedLangName]

# --- 설치 확인 ---
$Confirm = [System.Windows.Forms.MessageBox]::Show($Txt["ConfirmMsg"], $Txt["Title"], [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)

if ($Confirm -eq [System.Windows.Forms.DialogResult]::No) {
    exit
}

# --- 설치 로직 ---
$SourceDir = Get-Location
$AppDataMax = "$env:LOCALAPPDATA\Autodesk\3dsMax"
$InstallCount = 0
$VersionErrorCount = 0

# settings.json 내용 생성
$SettingsJson = "{ `"language`": `"$SelectedCode`" }"

if (-not (Test-Path $AppDataMax)) {
    [System.Windows.Forms.MessageBox]::Show($Txt["NoMax"], $Txt["Title"], [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
    exit
}

$MaxFolders = Get-ChildItem -Path $AppDataMax -Directory

foreach ($Folder in $MaxFolders) {
    if ($Folder.Name -match "(\d{4})") {
        $Year = [int]$matches[1]
        if ($Year -lt 2025) {
            $VersionErrorCount++
            continue
        }

        $LangFolders = Get-ChildItem -Path $Folder.FullName -Directory

        foreach ($LangFolder in $LangFolders) {
            if ($LangFolder.Name -in @("ENU", "KOR", "JPN", "CHS", "CHT", "FRA", "GER", "PTB")) {

                $TargetScripts = Join-Path $LangFolder.FullName "scripts\ohCHA_RigManager"
                $TargetMacros = Join-Path $LangFolder.FullName "usermacros"
                $TargetIcons = Join-Path $LangFolder.FullName "usericons"

                # 1. Scripts 복사
                if (Test-Path $TargetScripts) { Remove-Item $TargetScripts -Recurse -Force }
                New-Item -ItemType Directory -Force -Path $TargetScripts | Out-Null

                Copy-Item -Path "$SourceDir\01.src" -Destination "$TargetScripts" -Recurse -Force
                Copy-Item -Path "$SourceDir\03.assets" -Destination "$TargetScripts" -Recurse -Force
                Copy-Item -Path "$SourceDir\data" -Destination "$TargetScripts" -Recurse -Force

                # 2. Macro 복사
                Copy-Item -Path "$SourceDir\ohcha_loader.mcr" -Destination $TargetMacros -Force

                # 3. Icon 복사
                $IconSrc = Join-Path $SourceDir "03.assets\icons"
                $Icons = Get-ChildItem -Path $IconSrc -Filter "ohCHALogo*.png"
                foreach ($Icon in $Icons) {
                    Copy-Item -Path $Icon.FullName -Destination $TargetIcons -Force
                }

                # 4. ⭐️ 언어 설정 파일(settings.json) 생성
                $DataDir = Join-Path $TargetScripts "data"
                if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Force -Path $DataDir | Out-Null }
                $SettingsPath = Join-Path $DataDir "settings.json"
                Set-Content -Path $SettingsPath -Value $SettingsJson -Encoding UTF8

                $InstallCount++
            }
        }
    }
}

if ($InstallCount -gt 0) {
    $Msg = ($Txt["SuccessDetail"] -f $InstallCount) + "`n`n" + $Txt["NextStep"]
    [System.Windows.Forms.MessageBox]::Show($Msg, $Txt["Success"], [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
}
else {
    if ($VersionErrorCount -gt 0) {
        [System.Windows.Forms.MessageBox]::Show($Txt["VerError"], $Txt["Title"], [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
    } else {
        [System.Windows.Forms.MessageBox]::Show($Txt["NoMax"], $Txt["Title"], [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
    }
}