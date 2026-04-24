$ErrorActionPreference = "Stop"

Write-Host "[1/3] PyInstaller をインストール中..."
python -m pip install --upgrade pip pyinstaller

Write-Host "[2/3] EXE をビルド中..."
pyinstaller --noconfirm --clean --onefile --windowed --name GitMigrationTool .\git_migration_gui.py

Write-Host "[3/3] 完了: dist\GitMigrationTool.exe"
