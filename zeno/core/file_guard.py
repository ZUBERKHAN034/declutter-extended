import logging
import os
import subprocess
import time
import sys
from pathlib import Path

# Partial download extensions from various browsers, download managers, and apps
PARTIAL_EXTENSIONS = {
    # Browsers
    ".crdownload",    # Chrome
    ".part",          # Firefox
    ".download",      # Safari / generic
    ".opdownload",    # Opera
    ".partial",       # Some download managers
    # Download managers
    ".!ut",           # uTorrent
    ".bc!",          # BitComet
    ".aria2",        # Aria2
    ".metalink",     # Metalink
    # Temporary files
    ".tmp",          # Generic temp
    ".temp",         # Generic temp
    ".cache",        # Cache files
    # Backup files (indicate file may be in progress)
    ".bak",          # Backup
    ".old",          # Old version
    # Partial upload extensions
    ".upload",       # Upload in progress
    ".uploading",    # Upload in progress
    ".part-upload", # Partial upload
    # Cloud sync temp files
    ".syncing",      # OneDrive/Google Drive syncing
    ".sync-pending", # Sync pending
    ".cloud",       # Cloud temp
    # IDE/Dev temp files (file may be open in editor)
    ".swp",          # Vim swap
    ".swo",          # Vim swap
    ".swp~",         # Vim backup
    ".tmp.swn",      # SciTE temp
    # Compression temp
    ".r0",           # RAR split
    ".r00",          # RAR split
    # Others
    ".downloading",  # Generic downloading
    ".incomplete",   # Incomplete download
    ".pending",      # Pending file
    ".swpx",         # Vim swap file variant
}

STABILITY_WAIT_SECONDS = 2.0
_timeout = 300
_enabled = True


def set_enabled(enabled: bool):
    global _enabled
    _enabled = enabled


def set_timeout(timeout: int):
    global _timeout
    _timeout = max(30, min(3600, timeout))


def is_partial_file(path: str) -> bool:
    """File has a partial download extension."""
    return Path(path).suffix.lower() in PARTIAL_EXTENSIONS


def has_partial_sibling(path: str) -> bool:
    """A .crdownload/.part etc exists next to file."""
    p = Path(path)
    dirname = p.parent
    basename = p.stem
    for ext in PARTIAL_EXTENSIONS:
        # Check for file.crdownload, file.txt.crdownload, etc.
        if (dirname / (basename + ext)).exists():
            return True
        if (dirname / (p.name + ext)).exists():
            return True
    return False


def is_file_locked(path: str) -> bool:
    """File is exclusively locked by another process."""
    try:
        with open(path, "rb+"):
            pass
        return False
    except (PermissionError, OSError):
        return True


def is_office_temp_file(path: str) -> bool:
    """Check for Office temporary files (Excel, Word, etc.)"""
    p = Path(path)
    name = p.name
    # Check for Office temp files like ~$file.xlsx, ~$document.docx
    if name.startswith("~$"):
        return True
    # Check for Excel temp files
    if "~" in name and name.endswith((".tmp", ".temp", ".lock")):
        return True
    return False


def is_vim_swap_file(path: str) -> bool:
    """Check for Vim swap files"""
    p = Path(path)
    name = p.name
    if name.endswith((".swp", ".swo", ".swn", ".swm", ".swpp")):
        return True
    if ".swp" in name or ".swo" in name:
        return True
    return False


def is_emacs_temp_file(path: str) -> bool:
    """Check for Emacs auto-save files"""
    p = Path(path)
    name = p.name
    # Emacs autosave files start with #
    if name.startswith("#") and name.endswith("#"):
        return True
    # Emacs backup files end with ~
    if name.endswith("~"):
        return True
    return False


def is_ide_temp_file(path: str) -> bool:
    """Check for various IDE temporary files"""
    p = Path(path)
    name = p.name.lower()
    ide_temp_patterns = [
        ".idea/",           # IntelliJ/PyCharm
        ".vscode/",        # VS Code
        ".settings/",      # Eclipse
        "node_modules/",   # npm (often being installed)
        ".git/objects/pack/", # Git pack files being written
    ]
    # Check for IDE metadata folders
    if any(pattern in str(p).lower() for pattern in ide_temp_patterns):
        return True
    return False


def is_system_cache_file(path: str) -> bool:
    """Check for system cache and thumbnail files"""
    p = Path(path)
    name = p.name.lower()
    cache_filenames = {
        "thumbs.db",        # Windows
        "thumbs.db:encryptable",
        "desktop.ini",     # Windows
        ".ds_store",       # macOS
        ".localized",      # macOS
        ".spotlight-v100/", # macOS Spotlight
        ".trashes/",       # macOS
        ".voluble/",       # macOS
        "trashinfo",       # Linux
    }
    if name in cache_filenames:
        return True
    # Check for Windows thumbnail cache
    if "thumbcache" in name and name.endswith(".db"):
        return True
    return False


def is_hidden_file(path: str) -> bool:
    """Check if file is hidden (Windows/macOS hidden attribute)"""
    p = Path(path)
    name = p.name
    # Unix-style hidden files
    if name.startswith(".") and name not in [".", ".."]:
        # But allow some common non-temp dot files
        allowed_dotfiles = {".bash_profile", ".bashrc", ".zshrc", ".gitignore",
                           ".gitconfig", ".ssh", ".vimrc", ".npmrc"}
        if name not in allowed_dotfiles:
            return True

    if sys.platform == "win32":
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))
            if attrs != -1 and (attrs & 2):  # FILE_ATTRIBUTE_HIDDEN
                return True
        except Exception:
            pass

    return False


def is_resource_fork(path: str) -> bool:
    """Check for macOS resource forks"""
    if sys.platform != "darwin":
        return False
    p = Path(path)
    # macOS resource forks are stored in ._filename
    if p.name.startswith("._"):
        return True
    return False


def is_sync_in_progress(path: str) -> bool:
    """Check for cloud sync in-progress indicators"""
    p = Path(path)
    dirname = p.parent

    # OneDrive sync indicators
    onedrive_indicators = [
        "OneDriveTemp",
        "OneDriveWorking",
    ]

    # Google Drive sync indicators
    gdrive_indicators = [
        ".gdrive_cache",
        ".google_drive_cache",
    ]

    # Dropbox sync indicators
    dropbox_indicators = [
        ".dropbox.cache",
        ".dropbox-unpacker",
    ]

    path_str = str(dirname)

    for indicator in onedrive_indicators + gdrive_indicators + dropbox_indicators:
        if indicator in path_str:
            return True

    # Check for files being actively synced (filename patterns)
    name_lower = p.name.lower()
    if any(suffix in name_lower for suffix in [".syncing", ".sync-pending",
               ".sync-conflict", "-conflict", " (copy)"]):
        return True

    return False


def is_size_stable(path: str) -> bool:
    """File size is not growing."""
    try:
        size1 = os.path.getsize(path)
        time.sleep(STABILITY_WAIT_SECONDS)
        size2 = os.path.getsize(path)
        return size1 == size2 and size1 > 0
    except OSError:
        return False


def is_mtime_stable(path: str) -> bool:
    """File has not been modified very recently."""
    try:
        mtime = os.path.getmtime(path)
        age = time.time() - mtime
        return age > STABILITY_WAIT_SECONDS
    except OSError:
        return False


def is_safari_downloading(path: str) -> bool:
    """Check macOS quarantine/download-in-progress flag."""
    try:
        result = subprocess.run(
            ["xattr", "-l", path],
            capture_output=True,
            text=True,
            timeout=2,
        )
        output = result.stdout
        return "kMDItemIsInProgress" in output or "com.apple.progress" in output
    except Exception:
        return False


def is_file_ready(path: str) -> bool:
    """
    Master check — returns True only if the file
    is fully written and safe to process.

    Order of checks (fast to slow):
      1. Path still exists
      2. Not a partial/temp extension
      3. No partial sibling
      4. Not an Office temp file
      5. Not a Vim/Emacs temp file
      6. Not a system cache file
      7. Not hidden
      8. Not a macOS resource fork
      9. Not being synced
      10. Not currently being Safari-downloaded
      11. Not locked by another process
      12. mtime is not brand new
      13. Size is stable (slowest — involves wait)
    """
    if not _enabled:
        return True

    try:
        if not os.path.exists(path):
            return False
        if not os.path.isfile(path):
            return False

        # Check partial extensions
        if is_partial_file(path):
            logging.debug(f"[Guard] SKIP — partial extension: {path}")
            return False

        # Check for partial sibling
        if has_partial_sibling(path):
            logging.debug(f"[Guard] SKIP — partial sibling: {path}")
            return False

        # Check Office temp files
        if is_office_temp_file(path):
            logging.debug(f"[Guard] SKIP — Office temp file: {path}")
            return False

        # Check Vim swap files
        if is_vim_swap_file(path):
            logging.debug(f"[Guard] SKIP — Vim swap file: {path}")
            return False

        # Check Emacs temp files
        if is_emacs_temp_file(path):
            logging.debug(f"[Guard] SKIP — Emacs temp file: {path}")
            return False

        # Check IDE temp files
        if is_ide_temp_file(path):
            logging.debug(f"[Guard] SKIP — IDE temp file: {path}")
            return False

        # Check system cache files
        if is_system_cache_file(path):
            logging.debug(f"[Guard] SKIP — system cache file: {path}")
            return False

        # Check hidden files
        if is_hidden_file(path):
            logging.debug(f"[Guard] SKIP — hidden file: {path}")
            return False

        # Check macOS resource forks
        if is_resource_fork(path):
            logging.debug(f"[Guard] SKIP — resource fork: {path}")
            return False

        # Check sync in progress
        if is_sync_in_progress(path):
            logging.debug(f"[Guard] SKIP — sync in progress: {path}")
            return False

        # Check Safari downloading (macOS specific)
        if is_safari_downloading(path):
            logging.debug(f"[Guard] SKIP — Safari downloading: {path}")
            return False

        # Check if file is locked
        if is_file_locked(path):
            logging.debug(f"[Guard] SKIP — file locked: {path}")
            return False

        # Check modification time stability
        if not is_mtime_stable(path):
            logging.debug(f"[Guard] SKIP — modified too recently: {path}")
            return False

        # Check size stability (slowest check)
        if not is_size_stable(path):
            logging.debug(f"[Guard] SKIP — size still growing: {path}")
            return False

        return True
    except Exception:
        return False


def wait_until_ready(
    path: str,
    max_wait: int = None,
    poll_interval: int = 5,
) -> bool:
    """
    Poll until file is ready or max_wait seconds have elapsed.
    Returns True if file became ready, False if timed out.
    """
    if not _enabled:
        return True

    if max_wait is None:
        max_wait = _timeout

    elapsed = 0
    while elapsed < max_wait:
        if is_file_ready(path):
            logging.debug(f"[Guard] READY — processing: {path}")
            return True
        logging.debug(f"[Guard] WAIT — polling file: {path}")
        time.sleep(poll_interval)
        elapsed += poll_interval

    logging.warning(f"[Guard] TIMEOUT — gave up waiting: {path}")
    return False