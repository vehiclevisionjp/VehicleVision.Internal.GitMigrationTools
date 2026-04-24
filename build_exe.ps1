$ErrorActionPreference = "Stop"

Write-Host "[1/3] Installing PyInstaller..."
python -m pip install --upgrade pip pyinstaller

Write-Host "[2/3] Building EXE..."
python -m PyInstaller --noconfirm --clean --onefile --windowed --name GitMigrationTool .\git_migration_gui.py

Write-Host "[3/3] Done: dist\GitMigrationTool.exe"
