"""Command — process spawning builder.

Provides Command for configuring and spawning child processes
with arg, env, current_dir, stdin/stdout/stderr, spawn, output.
"""
from __future__ import annotations

import subprocess
from typing import Any, Iterable

from .child import Child, Stdio
from .output import ExitStatus, Output
from ..fs.path import Path


class Command:
    """Builder for configuring and spawning a child process.

    Configure the program, arguments, environment, working directory, and
    standard streams, then either :meth:`spawn` for a live handle,
    :meth:`output` to capture results, or :meth:`status` for the exit code.

    Examples:
        >>> result = (Command("echo").arg("hello")).output()
        >>> result.stdout_str().strip()
        'hello'
    """

    __slots__ = ("_program", "_args", "_env", "_cwd", "_stdin", "_stdout", "_stderr")

    def __init__(self, program: str | Path) -> None:
        program_str = program.as_str() if isinstance(program, Path) else str(program)
        self._program = program_str
        self._args: list[str] = []
        self._env: dict[str, str] | None = None
        self._cwd: str | None = None
        self._stdin: Stdio = Stdio.inherit()
        self._stdout: Stdio = Stdio.inherit()
        self._stderr: Stdio = Stdio.inherit()

    def arg(self, arg: str) -> Command:  # type: ignore
        """Append a single argument to the command line.

        Args:
            arg (str): The argument to append.

        Returns:
            Command: Self, to allow method chaining.
        """
        self._args.append(str(arg))
        return self

    def args(self, args: Iterable[str]) -> Command:  # type: ignore
        """Append multiple arguments to the command line.

        Args:
            args (Iterable[str]): An iterable of arguments to append.

        Returns:
            Command: Self, to allow method chaining.
        """
        for a in args:
            self._args.append(str(a))
        return self

    def env(self, key: str, val: str) -> Command:  # type: ignore
        """Set a single environment variable for the child.

        Args:
            key (str): The environment variable name.
            val (str): The environment variable value.

        Returns:
            Command: Self, to allow method chaining.
        """
        if self._env is None:
            self._env = {}
        self._env[key] = val
        return self

    def envs(self, envs: dict[str, str]) -> Command:  # type: ignore
        """Set multiple environment variables for the child at once.

        Args:
            envs (dict[str, str]): A mapping of variable names to values.

        Returns:
            Command: Self, to allow method chaining.
        """
        if self._env is None:
            self._env = {}
        self._env.update(envs)
        return self

    def current_dir(self, dir: str | Path) -> Command:  # type: ignore
        """Set the working directory for the child process.

        Args:
            dir (str | Path): The directory to run the child in.

        Returns:
            Command: Self, to allow method chaining.
        """
        self._cwd = dir.as_str() if isinstance(dir, Path) else str(dir)
        return self

    def stdin(self, cfg: Stdio) -> Command:  # type: ignore
        """Configure the child's stdin stream.

        Args:
            cfg (Stdio): The stream configuration, e.g. `Stdio.piped()`.

        Returns:
            Command: Self, to allow method chaining.
        """
        self._stdin = cfg
        return self

    def stdout(self, cfg: Stdio) -> Command:  # type: ignore
        """Configure the child's stdout stream.

        Args:
            cfg (Stdio): The stream configuration, e.g. `Stdio.piped()`.

        Returns:
            Command: Self, to allow method chaining.
        """
        self._stdout = cfg
        return self

    def stderr(self, cfg: Stdio) -> Command:  # type: ignore
        """Configure the child's stderr stream.

        Args:
            cfg (Stdio): The stream configuration, e.g. `Stdio.piped()`.

        Returns:
            Command: Self, to allow method chaining.
        """
        self._stderr = cfg
        return self

    def spawn(self) -> Child:  # type: ignore
        """Spawn the process and return a live Child handle.

        The configured stdin/stdout/stderr determine whether the returned
        :class:`Child` exposes pipes for the relevant streams.

        Returns:
            Child: A handle to the running child process.
        """
        stdin_cfg = None
        stdout_cfg = None
        stderr_cfg = None

        if self._stdin._kind == Stdio.PIPED:
            stdin_cfg = subprocess.PIPE
        elif self._stdin._kind == Stdio.NULL:
            stdin_cfg = subprocess.DEVNULL

        if self._stdout._kind == Stdio.PIPED:
            stdout_cfg = subprocess.PIPE
        elif self._stdout._kind == Stdio.NULL:
            stdout_cfg = subprocess.DEVNULL

        if self._stderr._kind == Stdio.PIPED:
            stderr_cfg = subprocess.PIPE
        elif self._stderr._kind == Stdio.NULL:
            stderr_cfg = subprocess.DEVNULL

        proc = subprocess.Popen(
            [self._program] + self._args,
            stdin=stdin_cfg,
            stdout=stdout_cfg,
            stderr=stderr_cfg,
            env=self._env,
            cwd=self._cwd,
        )
        return Child(proc)

    def output(self) -> Output:  # type: ignore
        """Run the process to completion and capture stdout and stderr.

        Returns:
            Output: The exit status and captured stdout/stderr bytes.
        """
        env = self._env
        proc = subprocess.run(
            [self._program] + self._args,
            capture_output=True,
            env=env,
            cwd=self._cwd,
        )
        return Output(
            ExitStatus(proc.returncode),
            proc.stdout,
            proc.stderr,
        )

    def status(self) -> ExitStatus:  # type: ignore
        """Run the process to completion and return only its exit status.

        Returns:
            ExitStatus: The exit status of the process.
        """
        proc = subprocess.run(
            [self._program] + self._args,
            capture_output=False,
            env=self._env,
            cwd=self._cwd,
        )
        return ExitStatus(proc.returncode)

    def get_program(self) -> str:  # type: ignore
        """Return the program (executable) name.

        Returns:
            str: The configured program name.
        """
        return self._program

    def get_args(self) -> list[str]:  # type: ignore
        """Return a copy of the configured arguments list.

        Returns:
            list[str]: A copy of the arguments.
        """
        return self._args.copy()

    def __repr__(self) -> str:
        return f"Command({self._program!r})"
