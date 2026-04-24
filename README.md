# Git Repository Migration Tool (GUI)

Gitレポジトリをサーバ間で移行するためのGUIツールです。Git LFSのオブジェクト移行にも対応しています。

## 特徴

- GUIで移行元/移行先URLを指定
- `git clone --mirror` による参照/タグ/ブランチの丸ごと移行
- Git LFS (`git lfs fetch --all` / `git lfs push --all`) 対応
- 移行前に移行先が空かどうかをチェック可能（既存refs検出で中断）
- ドライラン対応（実行予定コマンドのみ表示）
- 移行後ヴェリファイ対応（既定: `strict`）
- 移行先がGitHubの場合、移行元に合わせてデフォルトブランチを自動設定可能
- 移行先がGitHubの場合、Dependabot Alerts / Automated Security Fixes を有効化可能
- 起動時に `git` / `git-lfs` / `gh` の利用可否を画面表示
- 実行中の各ステップ（LFS移行・ヴェリファイなど）をチェックリスト形式で可視化（完了は取り消し線、実行中は▶で表示）
- 実行ログをGUI内で確認

## 前提条件

- Python 3.10 以上
- Git がインストールされ、`PATH` に通っていること
- Git LFS がインストールされていること（LFS移行を有効化する場合）
- GitHub向け設定を使う場合は GitHub CLI (`gh`) がインストールされていること
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
- GitHub宛先時にデフォルトブランチを設定する
- GitHub宛先時に推奨セキュリティ設定を有効化する

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
- `strict` モードでは、各refの解決オブジェクトIDが完全に一致するか比較

GitHub 宛先の場合、GitHub CLI (`gh`) で認証済みなら以下も実施できます。

- 移行元のデフォルトブランチ名を取得し、移行先の default branch に設定
- Dependabot Alerts を有効化
- Automated Security Fixes を有効化

## 補足

- 認証はGitの通常の認証方式（Credential Manager, SSH鍵, PAT等）を利用します。
- 大容量リポジトリの場合は時間がかかることがあります。

## GitHub連携を使う場合

移行ツールから GitHub のデフォルトブランチ設定/セキュリティ設定を行うには、
GitHub CLI (`gh`) の認証が必要です。

```powershell
gh auth login
gh auth status
```

必要権限の例:

- Repository administration (default branch変更)
- Dependabot alerts / security updates の管理権限

## 開発者向けドキュメント

CI / Release 自動化 / EXE ビルド / Dependabot / 開発セットアップは以下を参照してください。

- [DEVELOPMENT.md](DEVELOPMENT.md)
