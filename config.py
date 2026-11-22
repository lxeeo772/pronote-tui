from __future__ import annotations
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

CONFIG_DIR = Path.home() / ".config" / "pronote-tui"
CONFIG_FILE = CONFIG_DIR / "config.json"

def normalize_pronote_url(url: str) -> str:
    """Normalise l'URL Pronote en préservant les paramètres de requête éventuels."""
    url = url.strip()
    if not url:
        return ""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if not path or path == "/":
        path = "/pronote/eleve.html"
    elif path.endswith("/pronote"):
        path = path + "/eleve.html"
    elif not path.endswith(".html"):
        path = path + "/eleve.html"
        
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))

@dataclass
class AppConfig:
    url: str = ""
    username: str = ""
    password: str = ""
    ent_name: str = "Aucun (Connexion directe)"
    remember_password: bool = False
    use_demo: bool = True
    theme: str = "pronote-dark"
    last_sync: str = ""

    @classmethod
    def load(cls) -> "AppConfig":
        if not CONFIG_FILE.exists():
            return cls()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception:
            return cls()

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        if not self.remember_password:
            data["password"] = ""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
