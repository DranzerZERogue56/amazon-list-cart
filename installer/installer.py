#!/usr/bin/env python3
"""
Amazon List Auto-Cart — Extension Installer
Detects OS and installed browsers, downloads the latest release from GitHub,
extracts the extension, and walks you through enabling it in each browser.
"""

import sys
import os
import platform
import subprocess
import webbrowser
import zipfile
import urllib.request
import urllib.error
import json
import shutil
import threading
import io
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────
GITHUB_REPO  = "DranzerZERogue56/amazon-list-cart"
RELEASE_API  = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
FALLBACK_ZIP = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"
APP_NAME     = "AmazonListAutoCart"

# ── Browser detection ──────────────────────────────────────────────────────────

BROWSER_PATHS = {
    "Windows": {
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ],
        "opera": [
            r"C:\Program Files\Opera\opera.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\opera.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe"),
        ],
        "edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
    },
    "Darwin": {
        "chrome": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
        "opera":  ["/Applications/Opera.app/Contents/MacOS/Opera",
                   "/Applications/Opera GX.app/Contents/MacOS/Opera GX"],
        "safari": ["/Applications/Safari.app/Contents/MacOS/Safari"],
    },
}

BROWSER_LABELS = {
    "chrome": "Google Chrome",
    "opera":  "Opera / Opera GX",
    "edge":   "Microsoft Edge",
    "safari": "Safari  (requires Xcode)",
}

EXT_URLS = {
    "chrome": "chrome://extensions/",
    "opera":  "opera://extensions/",
    "edge":   "edge://extensions/",
}


def detect_browsers() -> dict:
    paths = BROWSER_PATHS.get(platform.system(), {})
    return {b: p for b, exes in paths.items() for p in exes if os.path.exists(p) and not {}.get(b)}


def get_install_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"
    return base / APP_NAME / "extension"


# ── Colours ────────────────────────────────────────────────────────────────────
C = {
    "bg":      "#131921",
    "surface": "#1E2A35",
    "orange":  "#FF9900",
    "green":   "#00A650",
    "white":   "#FFFFFF",
    "gray":    "#9AA0A6",
    "dark":    "#0D1117",
}


# ── App ────────────────────────────────────────────────────────────────────────

class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Amazon List Auto-Cart — Installer")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self.geometry("500x580")
        self.after(20, self._center)

        self.system      = platform.system()
        self.browsers    = detect_browsers()
        self.install_dir = get_install_dir()
        self.selected    = {}

        self._build_install_screen()

    # ── centering ─────────────────────────────────────────────────────────────

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── install screen ────────────────────────────────────────────────────────

    def _build_install_screen(self):
        self._clear()

        # Header
        hdr = tk.Frame(self, bg=C["bg"], pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Amazon List Auto-Cart",
                 font=("Helvetica", 17, "bold"), bg=C["bg"], fg=C["white"]).pack()
        tk.Label(hdr, text="Extension Installer",
                 font=("Helvetica", 11), bg=C["bg"], fg=C["gray"]).pack()

        # Body
        body = tk.Frame(self, bg=C["surface"], padx=26, pady=20)
        body.pack(fill="both", expand=True)

        # System row
        sys_frame = self._card(body, "Detected System")
        tk.Label(sys_frame, text=f"{platform.system()} {platform.release()}",
                 bg=C["surface"], fg=C["white"], font=("Helvetica", 11)).pack(anchor="w")

        # Browser checkboxes
        br_frame = self._card(body, "Install for")
        for browser, label in BROWSER_LABELS.items():
            found = browser in self.browsers
            is_safari = browser == "safari"

            if is_safari:
                enabled = self.system == "Darwin"
                note    = "  requires Xcode" if enabled else "  macOS only"
            else:
                enabled = found
                note    = "  found" if found else "  not installed"

            var = tk.BooleanVar(value=enabled and not is_safari)
            self.selected[browser] = var

            row = tk.Frame(br_frame, bg=C["surface"])
            row.pack(fill="x", pady=2)

            color = C["white"] if enabled else C["gray"]
            cb = tk.Checkbutton(row, text=f"  {label}",
                                variable=var,
                                state="normal" if enabled else "disabled",
                                bg=C["surface"], fg=color,
                                selectcolor=C["dark"],
                                activebackground=C["surface"], activeforeground=C["white"],
                                font=("Helvetica", 11))
            cb.pack(side="left")
            tk.Label(row, text=note, bg=C["surface"],
                     fg=C["green"] if (found and not is_safari) else C["gray"],
                     font=("Helvetica", 9)).pack(side="left")

        # Location
        loc_frame = self._card(body, "Install location")
        tk.Label(loc_frame, text=str(self.install_dir), bg=C["surface"],
                 fg=C["orange"], font=("Courier", 9),
                 wraplength=440, justify="left").pack(anchor="w")

        # Progress bar + status
        prog_outer = tk.Frame(body, bg=C["surface"])
        prog_outer.pack(fill="x", pady=(10, 4))
        self.progress = ttk.Progressbar(prog_outer, mode="indeterminate", length=450)
        self.progress.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(prog_outer, textvariable=self.status_var,
                 bg=C["surface"], fg=C["gray"], font=("Helvetica", 10),
                 anchor="w").pack(fill="x", pady=(4, 0))

        # Install button
        self.install_btn = tk.Button(
            body, text="Install Extension",
            font=("Helvetica", 13, "bold"),
            bg=C["orange"], fg=C["bg"],
            relief="flat", cursor="hand2",
            padx=20, pady=11,
            command=self._start_install,
        )
        self.install_btn.pack(fill="x", pady=(8, 0))

        tk.Label(body,
                 text="After installing, follow the steps shown to enable it in each browser.",
                 bg=C["surface"], fg=C["gray"],
                 font=("Helvetica", 9), wraplength=450).pack(pady=(10, 0))

    def _card(self, parent, title):
        lf = tk.LabelFrame(parent, text=f"  {title}  ", bg=C["surface"], fg=C["gray"],
                           font=("Helvetica", 9, "bold"), padx=10, pady=8,
                           relief="groove", bd=1)
        lf.pack(fill="x", pady=(0, 10))
        return lf

    # ── install worker ────────────────────────────────────────────────────────

    def _start_install(self):
        targets = [b for b, v in self.selected.items() if v.get()]
        if not targets:
            messagebox.showwarning("Select a browser",
                                   "Please select at least one browser to install for.")
            return
        self.install_btn.config(state="disabled")
        self.progress.start(12)
        threading.Thread(target=self._worker, args=(targets,), daemon=True).start()

    def _worker(self, targets):
        try:
            self._status("Fetching latest release…")
            zip_url = self._get_zip_url()

            self._status("Downloading extension…")
            zip_data = self._download(zip_url)

            self._status("Extracting files…")
            self._extract(zip_data)

            self._status("Done!")
            self.after(200, lambda: self._build_complete_screen(targets))
        except Exception as exc:
            self.after(0, lambda: self._on_error(str(exc)))

    def _get_zip_url(self) -> str:
        try:
            req = urllib.request.Request(
                RELEASE_API,
                headers={"Accept": "application/vnd.github+json",
                         "User-Agent": "AmazonListAutoCart-Installer"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                for asset in data.get("assets", []):
                    if asset["name"] == "extension.zip":
                        return asset["browser_download_url"]
        except Exception:
            pass
        return FALLBACK_ZIP

    def _download(self, url) -> io.BytesIO:
        req = urllib.request.Request(
            url, headers={"User-Agent": "AmazonListAutoCart-Installer"}
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            return io.BytesIO(r.read())

    def _extract(self, zip_data: io.BytesIO):
        dest = self.install_dir
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_data) as zf:
            members = zf.namelist()

            # Locate manifest.json — works for both direct extension.zip
            # and GitHub repo archive (nested under repo-name/extension/)
            manifest_path = next(
                (m for m in members if m.endswith("extension/manifest.json")), None
            ) or next(
                (m for m in members if m.endswith("manifest.json")), None
            )

            if not manifest_path:
                raise ValueError("Could not find manifest.json in the downloaded archive.")

            prefix = manifest_path[: manifest_path.rfind("manifest.json")]

            for member in members:
                if not member.startswith(prefix) or member == prefix:
                    continue
                rel  = member[len(prefix):]
                dest_path = dest / rel
                if member.endswith("/"):
                    dest_path.mkdir(parents=True, exist_ok=True)
                else:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, open(dest_path, "wb") as out:
                        shutil.copyfileobj(src, out)

    def _on_error(self, msg):
        self.progress.stop()
        self.install_btn.config(state="normal")
        self._status(f"Error: {msg}")
        messagebox.showerror("Install failed",
                             f"Could not install the extension:\n\n{msg}\n\n"
                             "Check your internet connection and try again.")

    def _status(self, msg):
        self.after(0, lambda: self.status_var.set(msg))

    # ── complete screen ───────────────────────────────────────────────────────

    def _build_complete_screen(self, targets):
        self.progress.stop()
        self._clear()

        path_str = str(self.install_dir)

        # Header
        hdr = tk.Frame(self, bg=C["bg"], pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Extension Downloaded",
                 font=("Helvetica", 17, "bold"), bg=C["bg"], fg=C["green"]).pack()
        tk.Label(hdr, text="Complete these steps to enable it in your browser.",
                 font=("Helvetica", 11), bg=C["bg"], fg=C["gray"]).pack()

        body = tk.Frame(self, bg=C["surface"], padx=26, pady=20)
        body.pack(fill="both", expand=True)

        # Path card
        path_card = self._card(body, "Extension folder — copied to clipboard")
        path_row  = tk.Frame(path_card, bg=C["surface"])
        path_row.pack(fill="x")
        tk.Label(path_row, text=path_str, bg=C["surface"], fg=C["orange"],
                 font=("Courier", 9), wraplength=370, justify="left").pack(side="left", fill="x", expand=True)
        tk.Button(path_row, text="Copy", font=("Helvetica", 9),
                  bg=C["dark"], fg=C["white"], relief="flat", cursor="hand2",
                  padx=8, pady=4,
                  command=lambda: self._copy(path_str)).pack(side="right", padx=(8, 0))
        self._copy(path_str)

        # Steps card
        steps_card = self._card(body, "Steps to enable in Chrome / Opera / Edge")
        steps = [
            "1.  Click \"Open Browser\" below",
            "2.  Toggle  Developer mode  (top-right corner)",
            "3.  Click  Load unpacked",
            "4.  Paste the path above → click  Select Folder",
            "5.  Extension icon appears in your toolbar!",
        ]
        for s in steps:
            tk.Label(steps_card, text=s, bg=C["surface"], fg=C["white"],
                     font=("Helvetica", 11), anchor="w").pack(fill="x", pady=1)

        # Browser open buttons
        btn_frame = tk.Frame(body, bg=C["surface"])
        btn_frame.pack(fill="x", pady=(4, 0))

        for browser in [t for t in targets if t != "safari"]:
            label = BROWSER_LABELS.get(browser, browser.title())
            tk.Button(btn_frame, text=f"Open {label}  →",
                      font=("Helvetica", 11, "bold"),
                      bg=C["orange"], fg=C["bg"],
                      relief="flat", cursor="hand2", padx=12, pady=9,
                      command=lambda b=browser: self._open_ext_page(b),
                      ).pack(fill="x", pady=3)

        if "safari" in targets:
            tk.Label(btn_frame,
                     text="Safari: run  convert-to-safari.sh  from the repo (requires Xcode on Mac).",
                     bg=C["surface"], fg=C["gray"],
                     font=("Helvetica", 9), wraplength=450).pack(pady=(4, 0))

        tk.Button(body, text="Done", font=("Helvetica", 11),
                  bg=C["dark"], fg=C["white"], relief="flat", cursor="hand2",
                  padx=12, pady=8, command=self.destroy).pack(fill="x", pady=(10, 0))

    # ── helpers ───────────────────────────────────────────────────────────────

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _open_ext_page(self, browser):
        url = EXT_URLS.get(browser, "chrome://extensions/")
        exe = self.browsers.get(browser)
        try:
            if exe:
                subprocess.Popen([exe, url])
            elif self.system == "Darwin":
                names = {"chrome": "Google Chrome", "opera": "Opera", "edge": "Microsoft Edge"}
                subprocess.Popen(["open", "-a", names.get(browser, browser), "--args", url])
            else:
                webbrowser.open(url)
        except Exception as exc:
            messagebox.showerror("Could not open browser", str(exc))


# ── Entry ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
