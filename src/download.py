"""Standard-library-only downloader used by ``00_download_data.ipynb``.

Nothing here imports pandas, numpy or anything module-specific: the download
homework has to run on a bare Python install, before the teaching environment
exists. Downloads are idempotent (a file already present with the right
checksum is skipped), resumable-by-restart, and retried on transient failures.
"""
import hashlib
import shutil
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

from data_registry import SOURCES

# Some hosts (the OASIS site among them) drop connections from unfamiliar agents,
# so we present a normal browser string.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en",
}
TIMEOUT = 120
RETRIES = 3


def repo_root():
    return next(parent for parent in [Path.cwd(), *Path.cwd().parents] if (parent / "src").exists())


def raw_path(key):
    return repo_root() / SOURCES[key]["path"]


def sha256_of(path, chunk=1 << 20):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def human(n_bytes):
    if n_bytes < 1024:
        return f"{n_bytes} B"
    if n_bytes < 1024 ** 2:
        return f"{n_bytes / 1024:.0f} KB"
    return f"{n_bytes / 1024 ** 2:.1f} MB"


def check(key):
    """Return (status, detail) for one already-downloaded source.

    status is 'ok', 'mismatch' or 'missing'.
    """
    source = SOURCES[key]
    path = raw_path(key)
    if not path.exists():
        return "missing", "not downloaded yet"
    size = path.stat().st_size
    if source["sha256"] is None:
        # Volatile source: the file legitimately changes, so sanity-check the size.
        if size < source["bytes"] * 0.5:
            return "mismatch", f"only {human(size)}, expected roughly {human(source['bytes'])}"
        return "ok", f"{human(size)} (live source, size checked not pinned)"
    if sha256_of(path) == source["sha256"]:
        return "ok", f"{human(size)}, checksum verified"
    return "mismatch", f"{human(size)}, checksum does NOT match - delete the file and re-run"


def fetch(key, force=False, progress=True):
    """Download one source. Returns (status, detail)."""
    source = SOURCES[key]
    path = raw_path(key)
    if not force:
        status, detail = check(key)
        if status == "ok":
            return "skipped", detail

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    context = ssl.create_default_context()
    last_error = None

    for attempt in range(1, RETRIES + 1):
        try:
            request = urllib.request.Request(source["url"], headers=HEADERS)
            with urllib.request.urlopen(request, timeout=TIMEOUT, context=context) as response:
                declared = response.headers.get("Content-Length")
                total = int(declared) if declared else source["bytes"]
                downloaded = 0
                with open(temporary, "wb") as handle:
                    while True:
                        block = response.read(1 << 16)
                        if not block:
                            break
                        handle.write(block)
                        downloaded += len(block)
                        if progress and total:
                            done = int(30 * downloaded / max(total, 1))
                            bar = "#" * min(done, 30) + "." * max(0, 30 - done)
                            print(f"\r    [{bar}] {human(downloaded)}", end="", flush=True)
            if progress:
                print("\r" + " " * 60 + "\r", end="")
            shutil.move(str(temporary), str(path))
            status, detail = check(key)
            if status == "ok":
                return "downloaded", detail
            return "mismatch", detail
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            temporary.unlink(missing_ok=True)
            if attempt < RETRIES:
                time.sleep(2 * attempt)

    return "failed", f"{type(last_error).__name__}: {last_error}"


def copy_from_folder(key, folder):
    """Offline fallback: take the file from an instructor USB stick or share."""
    source = SOURCES[key]
    candidate = Path(folder) / Path(source["path"]).name
    if not candidate.exists():
        return "missing", f"{candidate.name} not present in {folder}"
    target = raw_path(key)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate, target)
    return "copied", check(key)[1]
