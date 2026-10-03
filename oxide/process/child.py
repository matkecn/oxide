"""Child and Stdio — running process handles and stream config.

Provides Child for managing running processes and Stdio for
configuring process standard streams.
"""
from __future__ import annotations

from typing import Any

from .output import ExitStatus, Output
from ..fs.path import Path


class Stdio:
    """Configuration for a process's standard I/O stream.

    Describes how a child's stdin, stdout, or stderr should be wired:
    inherited, piped, sent to null, or redirected to a file. Build one with
    the class methods :meth:`inherit`, :meth:`piped`, :meth:`null`, or
    :meth:`from_path`.

    Examples:
        >>> Stdio.piped().kind()
        1
        >>> Stdio.from_path("log.txt").kind()
        3
    """

    __slots__ = ("_kind", "_file")

    INHERIT = 0
    PIPED = 1
    NULL = 2
    FILE = 3

    def __init__(self, kind: int = INHERIT, file: str | None = None) -> None:
        """Construct a Stdio configuration directly.

        Prefer the class methods (:meth:`inherit`, :meth:`piped`,
        :meth:`null`, :meth:`from_path`) for the common cases.

        Args:
            kind (int, optional): One of the ``INHERIT``, ``PIPED``,
                ``NULL``, or ``FILE`` constants. Defaults to ``INHERIT``.
            file (str | None, optional): File path used when ``kind`` is
                ``FILE``. Defaults to None.
        """
        self._kind = kind
        self._file = file

    @classmethod
    def inherit(cls) -> Stdio:
        """Create configuration to inherit the stream from the parent process.

        Returns:
            Stdio: An inherit configuration.
        """
        return cls(cls.INHERIT)

    @classmethod
    def piped(cls) -> Stdio:
        """Create configuration that creates a new pipe for the stream.

        The child's stream is connected to a pipe so the parent can write
        to (stdin) or read from (stdout/stderr) it.

        Returns:
            Stdio: A piped configuration.
        """
        return cls(cls.PIPED)

    @classmethod
    def null(cls) -> Stdio:
        """Create configuration that discards all stream data.

        The stream is connected to the null device; any output is thrown
        away.

        Returns:
            Stdio: A null configuration.
        """
        return cls(cls.NULL)

    @classmethod
    def from_path(cls, path: str | Path) -> Stdio:  # type: ignore
        """Create configuration that redirects the stream to or from a file.

        Args:
            path (str | Path): The file path to read from (stdin) or write
                to (stdout/stderr).

        Returns:
            Stdio: A file-redirect configuration.
        """
        path_str = path.as_str() if isinstance(path, Path) else str(path)
        return cls(cls.FILE, path_str)

    def kind(self) -> int:
        """Return the raw integer constant backing this configuration.

        Returns:
            int: One of `Stdio.INHERIT`, `Stdio.PIPED`, `Stdio.NULL`, or
                `Stdio.FILE`.
        """
        return self._kind

    def __repr__(self) -> str:
        if self._kind == self.INHERIT:
            return "Stdio::Inherit"
        if self._kind == self.PIPED:
            return "Stdio::Piped"
        if self._kind == self.NULL:
            return "Stdio::Null"
        return f"Stdio::File({self._file!r})"


class Child:
    """Handle to a running child process.

    Obtained from :meth:`Command.spawn`. Provides the process ID, waiting
    and polling for exit, killing, and access to piped standard streams.

    Examples:
        >>> from .command import Command
        >>> child = Command("echo").spawn()
        >>> child.wait()
        ExitStatus(code=0)
    """

    __slots__ = ("_process", "_pid")

    def __init__(self, process: Any) -> None:
        self._process = process
        self._pid = process.pid

    def id(self) -> int:  # type: ignore
        """Return the process ID.

        Returns:
            int: The OS process ID.
        """
        return self._pid

    def kill(self) -> None:  # type: ignore
        """Forcefully terminate the process.

        Sends the terminate/kill signal to the child process.
        """
        self._process.kill()

    def wait(self) -> ExitStatus:  # type: ignore
        """Wait for the process to exit and return its exit status.

        Blocks until the child terminates.

        Returns:
            ExitStatus: The exit status of the process.
        """
        code = self._process.wait()
        return ExitStatus(code)

    def wait_with_output(self) -> Output:  # type: ignore
        """Wait for the process and return its captured output.

        Communicates with the child to collect its stdout and stderr, then
        waits for it to exit.

        Returns:
            Output: The exit status and captured stdout/stderr.
        """
        stdout, stderr = self._process.communicate()
        return Output(
            ExitStatus(self._process.returncode),
            stdout or b"",
            stderr or b"",
        )

    def try_wait(self) -> ExitStatus | None:  # type: ignore
        """Poll for the exit status without blocking.

        Returns:
            ExitStatus | None: The exit status if the process has exited,
                or None if it is still running.
        """
        ret = self._process.poll()
        if ret is None:
            return None
        return ExitStatus(ret)

    def take_stdin(self) -> Any:  # type: ignore
        """Return the child's stdin pipe.

        Only valid if configured with `Stdio.piped()`.

        Returns:
            Any: The stdin pipe file object for the parent to write to.
        """
        return self._process.stdin

    def take_stdout(self) -> Any:  # type: ignore
        """Return the child's stdout pipe.

        Only valid if configured with `Stdio.piped()`.

        Returns:
            Any: The stdout pipe file object for the parent to read from.
        """
        return self._process.stdout

    def take_stderr(self) -> Any:  # type: ignore
        """Return the child's stderr pipe.

        Only valid if configured with `Stdio.piped()`.

        Returns:
            Any: The stderr pipe file object for the parent to read from.
        """
        return self._process.stderr

    def wait_timeout(self, secs: float) -> ExitStatus | None:  # type: ignore
        """Wait up to a number of seconds for the process to exit.

        Args:
            secs (float): Maximum seconds to wait.

        Returns:
            ExitStatus | None: The exit status if the process exited within
                the timeout, or None if it is still running.
        """
        ret = self._process.poll()
        if ret is not None:
            return ExitStatus(ret)
        try:
            self._process.wait(timeout=secs)
            return ExitStatus(self._process.returncode)
        except Exception:
            return None

    def __repr__(self) -> str:
        return f"Child(pid={self._pid})"
