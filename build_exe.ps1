$ErrorActionPreference = "Stop"

Write-Host "[1/3] Installing PyInstaller..."
python -m pip install --upgrade pip pyinstaller

Write-Host "[2/3] Building EXE..."
$repoRoot = $PSScriptRoot
if (-not $repoRoot) { $repoRoot = (Get-Location).Path }

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name GitMigrationTool `
    --icon "$repoRoot\assets\icon.ico" `
    --add-data "$repoRoot\assets;assets" `
    "$repoRoot\git_migration_gui.py"

Write-Host "[3/3] Done: dist\GitMigrationTool.exe"
