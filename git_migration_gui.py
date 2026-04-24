import os
import queue
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox, ttk


class MigrationApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Git Repository Migration Tool (with LFS)")
        self.root.geometry("900x620")

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker_thread: threading.Thread | None = None

        self.source_url = tk.StringVar()
        self.destination_url = tk.StringVar()
        self.keep_temp = tk.BooleanVar(value=False)
        self.include_lfs = tk.BooleanVar(value=True)
        self.check_destination_empty = tk.BooleanVar(value=True)
        self.dry_run = tk.BooleanVar(value=False)
        self.enable_verification = tk.BooleanVar(value=True)
        self.verification_mode = tk.StringVar(value="strict")

        self._build_ui()
        self._schedule_log_pump()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            frame,
            text="Gitレポジトリ移行ツール (LFS対応)",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor=tk.W, pady=(0, 16))

        form = ttk.Frame(frame)
        form.pack(fill=tk.X)

        ttk.Label(form, text="移行元URL:").grid(row=0, column=0, sticky=tk.W, pady=6)
        ttk.Entry(form, textvariable=self.source_url, width=100).grid(
            row=0, column=1, sticky=tk.EW, pady=6
        )

        ttk.Label(form, text="移行先URL:").grid(row=1, column=0, sticky=tk.W, pady=6)
        ttk.Entry(form, textvariable=self.destination_url, width=100).grid(
            row=1, column=1, sticky=tk.EW, pady=6
        )

        form.columnconfigure(1, weight=1)

        options = ttk.Frame(frame)
        options.pack(fill=tk.X, pady=(8, 12))

        ttk.Checkbutton(
            options,
            text="Git LFSを含めて移行する",
            variable=self.include_lfs,
        ).pack(anchor=tk.W)

        ttk.Checkbutton(
            options,
            text="作業用一時ディレクトリを残す (デバッグ用)",
            variable=self.keep_temp,
        ).pack(anchor=tk.W)

        ttk.Checkbutton(
            options,
            text="移行前に移行先が空かチェックする (refsなし)",
            variable=self.check_destination_empty,
        ).pack(anchor=tk.W)

        ttk.Checkbutton(
            options,
            text="ドライラン (実際には実行せずコマンドのみ表示)",
            variable=self.dry_run,
        ).pack(anchor=tk.W)

        ttk.Checkbutton(
            options,
            text="移行後ヴェリファイを実施する",
            variable=self.enable_verification,
        ).pack(anchor=tk.W)

        verification_mode_frame = ttk.Frame(options)
        verification_mode_frame.pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(verification_mode_frame, text="ヴェリファイモード:").pack(side=tk.LEFT)
        ttk.Combobox(
            verification_mode_frame,
            textvariable=self.verification_mode,
            state="readonly",
            values=("strict", "quick"),
            width=10,
        ).pack(side=tk.LEFT, padx=(8, 0))

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(0, 12))

        self.start_button = ttk.Button(actions, text="移行開始", command=self.start_migration)
        self.start_button.pack(side=tk.LEFT)

        self.clear_button = ttk.Button(actions, text="ログクリア", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=(8, 0))

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(0, 12))

        log_label = ttk.Label(frame, text="実行ログ:")
        log_label.pack(anchor=tk.W)

        self.log_text = tk.Text(frame, height=24, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)

        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _schedule_log_pump(self) -> None:
        self._drain_log_queue()
        self.root.after(100, self._schedule_log_pump)

    def _drain_log_queue(self) -> None:
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self._append_log(line)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def clear_log(self) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def start_migration(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showwarning("実行中", "すでに移行処理が実行中です。")
            return

        source = self.source_url.get().strip()
        destination = self.destination_url.get().strip()

        if not source or not destination:
            messagebox.showerror("入力エラー", "移行元URLと移行先URLを入力してください。")
            return

        self.start_button.configure(state=tk.DISABLED)
        self.progress.start(10)
        self.log_queue.put("=== 移行処理を開始します ===")
        self.log_queue.put(f"移行元: {source}")
        self.log_queue.put(f"移行先: {destination}")
        if self.dry_run.get():
            self.log_queue.put("モード: DRY-RUN")
        if self.enable_verification.get():
            self.log_queue.put(f"ヴェリファイ: 有効 ({self.verification_mode.get()})")
        else:
            self.log_queue.put("ヴェリファイ: 無効")

        self.worker_thread = threading.Thread(
            target=self._run_migration,
            args=(
                source,
                destination,
                self.include_lfs.get(),
                self.keep_temp.get(),
                self.check_destination_empty.get(),
                self.dry_run.get(),
                self.enable_verification.get(),
                self.verification_mode.get(),
            ),
            daemon=True,
        )
        self.worker_thread.start()

    def _set_finished(self) -> None:
        self.progress.stop()
        self.start_button.configure(state=tk.NORMAL)

    def _run_migration(
        self,
        source: str,
        destination: str,
        include_lfs: bool,
        keep_temp: bool,
        check_destination_empty: bool,
        dry_run: bool,
        enable_verification: bool,
        verification_mode: str,
    ) -> None:
        temp_dir = tempfile.mkdtemp(prefix="git-migration-")
        mirror_dir = os.path.join(temp_dir, "mirror.git")
        destination_mirror_dir = os.path.join(temp_dir, "destination-mirror.git")

        try:
            self._ensure_command("git")
            if include_lfs:
                self._ensure_git_lfs()

            self.log_queue.put(f"作業ディレクトリ: {temp_dir}")

            if dry_run:
                self.log_queue.put("ドライランのため、以下のコマンドは実行されません。")
                commands = self._build_migration_commands(source, destination, mirror_dir, include_lfs)
                for command in commands:
                    self.log_queue.put(f"[DRY-RUN] {' '.join(command)}")

                if check_destination_empty:
                    self.log_queue.put("[DRY-RUN] 移行先空チェックはスキップしました。")

                if enable_verification:
                    self.log_queue.put(
                        f"[DRY-RUN] 移行後ヴェリファイを実施予定: mode={verification_mode}"
                    )

                self.log_queue.put("=== ドライランが完了しました ===")
                self.root.after(
                    0,
                    lambda: messagebox.showinfo("完了", "ドライランが完了しました。"),
                )
                return

            if check_destination_empty:
                self._assert_destination_is_empty(destination)

            commands = self._build_migration_commands(source, destination, mirror_dir, include_lfs)
            for command in commands:
                self._run_command(command)

            if enable_verification:
                self._verify_migration(
                    source,
                    destination,
                    mirror_dir,
                    destination_mirror_dir,
                    include_lfs,
                    verification_mode,
                )

            self.log_queue.put("=== 移行が正常に完了しました ===")
            self.root.after(
                0,
                lambda: messagebox.showinfo("完了", "Gitレポジトリの移行が完了しました。"),
            )
        except Exception as ex:
            self.log_queue.put(f"エラー: {ex}")
            self.log_queue.put("=== 移行に失敗しました ===")
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "失敗", "移行中にエラーが発生しました。ログを確認してください。"
                ),
            )
        finally:
            if keep_temp:
                self.log_queue.put("一時ディレクトリを保持しました。")
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.log_queue.put("一時ディレクトリを削除しました。")

            self.root.after(0, self._set_finished)

    def _ensure_command(self, command: str) -> None:
        if shutil.which(command) is None:
            raise RuntimeError(f"'{command}' コマンドが見つかりません。PATHを確認してください。")

    def _ensure_git_lfs(self) -> None:
        try:
            self._run_command(["git", "lfs", "version"], echo=False)
        except RuntimeError as ex:
            raise RuntimeError(
                "Git LFSが利用できません。インストール後に再実行してください。"
            ) from ex

    def _build_migration_commands(
        self, source: str, destination: str, mirror_dir: str, include_lfs: bool
    ) -> list[list[str]]:
        commands = [
            ["git", "clone", "--mirror", source, mirror_dir],
            ["git", "-C", mirror_dir, "remote", "set-url", "--push", "origin", destination],
            ["git", "-C", mirror_dir, "push", "--mirror", "origin"],
        ]

        if include_lfs:
            commands.append(["git", "-C", mirror_dir, "lfs", "fetch", "--all", "origin"])
            commands.append(["git", "-C", mirror_dir, "lfs", "push", "--all", destination])

        return commands

    def _assert_destination_is_empty(self, destination: str) -> None:
        self.log_queue.put("移行先の空チェックを実施します。")
        output = self._run_command_capture(["git", "ls-remote", "--refs", destination])
        if output.strip():
            raise RuntimeError(
                "移行先に既存refsが存在します。誤上書き防止のため処理を中断しました。"
            )
        self.log_queue.put("移行先は空です (refsなし)。")

    def _verify_migration(
        self,
        source: str,
        destination: str,
        source_mirror_dir: str,
        destination_mirror_dir: str,
        include_lfs: bool,
        verification_mode: str,
    ) -> None:
        if verification_mode not in {"strict", "quick"}:
            raise RuntimeError(f"不明なヴェリファイモードです: {verification_mode}")

        self.log_queue.put(f"ヴェリファイ開始: mode={verification_mode}")

        self._run_command(
            ["git", "clone", "--mirror", destination, destination_mirror_dir]
        )

        source_refs = self._get_refs(source_mirror_dir)
        destination_refs = self._get_refs(destination_mirror_dir)
        if source_refs != destination_refs:
            raise RuntimeError("ヴェリファイ失敗: refsが一致しません。")
        self.log_queue.put(f"ヴェリファイOK: refs一致 ({len(source_refs)} refs)")

        self._run_command(["git", "-C", source_mirror_dir, "fsck", "--full"])
        self._run_command(["git", "-C", destination_mirror_dir, "fsck", "--full"])
        self.log_queue.put("ヴェリファイOK: fsck完了")

        if include_lfs:
            self._run_command(["git", "-C", source_mirror_dir, "lfs", "fetch", "--all", "origin"])
            self._run_command(["git", "-C", destination_mirror_dir, "lfs", "fetch", "--all", "origin"])

        if verification_mode == "strict":
            self._verify_strict_content(source_mirror_dir, destination_mirror_dir, source_refs)

        self.log_queue.put("ヴェリファイ完了: 一致を確認しました。")

    def _get_refs(self, repo_dir: str) -> dict[str, str]:
        output = self._run_command_capture(
            [
                "git",
                "-C",
                repo_dir,
                "for-each-ref",
                "--format=%(refname) %(objectname)",
                "refs/heads",
                "refs/tags",
            ]
        )
        refs: dict[str, str] = {}
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            ref_name, object_id = line.split(" ", 1)
            refs[ref_name] = object_id
        return refs

    def _verify_strict_content(
        self, source_repo_dir: str, destination_repo_dir: str, refs: dict[str, str]
    ) -> None:
        self.log_queue.put("strict検証: 全refsのツリー一覧を比較します。")
        for ref_name in sorted(refs.keys()):
            source_tree = self._run_command_capture(
                ["git", "-C", source_repo_dir, "ls-tree", "-r", "--full-tree", ref_name],
                echo=False,
            )
            destination_tree = self._run_command_capture(
                ["git", "-C", destination_repo_dir, "ls-tree", "-r", "--full-tree", ref_name],
                echo=False,
            )
            if source_tree != destination_tree:
                raise RuntimeError(f"strict検証失敗: ref内容不一致 {ref_name}")

        self.log_queue.put(f"strict検証OK: {len(refs)} refs の内容一致")

    def _run_command(self, command: list[str], echo: bool = True) -> None:
        command_display = " ".join(command)
        if echo:
            self.log_queue.put(f"[RUN] {command_display}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        assert process.stdout is not None
        for line in process.stdout:
            self.log_queue.put(line.rstrip())

        exit_code = process.wait()
        if exit_code != 0:
            raise RuntimeError(f"コマンド失敗 (exit={exit_code}): {command_display}")

    def _run_command_capture(self, command: list[str], echo: bool = True) -> str:
        command_display = " ".join(command)
        if echo:
            self.log_queue.put(f"[RUN] {command_display}")

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        combined_output = (completed.stdout or "") + (completed.stderr or "")
        for line in combined_output.splitlines():
            self.log_queue.put(line)

        if completed.returncode != 0:
            raise RuntimeError(
                f"コマンド失敗 (exit={completed.returncode}): {command_display}"
            )

        return completed.stdout or ""


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    app = MigrationApp(root)
    root.mainloop()
