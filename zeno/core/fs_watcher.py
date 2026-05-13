import logging
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = None


# Only define ZenoFileEventHandler if watchdog is available
if WATCHDOG_AVAILABLE:
    class ZenoFileEventHandler(FileSystemEventHandler):
        def __init__(self, callback):
            super().__init__()
            self._callback = callback
            self._pending = set()
            self._lock = threading.Lock()

        def on_created(self, event):
            if not event.is_directory:
                self._schedule(event.src_path)

        def on_modified(self, event):
            if not event.is_directory:
                self._schedule(event.src_path)

        def on_moved(self, event):
            if not event.is_directory:
                self._schedule(event.dest_path)

        def _schedule(self, path: str):
            with self._lock:
                if path not in self._pending:
                    self._pending.add(path)
                    t = threading.Timer(3.0, self._process, args=[path])
                    t.daemon = True
                    t.start()

        def _process(self, path: str):
            with self._lock:
                self._pending.discard(path)
            logging.debug(f"[Watcher] DETECTED — new file: {path}")
            self._callback(path)


class FSWatcher(QObject):
    file_detected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._observer = None
        self._watched_paths = set()
        self._enabled = True

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if not enabled and self._observer:
            self.stop()

    def watch(self, path: str, recursive: bool):
        if not self._enabled:
            return

        if not WATCHDOG_AVAILABLE:
            logging.warning("watchdog not installed, file watching disabled")
            return

        if path not in self._watched_paths:
            if self._observer is None:
                self._observer = Observer()

            try:
                handler = ZenoFileEventHandler(self.file_detected.emit)
                self._observer.schedule(handler, path, recursive=recursive)
                self._watched_paths.add(path)
            except Exception as e:
                logging.error(f"Failed to watch path {path}: {e}")

    def start(self):
        if not self._enabled:
            return

        if not WATCHDOG_AVAILABLE:
            return

        if self._observer and not self._observer.is_alive():
            try:
                self._observer.start()
            except Exception as e:
                logging.error(f"Failed to start observer: {e}")

    def stop(self):
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def update_watched_paths(self, paths: list[tuple[str, bool]]):
        if not self._enabled:
            return

        if not WATCHDOG_AVAILABLE:
            return

        self.stop()
        self._watched_paths = set()

        for path, recursive in paths:
            if Path(path).is_dir():
                self.watch(path, recursive)

        self.start()

    def is_available(self) -> bool:
        return WATCHDOG_AVAILABLE