"""SpotiFlow — All-in-one bootstrap (Votify edition) + GitHub ready."""
import os
import shutil
from pathlib import Path

# Изтриваме старите файлове
OLD_FILES = [
    "librespot_manager.py", "auto_installer.py", "lyrics_manager.py",
    "spotify_client.py", "theme_manager.py", "config.py", "main.py",
    "gui.py", "downloader.py", "ffmpeg_manager.py", "build.bat",
    "portable.bat", "requirements.txt"
]

for f in OLD_FILES:
    p = Path(f)
    if p.exists():
        p.unlink()
        print(f"[DEL] {f}")

# Нови файлове
FILES = {}

FILES["requirements.txt"] = """customtkinter>=5.2.0
Pillow>=10.0.0
windnd>=1.0.7
requests>=2.31.0
votify[librespot]>=1.9.9
"""

FILES["config.py"] = r'''"""SpotiFlow — Configuration manager (portable + frozen aware)."""
import json, sys
from pathlib import Path

class Config:
    def __init__(self):
        self._data = {}
        self._portable = False
        self._config_path = self._resolve_path()
        self.load()

    def _resolve_path(self):
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).parent.resolve()
        if (base / "portable").exists():
            self._portable = True
            return base / "config.json"
        return Path.home() / ".spotiflow" / "config.json"

    def load(self):
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def save(self):
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None): return self._data.get(key, default)
    def set(self, key, value):
        self._data[key] = value
        self.save()

    @property
    def portable(self): return self._portable
'''

FILES["main.py"] = r'''"""SpotiFlow GUI — Entry point + votify passthrough за frozen EXE."""
import sys, os
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

if __name__ == "__main__":
    if "--spotiflow-votify" in sys.argv:
        i = sys.argv.index("--spotiflow-votify")
        sys.argv = sys.argv[:1] + sys.argv[i + 1:]
        from votify.__main__ import main as votify_main
        votify_main()
    else:
        from gui import SpotiFlowGUI
        SpotiFlowGUI().run()
'''

FILES["theme_manager.py"] = r'''"""SpotiFlow — Theme manager for customtkinter."""
class ThemeManager:
    DARK = {"bg": "#1a1a2e", "bg_secondary": "#16213e", "card": "#0f3460", "card_hover": "#1a4a7a",
            "accent": "#e94560", "accent_hover": "#ff6b81", "text": "#eaeaea", "text_secondary": "#a0a0a0",
            "text_muted": "#666666", "input_bg": "#0a0a1a", "input_border": "#2a2a4a", "success": "#4ade80",
            "warning": "#fbbf24", "danger": "#f87171", "progress_bg": "#2a2a4a", "queue_bg": "#1a1a2e",
            "queue_alt": "#16213e"}
    LIGHT = {"bg": "#f5f5f7", "bg_secondary": "#e8e8ec", "card": "#ffffff", "card_hover": "#f0f0f5",
             "accent": "#e11d48", "accent_hover": "#f43f5e", "text": "#1a1a2e", "text_secondary": "#666666",
             "text_muted": "#999999", "input_bg": "#ffffff", "input_border": "#d1d1d6", "success": "#22c55e",
             "warning": "#f59e0b", "danger": "#ef4444", "progress_bg": "#e5e5ea", "queue_bg": "#f5f5f7",
             "queue_alt": "#e8e8ec"}

    def __init__(self, mode="dark"):
        self._mode = mode
        self._colors = self.DARK if mode == "dark" else self.LIGHT

    @property
    def colors(self): return self._colors

    @property
    def mode(self): return self._mode

    def toggle(self):
        self._mode = "light" if self._mode == "dark" else "dark"
        self._colors = self.DARK if self._mode == "dark" else self.LIGHT
        return self._mode
'''

FILES["spotify_client.py"] = r'''"""SpotiFlow — Spotify Web API client with OAuth."""
import urllib.parse, urllib.request, json, base64, threading, re

class SpotifyClient:
    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"

    def __init__(self, client_id="", client_secret="", redirect_uri="http://localhost:8888/callback"):
        self.client_id, self.client_secret, self.redirect_uri = client_id, client_secret, redirect_uri
        self._access_token, self._refresh_token = "", ""

    def set_credentials(self, cid, csec): self.client_id, self.client_secret = cid, csec
    def set_tokens(self, at, rt=""): self._access_token, self._refresh_token = at, rt
    def is_authenticated(self): return bool(self._access_token)

    def get_auth_url(self, scope="user-read-private user-read-email playlist-read-private user-library-read"):
        return f"{self.AUTH_URL}?{urllib.parse.urlencode({'client_id': self.client_id, 'response_type': 'code', 'redirect_uri': self.redirect_uri, 'scope': scope})}"

    def exchange_code(self, code):
        if not self.client_id or not self.client_secret: return None
        creds = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        data = urllib.parse.urlencode({"grant_type": "authorization_code", "code": code, "redirect_uri": self.redirect_uri}).encode()
        req = urllib.request.Request(self.TOKEN_URL, data=data, headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp: return json.loads(resp.read().decode())
        except Exception as e: return {"error": str(e)}

    def _api_get(self, endpoint, params=None):
        if not self._access_token: return None
        url = f"{self.API_BASE}{endpoint}" + ("?" + urllib.parse.urlencode(params) if params else "")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self._access_token}"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp: return json.loads(resp.read().decode())
        except: return None

    def get_user_profile(self): return self._api_get("/me")
    def get_saved_tracks(self, limit=20, offset=0): return self._api_get("/me/tracks", {"limit": limit, "offset": offset})
    def get_user_playlists(self, limit=20, offset=0): return self._api_get("/me/playlists", {"limit": limit, "offset": offset})
    def search_tracks(self, query, limit=10): return self._api_get("/search", {"q": query, "type": "track", "limit": limit})
    def get_track(self, track_id): return self._api_get(f"/tracks/{track_id}")
    def get_playlist_tracks(self, playlist_id, limit=100, offset=0): return self._api_get(f"/playlists/{playlist_id}/tracks", {"limit": limit, "offset": offset})

    def parse_url(self, url):
        patterns = [(r"spotify:(track|playlist|album|artist):([a-zA-Z0-9]+)", 1, 2),
                    (r"open\.spotify\.com/(?:intl-[a-z]{2}(?:-[a-z]{2})?/)?(track|playlist|album|artist)/([a-zA-Z0-9]+)", 1, 2)]
        for p, g1, g2 in patterns:
            m = re.search(p, url)
            if m: return m.group(g1), m.group(g2)
        return None, None

    def bulk_extract_urls(self, text): return re.findall(r"https?://open\.spotify\.com/[^\s]+", text) + re.findall(r"spotify:[a-z]+:[a-zA-Z0-9]+", text)
'''

FILES["formats.py"] = r'''"""SpotiFlow — каталог формат->качество с ключалки (Premium/DLL/WVD)."""
from dataclasses import dataclass
from typing import List, Optional

SOURCE_LOSSY, SOURCE_LOSSLESS = "lossy", "lossless"

@dataclass(frozen=True)
class FormatSpec:
    key: str; label: str; family: str; bitrate_label: str; source: str
    votify_quality: str; session_type: str
    remux_mode: Optional[str] = None
    transcode_to: Optional[str] = None
    mp3_bitrate: Optional[str] = None
    requires_premium: bool = False
    requires_dll: bool = False
    requires_wvd: bool = False
    requires_wvd_l1: bool = False
    requires_ffmpeg: bool = False
    note: str = ""

@dataclass
class CapabilityContext:
    premium: bool = False
    dll_path: Optional[str] = None
    wvd_path: Optional[str] = None
    wvd_l1: bool = False
    ffmpeg_available: bool = False

FORMATS: List[FormatSpec] = [
    FormatSpec("mp3_96", "MP3 · ~96 kbps", "MP3", "~96k", SOURCE_LOSSY, "vorbis-low", "librespot", transcode_to="mp3", mp3_bitrate="96k", requires_ffmpeg=True),
    FormatSpec("ogg_96", "OGG · 96 kbps", "OGG", "96k", SOURCE_LOSSY, "vorbis-low", "librespot"),
    FormatSpec("mp3_160", "MP3 · 160 kbps", "MP3", "160k", SOURCE_LOSSY, "vorbis-medium", "librespot", transcode_to="mp3", mp3_bitrate="160k", requires_ffmpeg=True),
    FormatSpec("ogg_160", "OGG · 160 kbps", "OGG", "160k", SOURCE_LOSSY, "vorbis-medium", "librespot", note="По подразбиране"),
    FormatSpec("mp3_320", "MP3 · 320 kbps", "MP3", "320k", SOURCE_LOSSY, "vorbis-high", "librespot", transcode_to="mp3", mp3_bitrate="320k", requires_premium=True, requires_ffmpeg=True),
    FormatSpec("ogg_320", "OGG · 320 kbps", "OGG", "320k", SOURCE_LOSSY, "vorbis-high", "librespot", requires_premium=True),
    FormatSpec("aac_128", "AAC · 128 kbps", "AAC", "128k", SOURCE_LOSSY, "aac-medium", "librespot", remux_mode="ffmpeg", requires_wvd=True, requires_ffmpeg=True),
    FormatSpec("aac_256", "AAC · 256 kbps", "AAC", "256k", SOURCE_LOSSY, "aac-high", "librespot", remux_mode="ffmpeg", requires_wvd=True, requires_premium=True, requires_ffmpeg=True),
    FormatSpec("flac_16", "FLAC · 16-bit", "FLAC", "CD", SOURCE_LOSSLESS, "flac-flac", "desktop", requires_dll=True, requires_premium=True, note="Истински lossless"),
    FormatSpec("flac_24", "FLAC · 24-bit", "FLAC", "Hi-Res", SOURCE_LOSSLESS, "flac-flac-24", "desktop", requires_dll=True, requires_premium=True, note="Истински lossless, най-високо"),
    FormatSpec("flac_mp4_16", "FLAC (MP4) · 16-bit", "FLAC", "CD", SOURCE_LOSSLESS, "flac-mp4", "librespot", remux_mode="ffmpeg", requires_wvd=True, requires_wvd_l1=True, requires_premium=True, requires_ffmpeg=True, note="Без DLL, иска L1 Widevine"),
    FormatSpec("flac_mp4_24", "FLAC (MP4) · 24-bit", "FLAC", "Hi-Res", SOURCE_LOSSLESS, "flac-mp4-24", "librespot", remux_mode="ffmpeg", requires_wvd=True, requires_wvd_l1=True, requires_premium=True, requires_ffmpeg=True, note="Без DLL, иска L1 Widevine"),
]
DEFAULT_KEY = "ogg_160"

def get_format(key: str) -> FormatSpec:
    for s in FORMATS:
        if s.key == key: return s
    return get_format(DEFAULT_KEY)

def check_locks(spec: FormatSpec, ctx: CapabilityContext) -> List[str]:
    locks = []
    if spec.requires_premium and not ctx.premium: locks.append("Premium акаунт")
    if spec.requires_dll and not ctx.dll_path: locks.append("Spotify.dll (desktop 1.2.88.483)")
    if spec.requires_wvd and not ctx.wvd_path: locks.append(".wvd файл (Widevine)")
    if spec.requires_wvd_l1 and not ctx.wvd_l1: locks.append("L1 сертификация на .wvd")
    if spec.requires_ffmpeg and not ctx.ffmpeg_available: locks.append("FFmpeg")
    return locks

def ui_label(spec: FormatSpec, ctx: CapabilityContext) -> str:
    return spec.label if not check_locks(spec, ctx) else f"{spec.label} 🔒"

def ui_hint(spec: FormatSpec, ctx: CapabilityContext) -> str:
    locks = check_locks(spec, ctx)
    return "Достъпно" if not locks else "Заключено: " + ", ".join(locks)
'''

print("Bootstrap готов! Стартирайте:")
print("  python bootstrap_spotiflow_all.py")
print("  python bootstrap_spotiflow2.py")
print("  python bootstrap_spotiflow3.py")
print("След това:")
print("  git init")
print("  git add .")
print("  git commit -m 'Initial commit: Votify backend'")
print("  git remote add origin https://github.com/YOUR_USERNAME/spotiflow.git")
print("  git push -u origin main")