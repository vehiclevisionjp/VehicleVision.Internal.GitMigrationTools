# Git Repository Migration Tool (GUI)

Gitレポジトリをサーバ間で移行するためのGUIツールです。Git LFSのオブジェクト移行にも対応しています。

## 特徴

- GUIで移行元/移行先URLを指定
- `git clone --mirror` による参照/タグ/ブランチの丸ごと移行
- Git LFS (`git lfs fetch --all` / `git lfs push --all`) 対応
- 移行前に移行先が空かどうかをチェック可能（既存refs検出で中断）
- ドライラン対応（実行予定コマンドのみ表示）
- 移行後ヴェリファイ対応（既定: `strict`）
- 実行ログをGUI内で確認

## 前提条件

- Python 3.10 以上
- Git がインストールされ、`PATH` に通っていること
- Git LFS がインストールされていること（LFS移行を有効化する場合）
- 移行元・移行先に対するアクセス権があること

## 使い方

1. 以下を実行してアプリを起動します。

```powershell
python .\git_migration_gui.py
```

1. GUIで以下を入力します。

- 移行元URL（例: `https://source.example.com/team/repo.git`）
- 移行先URL（例: `https://dest.example.com/team/repo.git`）

1. 必要に応じてオプションを選択します。

- Git LFSを含めて移行する
- 一時ディレクトリを保持する（デバッグ用）
- 移行前に移行先が空かチェックする（refsなし確認）
- ドライラン（実際には実行せずコマンドのみ表示）
- 移行後ヴェリファイを実施する
- ヴェリファイモード（`strict` / `quick`、既定は `strict`）

1. 「移行開始」をクリックします。

## 実行される処理

LFS有効時、内部的に概ね以下を実行します。

```bash
git clone --mirror <source> <temp>/mirror.git
git -C <temp>/mirror.git remote set-url --push origin <destination>
git -C <temp>/mirror.git push --mirror origin
git -C <temp>/mirror.git lfs fetch --all origin
git -C <temp>/mirror.git lfs push --all <destination>
```

ヴェリファイ有効時は、移行後に以下を実施します。

- `git clone --mirror <destination>` で移行先ミラーを取得
- `for-each-ref` で heads/tags の参照一致を確認
- 移行元/移行先の `git fsck --full` を実行
- `strict` モードでは、各refの `git ls-tree -r --full-tree` の結果を比較

## 補足

- 認証はGitの通常の認証方式（Credential Manager, SSH鍵, PAT等）を利用します。
- 大容量リポジトリの場合は時間がかかることがあります。

## EXE化 (Windows)

PowerShellで以下を実行すると、`dist\\GitMigrationTool.exe` が生成されます。

```powershell
.\build_exe.ps1
```

手動で実行する場合:

```powershell
python -m pip install --upgrade pip pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name GitMigrationTool .\git_migration_gui.py
```

## CI

GitHub Actions のワークフローを追加しています。

- ファイル: `.github/workflows/ci.yml`
- トリガー: `push` (main/master), `pull_request`
- 実行内容: `python -m py_compile git_migration_gui.py`

## Dependabot

Dependabot の設定を追加しています。

- ファイル: `.github/dependabot.yml`
- 更新対象: pip, GitHub Actions
- スケジュール: 毎週月曜 (Asia/Tokyo)

## 開発セットアップ

開発用依存関係をインストールします。

```powershell
python -m pip install -r .\requirements-dev.txt
```

pre-commit を有効化します。

```powershell
pre-commit install
pre-commit run --all-files
```

設定ファイル:

- `.pre-commit-config.yaml`
- `requirements-dev.txt`
