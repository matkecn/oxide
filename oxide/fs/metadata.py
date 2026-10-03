"""Metadata, Permissions, FileType, DirEntry, ReadDir — filesystem info."""
from __future__ import annotations

"""File metadata — type, permissions, and directory entries.

Provides Metadata, Permissions, FileType, DirEntry, and ReadDir
for querying filesystem information.
"""

import os
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from .path import Path


class FileType:
    """Represents the type of a filesystem entry (file, directory, or symlink)."""

    __slots__ = ("_is_file", "_is_dir", "_is_symlink")

    def __init__(self, is_file: bool = False, is_dir: bool = False, is_symlink: bool = False) -> None:
        """Create a FileType with the specified flags.

        Args:
            is_file: True if this is a regular file.
            is_dir: True if this is a directory.
            is_symlink: True if this is a symbolic link.
        """
        self._is_file = is_file
        self._is_dir = is_dir
        self._is_symlink = is_symlink

    def is_file(self) -> bool:
        """Check if this is a regular file.

        Returns:
            True if this represents a file, False otherwise.
        """
        return self._is_file

    def is_dir(self) -> bool:
        """Check if this is a directory.

        Returns:
            True if this represents a directory, False otherwise.
        """
        return self._is_dir

    def is_symlink(self) -> bool:
        """Check if this is a symbolic link.

        Returns:
            True if this represents a symlink, False otherwise.
        """
        return self._is_symlink

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FileType):
            return (self._is_file, self._is_dir, self._is_symlink) == (other._is_file, other._is_dir, other._is_symlink)
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._is_file, self._is_dir, self._is_symlink))

    def __repr__(self) -> str:
        if self._is_file:
            return "FileType::File"
        if self._is_dir:
            return "FileType::Dir"
        if self._is_symlink:
            return "FileType::Symlink"
        return "FileType::Unknown"


class Permissions:
    """Represents file system permissions, tracking read-only status."""

    __slots__ = ("_readonly",)

    def __init__(self, readonly: bool = False) -> None:
        """Create Permissions with the specified read-only flag.

        Args:
            readonly: True if the file is read-only, False otherwise.
        """
        self._readonly = readonly

    def readonly(self) -> bool:
        """Check if the file is read-only.

        Returns:
            True if read-only, False otherwise.
        """
        return self._readonly

    def set_readonly(self, readonly: bool) -> None:  # type: ignore
        """Set the read-only flag.

        Args:
            readonly: True to make read-only, False to allow writing.
        """
        self._readonly = readonly

    def mode(self) -> int:
        """Return the Unix permission mode bits.

        Returns:
            0o444 if read-only, 0o644 otherwise.
        """
        if self._readonly:
            return 0o444
        return 0o644

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Permissions):
            return self._readonly == other._readonly
        return NotImplemented

    def __repr__(self) -> str:
        return f"Permissions(readonly={self._readonly})"


class Metadata:
    """Filesystem metadata including type, size, permissions, and timestamps."""

    __slots__ = ("_file_type", "_permissions", "_size", "_modified", "_accessed", "_created", "_is_symlink")

    def __init__(self) -> None:
        """Create a default Metadata with no data."""
        self._file_type = FileType()
        self._permissions = Permissions()
        self._size = 0
        self._modified: float | None = None
        self._accessed: float | None = None
        self._created: float | None = None
        self._is_symlink = False

    def file_type(self) -> FileType:
        """Return the file type (file, directory, or symlink).

        Returns:
            The FileType of this entry.
        """
        return self._file_type

    def is_dir(self) -> bool:
        """Check if this is a directory.

        Returns:
            True if this is a directory, False otherwise.
        """
        return self._file_type.is_dir()

    def is_file(self) -> bool:
        """Check if this is a regular file.

        Returns:
            True if this is a regular file, False otherwise.
        """
        return self._file_type.is_file()

    def is_symlink(self) -> bool:
        """Check if this is a symbolic link.

        Returns:
            True if this is a symlink, False otherwise.
        """
        return self._is_symlink

    def len(self) -> int:  # type: ignore
        """Return the file size in bytes.

        Returns:
            The size of the file in bytes.
        """
        return self._size

    def size(self) -> int:
        """Return the file size in bytes.

        Returns:
            The size of the file in bytes.
        """
        return self._size

    def permissions(self) -> Permissions:
        """Return the file permissions.

        Returns:
            A Permissions object describing access rights.
        """
        return self._permissions

    def modified(self) -> SystemTime | None:
        """Return the last modification time, if available.

        Returns:
            A SystemTime of the last modification, or None if unknown.
        """
        if self._modified is None:
            return None
        from .._time.system_time import SystemTime
        t = SystemTime.__new__(SystemTime)
        t._seconds = int(self._modified)
        t._nanos = int((self._modified % 1) * 1_000_000_000)
        t._tz = None
        return t

    def accessed(self) -> SystemTime | None:
        """Return the last access time, if available.

        Returns:
            A SystemTime of the last access, or None if unknown.
        """
        if self._accessed is None:
            return None
        from .._time.system_time import SystemTime
        t = SystemTime.__new__(SystemTime)
        t._seconds = int(self._accessed)
        t._nanos = int((self._accessed % 1) * 1_000_000_000)
        t._tz = None
        return t

    def created(self) -> SystemTime | None:
        """Return the creation time, if available.

        Returns:
            A SystemTime of the creation, or None if unknown.
        """
        if self._created is None:
            return None
        from .._time.system_time import SystemTime
        t = SystemTime.__new__(SystemTime)
        t._seconds = int(self._created)
        t._nanos = int((self._created % 1) * 1_000_000_000)
        t._tz = None
        return t

    def __repr__(self) -> str:
        return f"Metadata(type={self._file_type}, size={self._size})"


class DirEntry:
    """A single entry from a directory listing, providing path and metadata access."""

    __slots__ = ("_path", "_metadata", "_name")

    def __init__(self, path: str | os.PathLike) -> None:
        """Create a DirEntry from a filesystem path.

        Args:
            path: The path to the directory entry.
        """
        self._path = os.fspath(path)
        self._name = os.path.basename(self._path)
        self._metadata: Metadata | None = None

    def path(self):
        """Return the full path to this directory entry.

        Returns:
            A Path representing this entry's location.
        """
        from .path import Path
        return Path(self._path)

    def file_name(self) -> str:
        """Return the file or directory name.

        Returns:
            The name of this entry.
        """
        return self._name

    def metadata(self) -> Metadata:
        """Return the metadata for this entry, caching the result.

        Returns:
            A Metadata object with file type, size, and timestamps.
        """
        if self._metadata is None:
            self._metadata = metadata_from_os(self._path)
        return self._metadata

    def file_type(self) -> FileType:
        """Return the file type of this entry.

        Returns:
            The FileType (file, directory, or symlink).
        """
        return self.metadata().file_type()

    def into_path(self):  # type: ignore
        """Consume this DirEntry and return its path.

        Returns:
            A Path representing this entry's location.
        """
        from .path import Path
        return Path(self._path)

    def __repr__(self) -> str:
        return f"DirEntry({self._name!r})"


class ReadDir:
    """An iterator over directory entries, lazily loading from the filesystem."""

    __slots__ = ("_path", "_entries")

    def __init__(self, path: str | os.PathLike) -> None:
        """Create a ReadDir for the specified directory path.

        Args:
            path: The directory path to read entries from.
        """
        self._path = os.fspath(path)
        self._entries: list[DirEntry] | None = None

    def _ensure_entries(self) -> list[DirEntry]:
        """Load directory entries if not already loaded.

        Returns:
            The list of DirEntry objects.
        """
        if self._entries is None:
            self._entries = []
            if os.path.isdir(self._path):
                for name in os.listdir(self._path):
                    entry_path = os.path.join(self._path, name)
                    self._entries.append(DirEntry(entry_path))
        return self._entries

    def __iter__(self) -> Iterator[DirEntry]:
        """Return an iterator over the directory entries.

        Returns:
            An iterator yielding DirEntry objects.
        """
        return iter(self._ensure_entries())

    def __next__(self) -> DirEntry:
        """Return the next directory entry.

        Returns:
            The next DirEntry in the directory.
        """
        entries = self._ensure_entries()
        return entries.__iter__().__next__()

    def len(self) -> int:  # type: ignore
        """Return the number of directory entries.

        Returns:
            The count of entries in the directory.
        """
        return len(self._ensure_entries())

    def is_empty(self) -> bool:  # type: ignore
        """Check if the directory has no entries.

        Returns:
            True if the directory is empty, False otherwise.
        """
        return len(self._ensure_entries()) == 0

    def __repr__(self) -> str:
        return f"ReadDir({self._path!r})"


def metadata_from_os(path: str) -> Metadata:
    """Create a Metadata object from OS stat information at the given path.

    Args:
        path: The filesystem path to query.

    Returns:
        A Metadata object populated with file type, size, permissions, and timestamps.
    """
    meta = Metadata()
    try:
        st = os.stat(path, follow_symlinks=False)
        meta._is_symlink = os.path.islink(path)
        if os.path.isfile(path):
            meta._file_type = FileType(is_file=True)
        elif os.path.isdir(path):
            meta._file_type = FileType(is_dir=True)
        elif meta._is_symlink:
            meta._file_type = FileType(is_symlink=True)
        meta._size = st.st_size
        meta._modified = st.st_mtime
        meta._accessed = st.st_atime
        try:
            meta._created = st.st_birthtime
        except AttributeError:
            meta._created = None
        meta._permissions = Permissions(readonly=not (st.st_mode & 0o200))
    except (OSError, ValueError):
        pass
    return meta
