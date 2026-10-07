"""Knowledge ingestion (apni machine par chalao).

  python ingest.py urls                      # sources.txt ke pages -> knowledge_cache/web/
  python ingest.py github owner/repo [...]   # repo shallow-clone -> knowledge_cache/github/

Rules: robots.txt maanta hai, har request ke beech delay rakhta hai, aur sirf local cache banata hai
(cache GitHub par push nahi hota). Sirf wahi repos/pages use karo jinki licence/terms allow karein.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

CACHE = Path("knowledge_cache")
UA = "AI-Assistant-ingest/1.0 (personal study use)"
DELAY = 2.0
TEXT_EXT = {".md", ".txt", ".sql", ".pks", ".pkb", ".xsl", ".xslt", ".java", ".py", ".json", ".yaml", ".yml", ".js"}
MAX_FILE = 200_000


def slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_")[:120]


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        t.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    lines = [ln.strip() for ln in root.get_text("\n").splitlines()]
    return "\n".join(ln for ln in lines if ln)


def allowed(url: str, cache: dict) -> bool:
    host = "{0.scheme}://{0.netloc}".format(urlparse(url))
    if host not in cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(host + "/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None
        cache[host] = rp
    rp = cache[host]
    return True if rp is None else rp.can_fetch(UA, url)


def ingest_urls(path: str = "sources.txt") -> None:
    out = CACHE / "web"
    out.mkdir(parents=True, exist_ok=True)
    robots: dict = {}
    urls = [l.strip() for l in Path(path).read_text().splitlines() if l.strip().startswith("http")]
    for i, url in enumerate(urls, 1):
        if not allowed(url, robots):
            print(f"[{i}/{len(urls)}] SKIP (robots.txt): {url}")
            continue
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"[{i}/{len(urls)}] FAIL {url}: {e}")
            continue
        text = html_to_text(r.text)
        if len(text) < 200:
            print(f"[{i}/{len(urls)}] SKIP (kam text): {url}")
            continue
        (out / f"{slug(url)}.txt").write_text(f"SOURCE: {url}\n{text}", encoding="utf-8")
        print(f"[{i}/{len(urls)}] OK {url} ({len(text)} chars)")
        time.sleep(DELAY)


def ingest_github(repo: str) -> None:
    name = repo.split("/")[-1]
    out = CACHE / "github" / name
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "clone", "--depth", "1", f"https://github.com/{repo}.git", str(tmp / name)], check=True)
        n = 0
        for p in (tmp / name).rglob("*"):
            if ".git" in p.parts or not p.is_file() or p.suffix.lower() not in TEXT_EXT:
                continue
            if p.stat().st_size > MAX_FILE:
                continue
            rel = p.relative_to(tmp / name)
            dest = out / (str(rel).replace("/", "__") + ".txt")
            dest.parent.mkdir(parents=True, exist_ok=True)
            body = p.read_text(encoding="utf-8", errors="ignore")
            dest.write_text(f"SOURCE: github.com/{repo}/{rel}\n{body}", encoding="utf-8")
            n += 1
        print(f"{repo}: {n} files ingest hui -> {out}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "urls":
        ingest_urls()
    elif len(sys.argv) >= 3 and sys.argv[1] == "github":
        for r in sys.argv[2:]:
            ingest_github(r)
    else:
        print(__doc__)
