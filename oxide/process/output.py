"""Process output and OS utilities.

Provides ExitStatus, Output, ExitCode, and functions: args, env,
current_dir, current_exe, home_dir, temp_dir.
"""
from __future__ import annotations

import os
import sys
import tempfile
from typing import Any, Iterable

from ..fs.path import Path


class ExitCode:
    """A simple process exit code wrapper.

    Represents an integer exit code with helpers to indicate success.

    Examples:
        >>> ExitCode.success().is_success()
        True
        >>> ExitCode.from_raw(1).is_success()
        False
    """

    __slots__ = ("_code",)

    def __init__(self, code: int = 0) -> None:
        """Construct an ExitCode from a raw integer.

        Args:
            code (int, optional): The exit code value. Defaults to ``0``.
        """
        self._code = code

    @classmethod
    def success(cls) -> ExitCode:
        """Return an exit code representing success (0).

        Returns:
            ExitCode: An ExitCode with value 0.
        """
        return cls(0)

    @classmethod
    def from_raw(cls, code: int) -> ExitCode:  # type: ignore
        """Create an ExitCode from a raw integer.

        Args:
            code (int): The raw exit code value.

        Returns:
            ExitCode: The wrapped exit code.
        """
        return cls(code)

    def code(self) -> int:  # type: ignore
        """Return the raw integer exit code value.

        Returns:
            int: The exit code.
        """
        return self._code

    def is_success(self) -> bool:
        """Return whether the exit code indicates success (0).

        Returns:
            bool: True if the exit code is 0.
        """
        return self._code == 0

    def __repr__(self) -> str:
        return f"ExitCode({self._code})"


class ExitStatus:
    """Exit status of a finished process, including exit code and signal info.

    Captures the raw exit code and whether it indicates success. For
    processes killed by a signal, the code is stored as a negative signal
    number.

    Examples:
        >>> ExitStatus(0).success()
        True
        >>> bool(ExitStatus(1))
        False
    """

    __slots__ = ("_code", "_success")

    def __init__(self, code: int) -> None:
        """Construct an ExitStatus from a raw exit code.

        Args:
            code (int): The process exit code. A negative value represents
                a signal.
        """
        self._code = code
        self._success = code == 0

    def code(self) -> int:  # type: ignore
        """Return the raw exit code.

        Returns:
            int: The exit code (negative if the process was signaled).
        """
        return self._code

    def success(self) -> bool:  # type: ignore
        """Return whether the process exited successfully (code 0).

        Returns:
            bool: True if the exit code is 0.
        """
        return self._success

    def signal(self) -> int | None:  # type: ignore
        """Return the signal number if killed by a signal, or None.

        Mirrors Unix convention: positive codes are normal exits, negative
        codes correspond to the signal that terminated the process.

        Returns:
            int | None: The signal number, or None if not signaled.
        """
        if self._code < 0:
            return -self._code
        return None

    def __repr__(self) -> str:
        return f"ExitStatus(code={self._code})"

    def __bool__(self) -> bool:
        return self._success


class Output:
    """Captured stdout and stderr from a finished process.

    Combines an :class:`ExitStatus` with the raw stdout/stderr bytes, with
    helpers to decode them as UTF-8 text.

    Examples:
        >>> out = Output(ExitStatus(0), b"hi", b"")
        >>> out.stdout_str()
        'hi'
    """

    __slots__ = ("_status", "_stdout", "_stderr")

    def __init__(self, status: ExitStatus, stdout: bytes = b"", stderr: bytes = b"") -> None:
        """Construct an Output from a status and captured streams.

        Args:
            status (ExitStatus): The process exit status.
            stdout (bytes, optional): Captured stdout. Defaults to empty.
            stderr (bytes, optional): Captured stderr. Defaults to empty.
        """
        self._status = status
        self._stdout = stdout
        self._stderr = stderr

    def status(self) -> ExitStatus:  # type: ignore
        """Return the exit status of the process.

        Returns:
            ExitStatus: The process exit status.
        """
        return self._status

    def stdout(self) -> bytes:  # type: ignore
        """Return the captured stdout as raw bytes.

        Returns:
            bytes: The stdout data.
        """
        return self._stdout

    def stderr(self) -> bytes:  # type: ignore
        """Return the captured stderr as raw bytes.

        Returns:
            bytes: The stderr data.
        """
        return self._stderr

    def stdout_str(self) -> str:  # type: ignore
        """Return stdout decoded as a UTF-8 string.

        Invalid bytes are replaced rather than raising an error.

        Returns:
            str: The decoded stdout.
        """
        return self._stdout.decode("utf-8", errors="replace")

    def stderr_str(self) -> str:  # type: ignore
        """Return stderr decoded as a UTF-8 string.

        Invalid bytes are replaced rather than raising an error.

        Returns:
            str: The decoded stderr.
        """
        return self._stderr.decode("utf-8", errors="replace")

    def __repr__(self) -> str:
        return f"Output(status={self._status})"


def args() -> list[str]:  # type: ignore
    """Return the command-line arguments, excluding the script name.

    Returns:
        list[str]: The arguments passed after the program name.
    """
    return sys.argv[1:]


def env(key: str, default: str | None = None) -> str | None:  # type: ignore
    """Return an environment variable value, or a default if unset.

    Args:
        key (str): The environment variable name.
        default (str | None, optional): Value to return if the variable is
            not set. Defaults to None.

    Returns:
        str | None: The variable's value, or the default.
    """
    return os.environ.get(key, default)


def current_dir() -> Path:  # type: ignore
    """Return the current working directory.

    Returns:
        Path: The current working directory as a Path.
    """
    return Path(os.getcwd())


def current_exe() -> Path:  # type: ignore
    """Return the absolute path of the currently running executable.

    Returns:
        Path: The resolved absolute path of the current executable.
    """
    return Path(os.path.realpath(sys.argv[0]))


def home_dir() -> Path | None:  # type: ignore
    """Return the user's home directory, or None if unavailable.

    Returns:
        Path | None: The home directory, or None if it could not be
            determined.
    """
    home = os.path.expanduser("~")
    if home:
        return Path(home)
    return None


def temp_dir() -> Path:  # type: ignore
    """Return the system's temporary directory.

    Returns:
        Path: The temporary directory path.
    """
    return Path(tempfile.gettempdir())
