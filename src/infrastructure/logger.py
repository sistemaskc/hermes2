import datetime
import json
import logging
import logging.handlers
import os
import platform
import socket
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from colorama import Fore, Style, init

init(autoreset=True)

LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}


class LogHandler(ABC):
    @abstractmethod
    def log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None: ...

    def close(self) -> None:
        pass


class ConsoleLogHandler(LogHandler):
    _COLORS = {
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "DEBUG": Fore.CYAN,
    }

    def __init__(self, include_metadata: bool = False):
        self.include_metadata = include_metadata

    def log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = self._COLORS.get(level, "")
        line = f"{color}[{timestamp}] - [{level}] - [{method}] - {message}{Style.RESET_ALL}"

        if self.include_metadata and metadata:
            meta_str = " | ".join(f"{k}={v}" for k, v in metadata.items())
            line += f" {Fore.BLACK}{Style.BRIGHT}| {meta_str}{Style.RESET_ALL}"

        try:
            print(line)
        except UnicodeEncodeError:
            safe = line.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
                sys.stdout.encoding or "utf-8"
            )
            print(safe)


class RotatingFileLogHandler(LogHandler):
    def __init__(
        self,
        filename: str,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 5,
        include_metadata: bool = True,
    ):
        self.include_metadata = include_metadata
        log_dir = os.path.dirname(filename)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        self._internal = logging.getLogger(f"RPA_FILE_{filename}")
        self._internal.setLevel(logging.DEBUG)
        self._internal.propagate = False

        if not self._internal.handlers:
            handler = logging.handlers.RotatingFileHandler(
                filename, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._internal.addHandler(handler)

    def log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] - [{level}] - [{method}] - {message}"

        if self.include_metadata and metadata:
            meta_str = " | ".join(f"{k}={v}" for k, v in metadata.items())
            line += f" | {meta_str}"

        getattr(self._internal, level.lower(), self._internal.info)(line)

    def close(self) -> None:
        for h in self._internal.handlers:
            h.close()


class JsonLogHandler(LogHandler):
    def __init__(self, filename: str, max_bytes: int = 5 * 1024 * 1024, backup_count: int = 5):
        log_dir = os.path.dirname(filename)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        self._internal = logging.getLogger(f"RPA_JSON_{filename}")
        self._internal.setLevel(logging.DEBUG)
        self._internal.propagate = False

        if not self._internal.handlers:
            handler = logging.handlers.RotatingFileHandler(
                filename, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._internal.addHandler(handler)

    def log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": level,
            "method": method,
            "message": message,
            "metadata": metadata or {},
        }
        self._internal.info(json.dumps(entry, ensure_ascii=False))

    def close(self) -> None:
        for h in self._internal.handlers:
            h.close()


class Logger:
    @staticmethod
    def get_session_name(base_name: str, extension: str) -> str:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()
        return f"{base_name}_{timestamp}_{pid}.{extension}"

    def __init__(self, handlers: Optional[List[LogHandler]] = None, min_level: str = "INFO"):
        self._handlers: List[LogHandler] = handlers if handlers is not None else [ConsoleLogHandler()]
        self._metadata: Dict = self._get_metadata()
        self._min_level = LEVELS.get(min_level.upper(), 1)

    def _get_metadata(self) -> Dict:
        return {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "python_version": platform.python_version(),
            "user": os.getlogin(),
        }

    def _log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        if LEVELS.get(level, 0) < self._min_level:
            return

        combined = {**self._metadata}
        if metadata:
            combined.update(metadata)

        for handler in self._handlers:
            try:
                handler.log(level, method, message, combined)
            except Exception as e:
                print(f"[Logger] Error en handler {handler.__class__.__name__}: {e}")

    def debug(self, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        self._log("DEBUG", method, message, metadata)

    def info(self, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        self._log("INFO", method, message, metadata)

    def warning(self, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        self._log("WARNING", method, message, metadata)

    def error(self, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        self._log("ERROR", method, message, metadata)

    def close(self) -> None:
        for handler in self._handlers:
            try:
                handler.close()
            except Exception as e:
                print(f"[Logger] Error al cerrar handler {handler.__class__.__name__}: {e}")


def _crear_logger() -> Logger:
    from src.config import settings

    settings.log_dir.mkdir(parents=True, exist_ok=True)

    handlers = [
        ConsoleLogHandler(include_metadata=False),
        RotatingFileLogHandler(str(settings.log_dir / Logger.get_session_name("rpa_consultador", "log"))),
        JsonLogHandler(str(settings.log_dir / Logger.get_session_name("rpa_consultador", "jsonl"))),
    ]
    return Logger(handlers=handlers, min_level=settings.log_level)


logger = _crear_logger()
