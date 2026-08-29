"""SpotiFlow — Bootstrap част 2: GUI + Wizard + build + README + .gitignore."""
from pathlib import Path

# Проверка, че част 1 е пусната
for req in ["formats.py", "votify_manager.py", "downloader.py"]:
    if not Path(req).exists():
        print(f"[!!] {req} липсва — първо пуснете bootstrap_spotiflow.py (част 1)")
        raise SystemExit(1)

FILES = {}

# ─── setup_wizard.py ──────────────────────────────────────────────
FILES["setup_wizard.py"] = r'''
"""SpotiFlow — Setup Wizard със същите съобщения като Settings (formats.py)."""
import os
import webbrowser
import customtkinter as ctk
from tkinter import filedialog, messagebox
from formats import (FORMATS, DEFAULT_KEY, get_format, ui_label, ui_hint,
                     CapabilityContext)


class SetupWizard(ctk.CTkToplevel):
    SPOTIFY_DL_URL = "https://www.filepuma.com/download/spotify_1.2.88.483-63917/"

    def __init__(self, parent, config, theme, votify, ffmpeg_ok=False, on_complete=None):
        super().__init__(parent)
        self.config, self.theme, self.votify = config, theme, votify
        self.ffmpeg_ok, self.on_complete = ffmpeg_ok, on_complete
        self.title("SpotiFlow — Setup")
        self.geometry("660x580")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        c = theme.colors
        self.configure(fg_color=c["bg"])
        self._step_idx = 0
        self._steps = ["welcome", "cookies", "quality", "complete"]
        self._fmt_key = config.get("audio_format", DEFAULT_KEY)
        self._build_chrome()
        self._show_step(0)

    def _build_chrome(self):
        c = self.theme.colors
        top = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=50)
        top.pack(fill="x")
        top.pack_propagate(False)
        self._dots = []
        for i in range(len(self._steps)):
            d = ctk.CTkLabel(top, text="●", font=ctk.CTkFont(size=14),
                             text_color=c["text_muted"])
            d.pack(side="left", padx=14, pady=16)
            self._dots.append(d)
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=40, pady=15)
        nav = ctk.CTkFrame(self, fg_color="transparent", height=50)
        nav.pack(fill="x", padx=40, pady=(0, 15))
        nav.pack_propagate(False)
        self._back_btn = ctk.CTkButton(nav, text="← Назад", width=100,
            fg_color=c["card"], hover_color=c["card_hover"], text_color=c["text"],
            command=self._go_back)
        self._back_btn.pack(side="left")
        self._next_btn = ctk.CTkButton(nav, text="Напред →", width=120,
            fg_color=c["accent"], hover_color=c["accent_hover"], text_color="white",
            command=self._go_next)
        self._next_btn.pack(side="right")

    def _ctx(self):
        return CapabilityContext(
            premium=bool(self._premium_var.get()),
            dll_path=self._dll_entry.get().strip() or None,
            wvd_path=self._wvd_entry.get().strip() or None,
            wvd_l1=bool(self._wvd_l1_var.get()),
            ffmpeg_available=self.ffmpeg_ok)

    def _show_step(self, idx):
        self._step_idx = idx
        c = self.theme.colors
        for i, d in enumerate(self._dots):
            d.configure(text_color=c["accent"] if i <= idx else c["text_muted"])
        self._back_btn.configure(state="normal" if idx > 0 else "disabled")
        self._next_btn.configure(text="Завърши ✓" if idx == len(self._steps) - 1 else "Напред →")
        for w in self._content.winfo_children():
            w.destroy()
        getattr(self, "_step_" + self._steps[idx])()

    def _go_back(self):
        if self._step_idx > 0:
            self._show_step(self._step_idx - 1)

    def _go_next(self):
        name = self._steps[self._step_idx]
        val = getattr(self, "_validate_" + name, lambda: True)()
        if not val:
            return
        if self._step_idx < len(self._steps) - 1:
            self._show_step(self._step_idx + 1)
        else:
            self._finish()

    def _finish(self):
        self.config.set("premium", bool(self._premium_var.get()))
        self.config.set("cookies_path", self._cookies_entry.get().strip())
        self.config.set("spotify_dll_path", self._dll_entry.get().strip())
        self.config.set("wvd_path", self._wvd_entry.get().strip())
        self.config.set("wvd_l1", bool(self._wvd_l1_var.get()))
        self.config.set("audio_format", self._fmt_key)
        self.config.set("setup_complete", True)
        if self.on_complete:
            self.on_complete()
        self.destroy()

    def _step_welcome(self):
        c = self.theme.colors
        ctk.CTkLabel(self._content, text="Добре дошли в SpotiFlow",
            font=ctk.CTkFont(size=26, weight="bold"), text_color=c["text"]).pack(pady=(25, 8))
        ctk.CTkLabel(self._content,
            text="Ще настроим свалянето на музика от Spotify:\n"
                 "1) cookies.txt  2) Spotify.dll (за FLAC)  3) формат и качество",
            font=ctk.CTkFont(size=13), text_color=c["text_secondary"],
            justify="left").pack(pady=10)
        skip = ctk.CTkButton(self._content, text="Пропусни → OGG 160 kbps без настройки",
            width=260, fg_color="transparent", hover_color=c["card_hover"],
            text_color=c["text_muted"], command=self._skip)
        skip.pack(pady=15)

    def _skip(self):
        self.config.set("audio_format", "ogg_160")
        self.config.set("setup_complete", True)
        if self.on_complete:
            self.on_complete()
        self.destroy()

    def _step_cookies(self):
        c = self.theme.colors
        ctk.CTkLabel(self._content, text="Стъпка 1: Акаунт и cookies",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=c["text"]).pack(pady=(10, 10))
        self._premium_var = ctk.BooleanVar(value=self.config.get("premium", False))
        ctk.CTkCheckBox(self._content, text="Premium акаунт", variable=self._premium_var,
            fg_color=c["accent"], text_color=c["text"],
            command=self._refresh_ctx_labels).pack(anchor="w", pady=4)
        ctk.CTkLabel(self._content, text="Бележка: грешен флаг = грешка при сваляне.",
            font=ctk.CTkFont(size=10), text_color=c["text_muted"]).pack(anchor="w")
        for label, attr, key in [("cookies.txt:", "_cookies_entry", "cookies_path"),
                                 ("Spotify.dll:", "_dll_entry", "spotify_dll_path"),
                                 (".wvd файл:", "_wvd_entry", "wvd_path")]:
            row = ctk.CTkFrame(self._content, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, width=90, font=ctk.CTkFont(size=12),
                         text_color=c["text_secondary"]).pack(side="left")
            e = ctk.CTkEntry(row, font=ctk.CTkFont(size=11), fg_color=c["input_bg"],
                             text_color=c["text"], border_color=c["input_border"])
            e.insert(0, self.config.get(key, ""))
            e.pack(side="left", fill="x", expand=True, padx=5)
            setattr(self, attr, e)
            ctk.CTkButton(row, text="…", width=34, fg_color=c["card"],
                hover_color=c["card_hover"], text_color=c["text"],
                command=lambda a=attr: self._browse(a)).pack(side="left")
        ctk.CTkButton(self._content, text="🔍 Автоматично намери Spotify.dll",
            width=240, fg_color=c["card"], hover_color=c["card_hover"],
            text_color=c["text"], command=self._auto_dll).pack(pady=6)
        self._wvd_l1_var = ctk.BooleanVar(value=self.config.get("wvd_l1", False))
        ctk.CTkCheckBox(self._content, text="L1 сертифициран .wvd", variable=self._wvd_l1_var,
            fg_color=c["accent"], text_color=c["text"],
            command=self._refresh_ctx_labels).pack(anchor="w", pady=2)
        self._ctx_note = ctk.CTkLabel(self._content, text="", font=ctk.CTkFont(size=11),
                                      text_color=c["text_secondary"])
        self._ctx_note.pack(anchor="w", pady=4)
        self._refresh_ctx_labels()

    def _browse(self, attr):
        p = filedialog.askopenfilename(filetypes=[("Files", "*.txt *.dll *.wvd"), ("All", "*.*")])
        if p:
            e = getattr(self, attr)
            e.delete(0, "end")
            e.insert(0, p)
            self._refresh_ctx_labels()

    def _auto_dll(self):
        dll = self.votify.find_spotify_dll()
        if dll:
            self._dll_entry.delete(0, "end")
            self._dll_entry.insert(0, dll)
            messagebox.showinfo("DLL", f"Намерен:\n{dll}")
        else:
            messagebox.showwarning("DLL",
                "Spotify.dll не е намерен.\nИнсталирайте Spotify desktop 1.2.88.483.")
            webbrowser.open(self.SPOTIFY_DL_URL)
        self._refresh_ctx_labels()

    def _refresh_ctx_labels(self):
        if not hasattr(self, "_ctx_note"):
            return
        ctx = self._ctx()
        from formats import check_locks
        unlocked = sum(1 for s in FORMATS if not check_locks(s, ctx))
        self._ctx_note.configure(
            text=f"С текущите настройки са отключени {unlocked} от {len(FORMATS)} формата.")

    def _validate_cookies(self):
        p = self._cookies_entry.get().strip()
        if not p or not os.path.exists(p):
            messagebox.showwarning("Cookies", "Изберете валиден cookies.txt файл.")
            return False
        try:
            txt = open(p, "r", encoding="utf-8", errors="ignore").read()
        except Exception:
            messagebox.showerror("Cookies", "Файлът не може да се прочете.")
            return False
        if "sp_dc" not in txt:
            if not messagebox.askyesno("Cookies",
                    "Файлът не съдържа sp_dc.\nСигурни ли сте, че е верен?"):
                return False
        return True

    def _step_quality(self):
        c = self.theme.colors
        ctk.CTkLabel(self._content, text="Стъпка 2: Формат и качество",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=c["text"]).pack(pady=(10, 8))
        ctx = self._ctx()
        self._fmt_var = ctk.StringVar(value="")
        box = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        box.pack(fill="both", expand=True)
        for spec in FORMATS:
            r = ctk.CTkRadioButton(box, text=ui_label(spec, ctx),
                variable=self._fmt_var, value=spec.key,
                fg_color=c["accent"], text_color=c["text"],
                font=ctk.CTkFont(size=12), command=self._show_hint)
            r.pack(anchor="w", pady=2)
            if spec.key == self._fmt_key:
                self._fmt_var.set(spec.key)
        self._hint = ctk.CTkLabel(self._content, text="", font=ctk.CTkFont(size=11),
                                  text_color=c["warning"])
        self._hint.pack(anchor="w", pady=6)
        self._show_hint()

    def _show_hint(self):
        c = self.theme.colors
        spec = get_format(self._fmt_var.get() or self._fmt_key)
        self._fmt_key = spec.key
        h = ui_hint(spec, self._ctx())
        self._hint.configure(text=f"{spec.label}: {h}",
            text_color=c["success"] if h == "Достъпно" else c["warning"])

    def _step_complete(self):
        c = self.theme.colors
        ctk.CTkLabel(self._content, text="🎉 Готово!",
            font=ctk.CTkFont(size=28, weight="bold"), text_color=c["accent"]).pack(pady=(25, 10))
        spec = get_format(self._fmt_key)
        ctk.CTkLabel(self._content,
            text=f"cookies: {os.path.basename(self._cookies_entry.get() or '—')}\n"
                 f"DLL: {os.path.basename(self._dll_entry.get() or '—')}\n"
                 f"формат: {spec.label}\n\n"
                 "Внимание: Spotify може да ограничи акаунти с масово сваляне.\n"
                 "Не прекалявайте с темпото.",
            font=ctk.CTkFont(size=12), text_color=c["text"], justify="left").pack(pady=10)


def show_setup_wizard(parent, config, theme, votify, ffmpeg_ok=False, on_complete=None):
    w = SetupWizard(parent, config, theme, votify, ffmpeg_ok, on_complete)
    w.focus()
    return w
'''.lstrip()

# ─── gui.py ────────────────────────────────────────────────────────
FILES["gui.py"] = r'''
"""SpotiFlow — Main GUI (votify backend + formats-aware Settings)."""
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError:
    print("customtkinter not installed. Run: pip install customtkinter")
    sys.exit(1)

from config import Config
from theme_manager import ThemeManager
from spotify_client import SpotifyClient
from votify_manager import VotifyManager
from ffmpeg_manager import FFmpegManager
from downloader import DownloadManager, DownloadItem
from formats import (FORMATS, DEFAULT_KEY, get_format, ui_label, ui_hint,
                     CapabilityContext)
from setup_wizard import show_setup_wizard


class SpotiFlowGUI:
    def __init__(self):
        self.config = Config()
        self.theme = ThemeManager(self.config.get("theme", "dark"))
        self.spotify = SpotifyClient(self.config.get("client_id", ""),
                                     self.config.get("client_secret", ""))
        self.spotify.set_tokens(self.config.get("access_token", ""),
                                self.config.get("refresh_token", ""))
        self.votify = VotifyManager(config=self.config)
        self.ffmpeg = FFmpegManager(config=self.config)
        self.downloader = DownloadManager(config=self.config, spotify=self.spotify,
                                          votify=self.votify, ffmpeg=self.ffmpeg)
        self.downloader.add_listener(self._on_queue_changed)
        self._current_view = "home"
        self._current_user = None
        self._drag_drop_enabled = False
        self.root = ctk.CTk()
        self.root.title("SpotiFlow")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        ctk.set_appearance_mode(self.theme.mode)
        ctk.set_default_color_theme("dark-blue")
        self._build_ui()
        self._check_dependencies()
        if not self.config.get("setup_complete", False):
            self.root.after(500, self._show_setup_wizard)

    def _build_ui(self):
        c = self.theme.colors
        self.root.configure(fg_color=c["bg"])
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self._sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0,
                                     fg_color=c["bg_secondary"])
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_rowconfigure(6, weight=1)
        self._sidebar.grid_propagate(False)
        ctk.CTkLabel(self._sidebar, text="SpotiFlow",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=c["accent"]
            ).grid(row=0, column=0, pady=(20, 10), padx=20)
        self._nav_buttons = {}
        for idx, (key, label) in enumerate([("home", "🏠  Home"), ("search", "🔍  Search"),
                ("library", "📚  Library"), ("downloads", "⬇️  Downloads"),
                ("settings", "⚙️  Settings")], start=1):
            b = ctk.CTkButton(self._sidebar, text=label, font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color=c["card_hover"],
                text_color=c["text"], anchor="w", height=36, corner_radius=8)
            b.grid(row=idx, column=0, pady=3, padx=12, sticky="ew")
            b.configure(command=lambda k=key: self._switch_view(k))
            self._nav_buttons[key] = b
        ctk.CTkButton(self._sidebar, text="🌗  Theme", font=ctk.CTkFont(size=12),
            fg_color=c["card"], hover_color=c["card_hover"], text_color=c["text"],
            height=32, corner_radius=8, command=self._toggle_theme
            ).grid(row=7, column=0, pady=5, padx=12, sticky="ew")
        self._user_frame = ctk.CTkFrame(self._sidebar, height=50,
                                        fg_color=c["card"], corner_radius=8)
        self._user_frame.grid(row=8, column=0, pady=(5, 15), padx=12, sticky="ew")
        self._user_frame.grid_propagate(False)
        u = ctk.CTkLabel(self._user_frame, text="Not logged in",
                         font=ctk.CTkFont(size=11), text_color=c["text_secondary"])
        u.place(relx=0.5, rely=0.5, anchor="center")
        self._content = ctk.CTkFrame(self.root, fg_color=c["bg"], corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)
        self.scroll_frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self._status_bar = ctk.CTkFrame(self.root, height=28,
                                        fg_color=c["bg_secondary"], corner_radius=0)
        self._status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._status_bar.grid_propagate(False)
        self._status_label = ctk.CTkLabel(self._status_bar, text="Ready",
            font=ctk.CTkFont(size=11), text_color=c["text_secondary"])
        self._status_label.pack(side="left", padx=12, pady=4)
        self._queue_count_label = ctk.CTkLabel(self._status_bar, text="Queue: 0",
            font=ctk.CTkFont(size=11), text_color=c["text_secondary"])
        self._queue_count_label.pack(side="right", padx=12, pady=4)
        self._switch_view("home")
        self._setup_drag_drop()

    def _setup_drag_drop(self):
        try:
            import windnd
            windnd.hook_dropfiles(self.root, func=self._on_drop)
            self._drag_drop_enabled = True
        except Exception:
            self._drag_drop_enabled = False

    def _on_drop(self, files):
        def process():
            for f in files:
                try:
                    p = f.decode("utf-8") if isinstance(f, bytes) else str(f)
                    if os.path.isfile(p):
                        with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                            self._process_urls_bulk(fh.read())
                    else:
                        self._process_urls_bulk(p)
                except Exception:
                    pass
        self.root.after(0, process)

    def _toggle_theme(self):
        self.config.set("theme", self.theme.toggle())
        ctk.set_appearance_mode(self.theme.mode)
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        if self._current_user:
            self._update_user_ui(self._current_user)

    def _switch_view(self, name):
        self._current_view = name
        c = self.theme.colors
        for key, b in self._nav_buttons.items():
            if key == name:
                b.configure(fg_color=c["card"], text_color=c["accent"])
            else:
                b.configure(fg_color="transparent", text_color=c["text"])
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        m = getattr(self, "_show_" + name, None)
        if m:
            m()

    def _on_queue_changed(self):
        if self.root and self.root.winfo_exists():
            self.root.after(0, self._update_queue_count)
            if self._current_view == "downloads":
                self.root.after(0, self._refresh_downloads_view)

    def _update_queue_count(self):
        self._queue_count_label.configure(text=f"Queue: {len(self.downloader.get_queue())}")

    def _process_urls_bulk(self, text):
        urls = self.spotify.bulk_extract_urls(text)
        if not urls:
            self._status_label.configure(text="No Spotify URLs found")
            return
        for u in urls:
            self._add_url_to_queue(u)
        self._status_label.configure(text=f"Added {len(urls)} items to queue")
        if self._current_view != "downloads":
            self._switch_view("downloads")

    def _add_url_to_queue(self, url):
        item_type, item_id = self.spotify.parse_url(url)
        if not item_type:
            return
        if item_type == "track" and self.spotify.is_authenticated():
            def fetch():
                track = self.spotify.get_track(item_id)
                if track and self.root and self.root.winfo_exists():
                    self.root.after(0, lambda t=track: self._enqueue_track(t))
            threading.Thread(target=fetch, daemon=True).start()
        else:
            # track без OAuth / album / playlist / artist: votify ги разбира директно
            self.downloader.add_item(DownloadItem(
                track_id=url if item_type != "track" else item_id,
                track_name=item_type, artist_name="Spotify"))
            self._update_queue_count()

    def _enqueue_track(self, track):
        if not track:
            return
        artists = track.get("artists", [])
        album = track.get("album", {})
        images = album.get("images", [])
        self.downloader.add_item(DownloadItem(
            track_id=track.get("id", ""), track_name=track.get("name", "Unknown"),
            artist_name=artists[0].get("name", "Unknown") if artists else "Unknown",
            album_name=album.get("name", ""), duration_ms=track.get("duration_ms", 0),
            cover_url=images[0].get("url", "") if images else ""))
        self._update_queue_count()

    def _show_home(self):
        c = self.theme.colors
        f = self.scroll_frame
        hero = ctk.CTkFrame(f, fg_color=c["card"], corner_radius=16, height=150)
        hero.grid(row=0, column=0, pady=(20, 15), padx=20, sticky="ew")
        hero.grid_propagate(False)
        ctk.CTkLabel(hero, text="Welcome to SpotiFlow",
            font=ctk.CTkFont(size=28, weight="bold"), text_color=c["text"]
            ).place(relx=0.5, rely=0.35, anchor="center")
        ctk.CTkLabel(hero, text="Lossless downloads, директно от Spotify",
            font=ctk.CTkFont(size=13), text_color=c["text_secondary"]
            ).place(relx=0.5, rely=0.62, anchor="center")
        url_card = ctk.CTkFrame(f, fg_color=c["card"], corner_radius=12)
        url_card.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        url_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(url_card, text="Paste Spotify URLs (track / album / playlist):",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=c["text"]
            ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        self._url_entry = ctk.CTkEntry(url_card,
            placeholder_text="https://open.spotify.com/track/... or spotify:track:...",
            font=ctk.CTkFont(size=12), fg_color=c["input_bg"], text_color=c["text"],
            placeholder_text_color=c["text_muted"], border_color=c["input_border"],
            corner_radius=8, height=40)
        self._url_entry.grid(row=1, column=0, padx=15, pady=(5, 10), sticky="ew")
        ctk.CTkButton(url_card, text="➕ Add to Queue", font=ctk.CTkFont(size=12, weight="bold"),
            width=140, height=36, corner_radius=8, fg_color=c["accent"],
            hover_color=c["accent_hover"], text_color="white",
            command=self._add_url_from_entry).grid(row=1, column=1, padx=(5, 15), pady=(5, 10))
        if self._drag_drop_enabled:
            ctk.CTkLabel(f, text="Tip: влачете .txt файлове с връзки директно в прозореца",
                font=ctk.CTkFont(size=11), text_color=c["text_muted"]
                ).grid(row=2, column=0, pady=5, padx=20)

    def _add_url_from_entry(self):
        t = self._url_entry.get().strip()
        if not t:
            return
        self._process_urls_bulk(t)
        self._url_entry.delete(0, "end")

    def _show_search(self):
        c = self.theme.colors
        f = self.scroll_frame
        ctk.CTkLabel(f, text="Search Spotify", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=c["text"]).grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        sf = ctk.CTkFrame(f, fg_color=c["card"], corner_radius=12)
        sf.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        sf.grid_columnconfigure(0, weight=1)
        self._search_entry = ctk.CTkEntry(sf, placeholder_text="Търси изпълнители и песни...",
            font=ctk.CTkFont(size=13), fg_color=c["input_bg"], text_color=c["text"],
            placeholder_text_color=c["text_muted"], border_color=c["input_border"],
            corner_radius=8, height=40)
        self._search_entry.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        self._search_entry.bind("<Return>", lambda e: self._do_search())
        ctk.CTkButton(sf, text="🔍 Search", font=ctk.CTkFont(size=12, weight="bold"), width=100,
            height=36, corner_radius=8, fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color="white", command=self._do_search).grid(row=0, column=1, padx=(5, 15), pady=15)
        self._search_results = ctk.CTkScrollableFrame(f, fg_color="transparent", height=500)
        self._search_results.grid(row=2, column=0, pady=10, padx=20, sticky="nsew")
        self._search_results.grid_columnconfigure(0, weight=1)
        if not self.spotify.is_authenticated():
            ctk.CTkLabel(self._search_results,
                text="Search изисква OAuth login (Settings → Spotify OAuth).",
                font=ctk.CTkFont(size=12), text_color=c["text_muted"]).grid(row=0, column=0, pady=40)

    def _do_search(self):
        q = self._search_entry.get().strip()
        if not q or not self.spotify.is_authenticated():
            return
        def work():
            r = self.spotify.search_tracks(q, limit=20)
            if self.root and self.root.winfo_exists():
                self.root.after(0, lambda: self._display_search_results(r))
        threading.Thread(target=work, daemon=True).start()

    def _display_search_results(self, result):
        c = self.theme.colors
        for w in self._search_results.winfo_children():
            w.destroy()
        if not result or not result.get("tracks", {}).get("items"):
            ctk.CTkLabel(self._search_results, text="No results",
                text_color=c["text_muted"]).grid(row=0, column=0, pady=40)
            return
        for idx, t in enumerate(result["tracks"]["items"]):
            self._track_row(self._search_results, t, idx)

    def _track_row(self, parent, t, idx):
        c = self.theme.colors
        artists = t.get("artists", [])
        an = artists[0].get("name", "Unknown") if artists else "Unknown"
        al = t.get("album", {})
        row = ctk.CTkFrame(parent, fg_color=c["card"], height=56)
        row.grid_propagate(False)
        row.grid_columnconfigure(1, weight=1)
        row.grid(row=idx, column=0, pady=3, sticky="ew")
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(info, text=t.get("name", "?")[:40],
            font=ctk.CTkFont(size=12, weight="bold"), text_color=c["text"]).pack(anchor="w")
        ctk.CTkLabel(info, text=f"{an}  |  {al.get('name', '')[:30]}",
            font=ctk.CTkFont(size=10), text_color=c["text_secondary"]).pack(anchor="w")
        ctk.CTkButton(row, text="➕", width=32, height=32, corner_radius=16,
            fg_color=c["accent"], hover_color=c["accent_hover"], text_color="white",
            command=lambda t=t: self._enqueue_track(t)).grid(row=0, column=1, padx=(5, 10), pady=8)

    def _show_library(self):
        c = self.theme.colors
        f = self.scroll_frame
        ctk.CTkLabel(f, text="Library", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=c["text"]).grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        if not self.spotify.is_authenticated():
            ctk.CTkLabel(f, text="Please log in (Settings → Spotify OAuth).",
                font=ctk.CTkFont(size=13), text_color=c["text_secondary"]
                ).grid(row=1, column=0, pady=50)
            return
        for idx, (label, cmd) in enumerate([("❤️ Load Liked Songs", self._load_saved),
                                            ("📋 Load Playlists", self._load_playlists)], 1):
            ctk.CTkButton(f, text=label, font=ctk.CTkFont(size=12), fg_color=c["accent"],
                hover_color=c["accent_hover"], text_color="white",
                command=cmd).grid(row=idx, column=0, pady=4, padx=20, sticky="w")
        self._lib_frame = ctk.CTkScrollableFrame(f, fg_color="transparent", height=450)
        self._lib_frame.grid(row=3, column=0, pady=10, padx=20, sticky="nsew")
        self._lib_frame.grid_columnconfigure(0, weight=1)

    def _load_saved(self):
        def work():
            r = self.spotify.get_saved_tracks(limit=50)
            if self.root and self.root.winfo_exists():
                self.root.after(0, lambda: self._show_saved(r))
        threading.Thread(target=work, daemon=True).start()

    def _show_saved(self, result):
        for w in self._lib_frame.winfo_children():
            w.destroy()
        if not result or not result.get("items"):
            return
        tracks = [i.get("track") for i in result["items"] if i.get("track")]
        for idx, t in enumerate(tracks):
            self._track_row(self._lib_frame, t, idx)

    def _load_playlists(self):
        def work():
            r = self.spotify.get_user_playlists(limit=50)
            if self.root and self.root.winfo_exists():
                self.root.after(0, lambda: self._show_playlists(r))
        threading.Thread(target=work, daemon=True).start()

    def _show_playlists(self, result):
        c = self.theme.colors
        for w in self._lib_frame.winfo_children():
            w.destroy()
        if not result or not result.get("items"):
            return
        for idx, pl in enumerate(result["items"]):
            row = ctk.CTkFrame(self._lib_frame, fg_color=c["card"], height=56)
            row.grid_propagate(False)
            row.grid_columnconfigure(1, weight=1)
            row.grid(row=idx, column=0, pady=3, sticky="ew")
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=0, padx=12, pady=8, sticky="w")
            ctk.CTkLabel(info, text=pl.get("name", "?")[:40],
                font=ctk.CTkFont(size=12, weight="bold"), text_color=c["text"]).pack(anchor="w")
            ctk.CTkLabel(info, text=f"{pl.get('tracks', {}).get('total', 0)} tracks",
                font=ctk.CTkFont(size=10), text_color=c["text_secondary"]).pack(anchor="w")
            ctk.CTkButton(row, text="➕", width=32, height=32, corner_radius=16,
                fg_color=c["accent"], hover_color=c["accent_hover"], text_color="white",
                command=lambda p=pl: self._add_playlist(p)
                ).grid(row=0, column=1, padx=(5, 10), pady=8)

    def _add_playlist(self, pl):
        self.downloader.add_item(DownloadItem(
            track_id=pl.get("external_urls", {}).get("spotify", f"spotify:playlist:{pl.get('id')}"),
            track_name="playlist", artist_name=pl.get("name", "Playlist")))
        self._update_queue_count()
        self._status_label.configure(text=f"Playlist added: {pl.get('name', '')}")

    def _show_downloads(self):
        c = self.theme.colors
        f = self.scroll_frame
        ctk.CTkLabel(f, text="Downloads", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=c["text"]).grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctrl = ctk.CTkFrame(f, fg_color="transparent")
        ctrl.grid(row=1, column=0, pady=5, padx=20, sticky="w")
        ctk.CTkButton(ctrl, text="Start", width=80, height=32, corner_radius=8,
            fg_color=c["accent"], hover_color=c["accent_hover"], text_color="white",
            command=self._start_downloads).pack(side="left", padx=3)
        ctk.CTkButton(ctrl, text="Stop", width=80, height=32, corner_radius=8,
            fg_color=c["danger"], hover_color="#ff4466", text_color="white",
            command=self._stop_downloads).pack(side="left", padx=3)
        ctk.CTkButton(ctrl, text="Clear", width=80, height=32, corner_radius=8,
            fg_color=c["card"], hover_color=c["card_hover"], text_color=c["text"],
            command=self._clear_completed).pack(side="left", padx=3)
        ctk.CTkButton(ctrl, text="M3U", width=80, height=32, corner_radius=8,
            fg_color=c["card"], hover_color=c["card_hover"], text_color=c["text"],
            command=self._export_m3u).pack(side="left", padx=3)
        self._queue_frame = ctk.CTkScrollableFrame(f, fg_color="transparent", height=480)
        self._queue_frame.grid(row=2, column=0, pady=10, padx=20, sticky="nsew")
        self._queue_frame.grid_columnconfigure(0, weight=1)
        self._refresh_downloads_view()

    def _refresh_downloads_view(self):
        if not hasattr(self, "_queue_frame") or not self._queue_frame.winfo_exists():
            return
        c = self.theme.colors
        for w in self._queue_frame.winfo_children():
            w.destroy()
        queue = self.downloader.get_queue()
        if not queue:
            ctk.CTkLabel(self._queue_frame, text="Queue is empty",
                text_color=c["text_muted"]).grid(row=0, column=0, pady=50)
            return
        colors = {DownloadItem.STATUS_PENDING: c["text_muted"],
                  DownloadItem.STATUS_DOWNLOADING: c["accent"],
                  DownloadItem.STATUS_CONVERTING: c["warning"],
                  DownloadItem.STATUS_COMPLETED: c["success"],
                  DownloadItem.STATUS_FAILED: c["danger"],
                  DownloadItem.STATUS_CANCELLED: c["text_muted"]}
        for idx, it in enumerate(queue):
            row = ctk.CTkFrame(self._queue_frame,
                fg_color=c["queue_bg"] if idx % 2 == 0 else c["queue_alt"])
            row.grid_columnconfigure(1, weight=1)
            row.grid(row=idx, column=0, pady=2, sticky="ew")
            ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=14),
                text_color=colors.get(it.status, c["text_muted"]), width=25
                ).grid(row=0, column=0, padx=(10, 5), pady=8)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=1, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(info, text=f"{it.artist_name} - {it.track_name}"[:60],
                font=ctk.CTkFont(size=11, weight="bold"), text_color=c["text"]).pack(anchor="w")
            ctk.CTkLabel(info, text=it.message or it.status, font=ctk.CTkFont(size=10),
                text_color=c["text_secondary"]).pack(anchor="w")
            if it.status in (DownloadItem.STATUS_DOWNLOADING, DownloadItem.STATUS_CONVERTING):
                p = ctk.CTkProgressBar(row, width=100, height=4, corner_radius=2,
                    fg_color=c["progress_bg"], progress_color=c["accent"])
                p.grid(row=0, column=2, padx=10, pady=8)
                p.set(it.progress / 100.0)
            if it.status in (DownloadItem.STATUS_COMPLETED, DownloadItem.STATUS_FAILED,
                             DownloadItem.STATUS_CANCELLED):
                ctk.CTkButton(row, text="x", width=24, height=24, corner_radius=12,
                    fg_color="transparent", hover_color=c["danger"], text_color=c["text_muted"],
                    command=lambda i=it: self._remove_item(i)).grid(row=0, column=3, padx=(5, 10), pady=8)

    def _remove_item(self, item):
        self.downloader.remove_item(item)
        self._update_queue_count()
        self._refresh_downloads_view()

    def _start_downloads(self):
        if not self.downloader.is_running():
            self.downloader.start()
            self._status_label.configure(text="Starting downloads...")

    def _stop_downloads(self):
        self.downloader.stop()
        self._status_label.configure(text="Stopping downloads...")

    def _clear_completed(self):
        for it in list(self.downloader.get_queue()):
            if it.status in (DownloadItem.STATUS_COMPLETED, DownloadItem.STATUS_FAILED,
                             DownloadItem.STATUS_CANCELLED):
                self.downloader.remove_item(it)
        self._update_queue_count()
        self._refresh_downloads_view()

    def _export_m3u(self):
        p = self.downloader.export_m3u()
        if p:
            messagebox.showinfo("M3U Export", f"Playlist saved to:\n{p}")
        else:
            messagebox.showwarning("Empty queue", "No completed downloads to export.")

    def _show_settings(self):
        c = self.theme.colors
        f = self.scroll_frame
        ctk.CTkLabel(f, text="Settings", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=c["text"]).grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        # OAuth card
        auth = ctk.CTkFrame(f, fg_color=c["card"], corner_radius=12)
        auth.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        auth.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(auth, text="Spotify OAuth (за Search/Library — не е задължително за сваляне)",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=c["text"]
            ).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")
        ctk.CTkLabel(auth, text="Client ID:", font=ctk.CTkFont(size=12),
                     text_color=c["text_secondary"]).grid(row=1, column=0, padx=15, pady=5, sticky="w")
        self._cid_entry = ctk.CTkEntry(auth, font=ctk.CTkFont(size=12), fg_color=c["input_bg"],
            text_color=c["text"], border_color=c["input_border"], corner_radius=6)
        self._cid_entry.grid(row=1, column=1, padx=(5, 15), pady=5, sticky="ew")
        self._cid_entry.insert(0, self.config.get("client_id", ""))
        ctk.CTkLabel(auth, text="Client Secret:", font=ctk.CTkFont(size=12),
                     text_color=c["text_secondary"]).grid(row=2, column=0, padx=15, pady=5, sticky="w")
        self._csec_entry = ctk.CTkEntry(auth, font=ctk.CTkFont(size=12), show="*",
            fg_color=c["input_bg"], text_color=c["text"], border_color=c["input_border"], corner_radius=6)
        self._csec_entry.grid(row=2, column=1, padx=(5, 15), pady=5, sticky="ew")
        self._csec_entry.insert(0, self.config.get("client_secret", ""))
        ctk.CTkLabel(auth, text="Auth Code:", font=ctk.CTkFont(size=12),
                     text_color=c["text_secondary"]).grid(row=3, column=0, padx=15, pady=5, sticky="w")
        self._code_entry = ctk.CTkEntry(auth, font=ctk.CTkFont(size=12), fg_color=c["input_bg"],
            text_color=c["text"], border_color=c["input_border"], corner_radius=6,
            placeholder_text="Paste code from browser URL here",
            placeholder_text_color=c["text_muted"])
        self._code_entry.grid(row=3, column=1, padx=(5, 15), pady=5, sticky="ew")
        bf = ctk.CTkFrame(auth, fg_color="transparent")
        bf.grid(row=4, column=0, columnspan=2, padx=15, pady=(10, 15), sticky="w")
        ctk.CTkButton(bf, text="Get URL", width=90, height=32, corner_radius=8,
            fg_color=c["accent"], hover_color=c["accent_hover"], text_color="white",
            command=self._get_auth_url).pack(side="left", padx=3)
        ctk.CTkButton(bf, text="Login", width=80, height=32, corner_radius=8,
            fg_color=c["accent"], hover_color=c["accent_hover"], text_color="white",
            command=self._do_login).pack(side="left", padx=3)
        ctk.CTkButton(bf, text="Save", width=80, height=32, corner_radius=8,
            fg_color=c["card_hover"], hover_color=c["accent"], text_color=c["text"],
            command=self._save_credentials).pack(side="left", padx=3)
        # Quality & Format card
        qf = ctk.CTkFrame(f, fg_color=c["card"], corner_radius=12)
        qf.grid(row=2, column=0, pady=10, padx=20, sticky="ew")
        qf.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(qf, text="Качество и формат", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=c["text"]).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 8), sticky="w")
        self._premium_var = tk.BooleanVar(value=self.config.get("premium", False))
        ctk.CTkCheckBox(qf, text="Premium акаунт", variable=self._premium_var,
            font=ctk.CTkFont(size=12), fg_color=c["accent"], text_color=c["text"],
            command=self._refresh_format_menu).grid(row=1, column=0, columnspan=2, padx=15, sticky="w")
        ctk.CTkLabel(qf, text="Бележка: грешен флаг = грешка при сваляне.",
            font=ctk.CTkFont(size=10), text_color=c["text_muted"]
            ).grid(row=2, column=0, columnspan=2, padx=15, sticky="w")
        for row, (lbl, attr, key) in enumerate([("cookies.txt:", "_cookies_entry", "cookies_path"),
                ("Spotify.dll:", "_dll_entry", "spotify_dll_path"),
                (".wvd файл:", "_wvd_entry", "wvd_path")], start=3):
            ctk.CTkLabel(qf, text=lbl, font=ctk.CTkFont(size=12),
                text_color=c["text_secondary"]).grid(row=row, column=0, padx=15, pady=4, sticky="w")
            e = ctk.CTkEntry(qf, font=ctk.CTkFont(size=11), fg_color=c["input_bg"],
                text_color=c["text"], border_color=c["input_border"], corner_radius=6)
            e.insert(0, self.config.get(key, ""))
            e.grid(row=row, column=1, padx=(5, 15), pady=4, sticky="ew")
            setattr(self, attr, e)
        ctk.CTkButton(qf, text="🔍 Auto DLL", width=90, height=28, corner_radius=6,
            fg_color=c["card_hover"], hover_color=c["accent"], text_color=c["text"],
            command=self._auto_dll).grid(row=3, column=1, padx=(5, 15), pady=0, sticky="e")
        self._wvd_l1_var = tk.BooleanVar(value=self.config.get("wvd_l1", False))
        ctk.CTkCheckBox(qf, text="L1 сертифициран .wvd", variable=self._wvd_l1_var,
            font=ctk.CTkFont(size=11), fg_color=c["accent"], text_color=c["text"],
            command=self._refresh_format_menu).grid(row=6, column=0, columnspan=2, padx=15, sticky="w")
        self._fmt_var = tk.StringVar()
        self._fmt_menu = ctk.CTkOptionMenu(qf, values=[], variable=self._fmt_var,
            font=ctk.CTkFont(size=12), fg_color=c["input_bg"], button_color=c["accent"],
            button_hover_color=c["accent_hover"], text_color=c["text"],
            command=self._on_format_change)
        self._fmt_menu.grid(row=7, column=0, columnspan=2, padx=15, pady=8, sticky="ew")
        self._fmt_hint = ctk.CTkLabel(qf, text="", font=ctk.CTkFont(size=10),
                                      text_color=c["warning"])
        self._fmt_hint.grid(row=8, column=0, columnspan=2, padx=15, sticky="w")
        ctk.CTkButton(qf, text="Запази", width=110, height=32, corner_radius=8,
            fg_color=c["accent"], hover_color=c["accent_hover"], text_color="white",
            command=self._save_quality_settings).grid(row=9, column=0, columnspan=2, padx=15, pady=(8, 15))
        self._refresh_format_menu()
        # Dependencies card
        dep = ctk.CTkFrame(f, fg_color=c["card"], corner_radius=12)
        dep.grid(row=3, column=0, pady=10, padx=20, sticky="ew")
        ctk.CTkLabel(dep, text="Dependencies", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=c["text"]).grid(row=0, column=0, padx=15, pady=(15, 8), sticky="w")
        vok = self.votify.is_installed()
        ctk.CTkLabel(dep, text=f"votify: {'Installed' if vok else 'Missing'}",
            font=ctk.CTkFont(size=12),
            text_color=c["success"] if vok else c["danger"]).grid(row=1, column=0, padx=15, sticky="w")
        fok = self.ffmpeg.is_available()
        ctk.CTkLabel(dep, text=f"FFmpeg: {'Installed' if fok else 'Missing'}",
            font=ctk.CTkFont(size=12),
            text_color=c["success"] if fok else c["warning"]).grid(row=2, column=0, padx=15, sticky="w")
        ctk.CTkLabel(dep, text="За MP3/AAC формати сложете ffmpeg.exe до приложението.",
            font=ctk.CTkFont(size=10), text_color=c["text_muted"]
            ).grid(row=3, column=0, padx=15, pady=(2, 8), sticky="w")
        ctk.CTkButton(dep, text="🔄 Стартирай Setup Wizard", width=200, height=32,
            corner_radius=8, fg_color=c["card_hover"], hover_color=c["accent"],
            text_color=c["text"], command=self._show_setup_wizard
            ).grid(row=4, column=0, padx=15, pady=(5, 15), sticky="w")

    def _build_capability_context(self):
        return CapabilityContext(
            premium=bool(self._premium_var.get()),
            dll_path=self._dll_entry.get().strip() or None,
            wvd_path=self._wvd_entry.get().strip() or None,
            wvd_l1=bool(self._wvd_l1_var.get()),
            ffmpeg_available=bool(self.ffmpeg and self.ffmpeg.is_available()))

    def _refresh_format_menu(self):
        ctx = self._build_capability_context()
        self._fmt_map = {ui_label(s, ctx): s.key for s in FORMATS}
        current = get_format(self.config.get("audio_format", DEFAULT_KEY))
        self._fmt_menu.configure(values=list(self._fmt_map))
        self._fmt_var.set(ui_label(current, ctx))
        self._on_format_change(self._fmt_var.get())

    def _on_format_change(self, label):
        c = self.theme.colors
        key = self._fmt_map.get(label, DEFAULT_KEY)
        self.config.set("audio_format", key)
        h = ui_hint(get_format(key), self._build_capability_context())
        self._fmt_hint.configure(text=h,
            text_color=c["success"] if h == "Достъпно" else c["warning"])

    def _save_quality_settings(self):
        self.config.set("premium", bool(self._premium_var.get()))
        self.config.set("cookies_path", self._cookies_entry.get().strip())
        self.config.set("spotify_dll_path", self._dll_entry.get().strip())
        self.config.set("wvd_path", self._wvd_entry.get().strip())
        self.config.set("wvd_l1", bool(self._wvd_l1_var.get()))
        self._refresh_format_menu()
        self._status_label.configure(text="Настройките са запазени")

    def _auto_dll(self):
        dll = self.votify.find_spotify_dll()
        if dll:
            self._dll_entry.delete(0, "end")
            self._dll_entry.insert(0, dll)
            self._refresh_format_menu()
        else:
            messagebox.showwarning("DLL", "Spotify.dll не е намерен автоматично.")

    def _get_auth_url(self):
        if not self.spotify.client_id or not self.spotify.client_secret:
            messagebox.showwarning("Missing data", "Enter Client ID and Secret first.")
            return
        import webbrowser
        url = self.spotify.get_auth_url()
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        webbrowser.open(url)
        messagebox.showinfo("URL copied", "OAuth URL copied to clipboard.")

    def _do_login(self):
        code = self._code_entry.get().strip()
        if not code:
            messagebox.showwarning("Missing code", "Paste the authorization code.")
            return
        def work():
            r = self.spotify.exchange_code(code)
            if self.root and self.root.winfo_exists():
                self.root.after(0, lambda: self._handle_login(r))
        threading.Thread(target=work, daemon=True).start()

    def _handle_login(self, result):
        if result and "access_token" in result:
            self.spotify.set_tokens(result["access_token"], result.get("refresh_token", ""))
            self.config.set("access_token", result["access_token"])
            self.config.set("refresh_token", result.get("refresh_token", ""))
            self._status_label.configure(text="Login successful!")
            self._fetch_user_profile()
        else:
            self._status_label.configure(text="Login error")
            messagebox.showerror("Error", "Authentication failed.")

    def _save_credentials(self):
        cid, csec = self._cid_entry.get().strip(), self._csec_entry.get().strip()
        self.config.set("client_id", cid)
        self.config.set("client_secret", csec)
        self.spotify.set_credentials(cid, csec)
        self._status_label.configure(text="Credentials saved")

    def _fetch_user_profile(self):
        def work():
            p = self.spotify.get_user_profile()
            if self.root and self.root.winfo_exists():
                self.root.after(0, lambda: self._update_user_ui(p))
        threading.Thread(target=work, daemon=True).start()

    def _update_user_ui(self, profile):
        if not profile:
            return
        self._current_user = profile
        for w in self._user_frame.winfo_children():
            w.destroy()
        c = self.theme.colors
        ctk.CTkLabel(self._user_frame, text=f"User: {profile.get('display_name', 'User')}",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=c["text"]
            ).place(relx=0.5, rely=0.5, anchor="center")

    def _check_dependencies(self):
        if not self.votify.is_installed():
            self._status_label.configure(text="votify missing - rebuild with new build.bat")

    def _show_setup_wizard(self):
        show_setup_wizard(self.root, self.config, self.theme, self.votify,
                          ffmpeg_ok=bool(self.ffmpeg and self.ffmpeg.is_available()),
                          on_complete=lambda: self._switch_view(self._current_view))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    SpotiFlowGUI().run()
'''.lstrip()

# ─── build.bat (Votify-ready) ──────────────────────────────────────
FILES["build.bat"] = r'''@echo off
chcp 65001 >nul
title SpotiFlow Auto Build (Votify Edition)
color 0A
echo ==========================================
echo   SpotiFlow Auto Build (Votify Edition)
echo ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install from python.org (Add to PATH!)
    pause
    exit /b 1
)
echo [OK] Python found.

echo Creating virtual environment...
if exist venv rmdir /s /q venv
python -m venv venv
if errorlevel 1 ( echo [ERROR] venv failed & pause & exit /b 1 )
call venv\Scripts\activate.bat

echo Installing dependencies (votify + GUI + requests + windnd)...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 ( echo [ERROR] deps failed & pause & exit /b 1 )
echo [OK] Dependencies installed.

REM debug mode: build.bat debug  ->  console with traceback
set CONSOLE=--windowed
if /i "%~1"=="debug" set CONSOLE=--console

echo Building EXE (%CONSOLE%)...
pyinstaller ^
--noconfirm ^
--clean ^
--name "SpotiFlow" ^
%CONSOLE% ^
--onefile ^
--collect-data customtkinter ^
--collect-data votify ^
--copy-metadata votify ^
--hidden-import yt_dlp ^
--exclude-module sklearn ^
--exclude-module cv2 ^
--exclude-module torch ^
--exclude-module tensorflow ^
--exclude-module matplotlib ^
--exclude-module pandas ^
--exclude-module scipy ^
--exclude-module nltk ^
--exclude-module sacremoses ^
main.py
if errorlevel 1 ( echo [ERROR] build failed & pause & exit /b 1 )

echo.
echo ==========================================
echo   BUILD SUCCESSFUL - dist\SpotiFlow.exe
echo ==========================================
pause
'''

# ─── portable.bat ─────────────────────────────────────────────────
FILES["portable.bat"] = r'''@echo off
echo Creating portable marker...
cd /d "%~dp0"
echo. > portable
echo [OK] Portable mode enabled.
echo Running build.bat...
call build.bat
'''

# ─── .gitignore ───────────────────────────────────────────────────
FILES[".gitignore"] = r'''# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual environment
venv/
.env/

# Build output
dist/
build/
*.spec

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# SpotiFlow
config.json
cookies.txt
*.log
portable
'''

# ─── README.md ────────────────────────────────────────────────────
FILES["README.md"] = r'''# SpotiFlow

Модерно desktop приложение за сваляне на музика от Spotify в lossless качество.

## Характеристики

- 🎵 **Lossless FLAC** (16-bit / 24-bit) — директно от Spotify CDN
- 🎙️ **Vorbis 320kbps** — стандартно качество за Premium
- 📥 **Batch downloads** — цели албуми и плейлисти
- 🎨 **Modern GUI** — CustomTkinter с dark/light теми
- 🔒 **Portable mode** — всичко в една папка
- 📝 **Synced lyrics** (.lrc) автоматично
- 🖼️ **Cover art** вграден в метаданните

## Изисквания

- **Python 3.10+** (за development)
- **Spotify Premium** акаунт
- **cookies.txt** (Netscape формат от браузъра)
- **Spotify.dll** (за FLAC lossless — версия 1.2.88.483)

## Инсталация (Development)

```bash
pip install -r requirements.txt
python main.py