"""Process management — spawning and controlling processes.

Provides Command, Child, Stdio, ExitStatus, Output, ExitCode,
and OS utility functions.
"""
from __future__ import annotations

from .command import Command
from .child import Child, Stdio
from .output import ExitStatus, Output, ExitCode, args, env, current_dir, current_exe, home_dir, temp_dir

__all__ = [
    "Command",
    "Child",
    "Stdio",
    "ExitStatus",
    "Output",
    "ExitCode",
    "args",
    "env",
    "current_dir",
    "current_exe",
    "home_dir",
    "temp_dir",
]
