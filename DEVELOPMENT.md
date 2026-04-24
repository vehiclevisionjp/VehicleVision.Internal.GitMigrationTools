# Development Guide

このドキュメントは開発者向けです。利用者向けの使い方は [README.md](README.md) を参照してください。

## 開発セットアップ

```powershell
python -m pip install -r .\requirements-dev.txt
pre-commit install
pre-commit run --all-files
```

関連ファイル:

- `.pre-commit-config.yaml`
- `requirements-dev.txt`

## アイコン生成

アプリケーション用のアイコン（PNG / ICO）を生成します。

```powershell
python -m pip install pillow
python .\generate_icon.py
```

生成されるファイル:

- `assets/icon.png` - GUI アプリケーション用
- `assets/icon.ico` - EXE ビルド用 (Windows)

既に生成済みの場合は実行不要です。

## EXEビルド (Windows)

```powershell
.\build_exe.ps1
```

`build_exe.ps1` 実行時に実行ポリシーで失敗する場合:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\build_exe.ps1
```

または:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

手動ビルド:

```powershell
python -m pip install --upgrade pip pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name GitMigrationTool --icon assets/icon.ico --add-data "assets:assets" .\git_migration_gui.py
```

## GitHub Actions

### CI

- File: `.github/workflows/ci.yml`
- Trigger: `push` (`main`/`master`), `pull_request`
- Run: `python -m py_compile git_migration_gui.py`

### Dependency Review

- File: `.github/workflows/dependency-review.yml`
- Trigger: `pull_request`
- Run: `actions/dependency-review-action@v4` (`high` 以上で失敗)

### Manual Release

- File: `.github/workflows/release.yml`
- Trigger: `workflow_dispatch`
- Input: `bump` (`major` / `minor` / `patch`)
- Process: 次の `vX.Y.Z` タグを計算し、`dist/GitMigrationTool.exe` を添付した GitHub Release を作成

## Dependabot

- File: `.github/dependabot.yml`
- Target: `pip`, `github-actions`
- Schedule: 毎週月曜 (Asia/Tokyo)
