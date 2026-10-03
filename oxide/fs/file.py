"""File and OpenOptions — file I/O with configurable open modes."""
from __future__ import annotations

"""File and OpenOptions — file I/O.

Provides File for reading/writing files and OpenOptions for
configurable file opening with read, write, append, create modes.
"""

import os
from typing import Any

from .path import Path
from .metadata import Metadata, Permissions, metadata_from_os


class OpenOptions:
    """Builder for configuring file open modes with a fluent interface."""

    __slots__ = ("_read", "_write", "_append", "_truncate", "_create", "_create_new")

    def __init__(self) -> None:
        """Create a new OpenOptions with all flags disabled."""
        self._read = False
        self._write = False
        self._append = False
        self._truncate = False
        self._create = False
        self._create_new = False

    @classmethod
    def new(cls) -> OpenOptions:  # type: ignore
        """Create a new OpenOptions with all flags disabled.

        Returns:
            A new OpenOptions instance.
        """
        return cls()

    def read(self, enable: bool = True) -> OpenOptions:
        """Enable or disable read mode.

        Args:
            enable: True to enable reading, False to disable. Defaults to True.

        Returns:
            This OpenOptions instance for chaining.
        """
        self._read = enable
        return self

    def write(self, enable: bool = True) -> OpenOptions:
        """Enable or disable write mode.

        Args:
            enable: True to enable writing, False to disable. Defaults to True.

        Returns:
            This OpenOptions instance for chaining.
        """
        self._write = enable
        return self

    def append(self, enable: bool = True) -> OpenOptions:
        """Enable or disable append mode.

        Args:
            enable: True to enable appending, False to disable. Defaults to True.

        Returns:
            This OpenOptions instance for chaining.
        """
        self._append = enable
        return self

    def truncate(self, enable: bool = True) -> OpenOptions:
        """Enable or disable truncation on open.

        Args:
            enable: True to enable truncation, False to disable. Defaults to True.

        Returns:
            This OpenOptions instance for chaining.
        """
        self._truncate = enable
        return self

    def create(self, enable: bool = True) -> OpenOptions:
        """Enable or disable file creation if it does not exist.

        Args:
            enable: True to enable creation, False to disable. Defaults to True.

        Returns:
            This OpenOptions instance for chaining.
        """
        self._create = enable
        return self

    def create_new(self, enable: bool = True) -> OpenOptions:
        """Enable or disable requiring a new file (fails if file exists).

        Args:
            enable: True to require a new file, False to disable. Defaults to True.

        Returns:
            This OpenOptions instance for chaining.
        """
        self._create_new = enable
        return self

    def open(self, path: str | Path) -> File:
        """Open a file with the configured options.

        Args:
            path: The path to the file to open.

        Returns:
            A File instance for the opened file.

        Raises:
            FileExistsError: If create_new is set and the file already exists.
            FileNotFoundError: If write mode is used without create and file does not exist.
        """
        path_str = path.as_str() if isinstance(path, Path) else str(path)

        if self._create_new and os.path.exists(path_str):
            raise FileExistsError(f"file already exists: {path_str}")

        mode = 'r'
        if self._create_new or (self._create and self._write):
            mode = 'w'
        elif self._write and self._append:
            mode = 'a'
        elif self._write:
            mode = 'w'
        elif self._read and self._write:
            mode = 'r+'
        elif self._read:
            mode = 'r'

        if self._truncate and mode in ('r+', 'w', 'a'):
            if mode == 'r+':
                mode = 'w'
            elif mode == 'a':
                mode = 'w'

        if 'w' in mode and not self._create and not os.path.exists(path_str):
            if not self._create:
                raise FileNotFoundError(f"no such file or directory: {path_str}")

        f = open(path_str, mode)  # type: ignore[arg-type]
        return File(f, path_str)

    def __repr__(self) -> str:  # type: ignore
        flags = []
        if self._read:
            flags.append("read")
        if self._write:
            flags.append("write")
        if self._append:
            flags.append("append")
        if self._truncate:
            flags.append("truncate")
        if self._create:
            flags.append("create")
        if self._create_new:
            flags.append("create_new")
        return f"OpenOptions({', '.join(flags)})"


class File:
    """File handle supporting read, write, seek, and metadata operations."""

    __slots__ = ("_handle", "_path", "_closed")

    def __init__(self, handle: Any, path: str = "") -> None:
        """Create a File from an open file handle.

        Args:
            handle: The underlying file handle.
            path: The filesystem path of the file. Defaults to empty string.
        """
        self._handle = handle
        self._path = path
        self._closed = False

    @classmethod
    def create(cls, path: str | Path) -> File:  # type: ignore
        """Create a new file or truncate an existing one for writing.

        Args:
            path: The path to the file to create.

        Returns:
            A new File instance opened for writing.
        """
        path_str = path.as_str() if isinstance(path, Path) else str(path)
        return cls(open(path_str, 'w'), path_str)

    @classmethod
    def create_new(cls, path: str | Path) -> File:  # type: ignore
        """Create a new file, raising an error if it already exists.

        Args:
            path: The path to the file to create.

        Returns:
            A new File instance opened for writing.

        Raises:
            FileExistsError: If the file already exists.
        """
        path_str = path.as_str() if isinstance(path, Path) else str(path)
        if os.path.exists(path_str):
            raise FileExistsError(f"file already exists: {path_str}")
        return cls(open(path_str, 'w'), path_str)

    @classmethod
    def open(cls, path: str | Path) -> File:  # type: ignore
        """Open an existing file for reading.

        Args:
            path: The path to the file to open.

        Returns:
            A new File instance opened for reading.
        """
        path_str = path.as_str() if isinstance(path, Path) else str(path)
        return cls(open(path_str, 'r'), path_str)

    @classmethod
    def options(cls) -> OpenOptions:  # type: ignore
        """Return a new OpenOptions builder for configuring file open modes.

        Returns:
            A new OpenOptions instance.
        """
        return OpenOptions()

    def read(self) -> bytes:  # type: ignore
        """Read all remaining bytes from the file.

        Returns:
            The file content as bytes.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        return self._handle.read()  # type: ignore

    def read_exact(self, buf: bytearray) -> int:  # type: ignore
        """Read exactly len(buf) bytes into the buffer.

        Args:
            buf: The buffer to fill with bytes.

        Returns:
            The number of bytes read.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        data = self._handle.read(len(buf))  # type: ignore
        n = len(data)
        buf[:n] = data
        return n

    def read_to_string(self) -> str:  # type: ignore
        """Read all remaining bytes and return as a string.

        Returns:
            The file content as a string.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        return self._handle.read()  # type: ignore

    def write(self, data: bytes | str) -> int:  # type: ignore
        """Write data to the file.

        Args:
            data: The bytes or string to write.

        Returns:
            The number of bytes written.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        return self._handle.write(data)  # type: ignore

    def write_all(self, data: bytes | str) -> None:  # type: ignore
        """Write all data to the file.

        Args:
            data: The bytes or string to write completely.
        """
        self.write(data)

    def flush(self) -> None:  # type: ignore
        """Flush buffered data to the underlying file.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        self._handle.flush()  # type: ignore

    def sync_all(self) -> None:  # type: ignore
        """Flush data and ensure it is written to the underlying storage."""
        self.flush()

    def sync_data(self) -> None:  # type: ignore
        """Flush data to ensure file metadata is written to storage."""
        self.flush()

    def seek(self, pos: int) -> int:  # type: ignore
        """Seek to the given byte position in the file.

        Args:
            pos: The byte position to seek to.

        Returns:
            The new file position.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        return self._handle.seek(pos)  # type: ignore

    def seek_from_start(self, offset: int) -> int:  # type: ignore
        """Seek to an absolute byte position from the start of the file.

        Args:
            offset: The byte offset from the start.

        Returns:
            The new file position.
        """
        return self.seek(offset)

    def seek_from_current(self, offset: int) -> int:  # type: ignore
        """Seek to a relative byte position from the current position.

        Args:
            offset: The byte offset from the current position.

        Returns:
            The new file position.
        """
        return self.seek(offset)

    def seek_from_end(self, offset: int) -> int:  # type: ignore
        """Seek to a relative byte position from the end of the file.

        Args:
            offset: The byte offset from the end.

        Returns:
            The new file position.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        return self._handle.seek(offset, 2)  # type: ignore

    def stream_position(self) -> int:  # type: ignore
        """Return the current file position.

        Returns:
            The current byte position in the file.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        return self._handle.tell()  # type: ignore

    def set_len(self, size: int) -> None:  # type: ignore
        """Truncate the file to the specified size.

        Args:
            size: The new file size in bytes.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        self._handle.truncate(size)  # type: ignore

    def metadata(self) -> Metadata:  # type: ignore
        """Return metadata about this file.

        Returns:
            A Metadata object containing file type, size, permissions, and timestamps.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        return metadata_from_os(self._path)

    def set_permissions(self, perm: Permissions) -> None:  # type: ignore
        """Set the file permissions.

        Args:
            perm: The new permissions to apply.
        """
        os.chmod(self._path, 0o444 if perm.readonly() else 0o644)

    def path(self) -> Path:  # type: ignore
        """Return the path of this file.

        Returns:
            A Path representing the file's location.
        """
        return Path(self._path)

    def into_inner(self) -> Any:  # type: ignore
        """Consume this File and return the underlying handle, closing the file.

        Returns:
            The underlying file handle.
        """
        self._closed = True
        return self._handle

    def try_clone(self) -> File:  # type: ignore
        """Clone this file handle by opening the same path again.

        Returns:
            A new File pointing to the same path.

        Raises:
            ValueError: If the file is closed.
        """
        if self._closed:
            raise ValueError("file is closed")
        import io
        new_handle = open(self._path, self._handle.mode)  # type: ignore
        return File(new_handle, self._path)

    def __enter__(self) -> File:  # type: ignore
        """Enter the context manager.

        Returns:
            This File instance.
        """
        return self

    def __exit__(self, *_: Any) -> None:  # type: ignore
        """Exit the context manager, closing the file."""
        self.close()

    def close(self) -> None:  # type: ignore
        """Close the file handle if not already closed."""
        if not self._closed:
            self._handle.close()  # type: ignore
            self._closed = True

    def is_closed(self) -> bool:  # type: ignore
        """Check if this file has been closed.

        Returns:
            True if the file is closed, False otherwise.
        """
        return self._closed

    def __repr__(self) -> str:
        return f"File({self._path!r}, closed={self._closed})"
