"""Path and PathBuf — filesystem path manipulation."""
from __future__ import annotations

"""Path and PathBuf — filesystem path types.

Provides Path for immutable paths and PathBuf for mutable paths
with join, parent, extension, file_name, and filesystem operations.
"""

import os

from .metadata import Metadata, DirEntry, ReadDir, metadata_from_os


class Path:
    """Immutable filesystem path with operations for path manipulation and filesystem access."""

    __slots__ = ("_path",)

    def __init__(self, path: str | os.PathLike) -> None:
        """Create a Path from a string or path-like object.

        Args:
            path: The filesystem path string or os.PathLike object.
        """
        self._path = os.fspath(path) if isinstance(path, os.PathLike) else path

    @classmethod
    def new(cls, path: str) -> Path:  # type: ignore
        """Create a new Path from a string.

        Args:
            path: The filesystem path string.

        Returns:
            A new Path instance.
        """
        return cls(path)

    def as_str(self) -> str:
        """Return the path as a string.

        Returns:
            The path string.
        """
        return self._path

    def to_str(self) -> str | None:
        """Return the path as a string or None.

        Returns:
            The path string, or None if not set.
        """
        return self._path

    def to_string_lossy(self) -> str:
        """Return the path as a lossy string.

        Returns:
            The path string (lossless on all platforms).
        """
        return self._path

    def to_path_buf(self) -> PathBuf:  # type: ignore
        """Convert this Path to a mutable PathBuf.

        Returns:
            A PathBuf containing this path.
        """
        return PathBuf(self._path)

    def as_os_str(self) -> str:  # type: ignore
        """Return the path as an OS string.

        Returns:
            The path as a string.
        """
        return self._path

    def is_absolute(self) -> bool:
        """Check if the path is absolute.

        Returns:
            True if the path is absolute, False otherwise.
        """
        return os.path.isabs(self._path)

    def is_relative(self) -> bool:  # type: ignore
        """Check if the path is relative.

        Returns:
            True if the path is relative, False otherwise.
        """
        return not self.is_absolute()

    def is_relative_to(self, base: str | Path) -> bool:  # type: ignore
        """Check if this path is relative to the given base path.

        Args:
            base: The base path to check against.

        Returns:
            True if this path is relative to base, False otherwise.
        """
        base_str = base.as_str() if isinstance(base, Path) else str(base)
        try:
            os.path.relpath(self._path, base_str)
            return True
        except ValueError:
            return False

    def starts_with(self, base: str | Path) -> bool:  # type: ignore
        """Check if this path starts with the given base path.

        Args:
            base: The base path to check against.

        Returns:
            True if this path starts with base, False otherwise.
        """
        base_str = base.as_str() if isinstance(base, Path) else str(base)
        return os.path.commonpath([self._path, base_str]) == base_str or self._path == base_str

    def ends_with(self, ext: str | Path) -> bool:  # type: ignore
        """Check if this path ends with the given extension or path.

        Args:
            ext: The extension or path suffix to check.

        Returns:
            True if this path ends with ext, False otherwise.
        """
        ext_str = ext.as_str() if isinstance(ext, Path) else str(ext)
        return self._path.endswith(ext_str)

    def parent(self) -> Path | None:
        """Return the parent directory of this path.

        Returns:
            A Path representing the parent directory, or None at the root.
        """
        parent = os.path.dirname(self._path)
        if not parent:
            return None
        return Path(parent)

    def file_name(self) -> str | None:  # type: ignore
        """Return the final component of the path.

        Returns:
            The file or directory name, or None if the path is empty.
        """
        return os.path.basename(self._path) or None

    def extension(self) -> str | None:  # type: ignore
        """Return the file extension without the leading dot.

        Returns:
            The extension string, or None if there is no extension.
        """
        _, ext = os.path.splitext(self._path)
        return ext[1:] if ext else None

    def file_stem(self) -> str | None:  # type: ignore
        """Return the filename without its extension.

        Returns:
            The file stem, or None if the path is empty.
        """
        stem, _ = os.path.splitext(os.path.basename(self._path))
        return stem or None

    def with_extension(self, ext: str) -> Path:  # type: ignore
        """Return a new path with the given extension replacing the current one.

        Args:
            ext: The new extension (with or without leading dot).

        Returns:
            A new Path with the updated extension.
        """
        base, _ = os.path.splitext(self._path)
        if ext and not ext.startswith('.'):
            ext = '.' + ext
        return Path(base + ext)

    def join(self, other: str | Path) -> Path:
        """Join this path with another path component.

        Args:
            other: The path component to append.

        Returns:
            A new Path representing the joined path.
        """
        other_str = other.as_str() if isinstance(other, Path) else other
        return Path(os.path.join(self._path, other_str))

    def __truediv__(self, other: str | Path) -> Path:
        return self.join(other)

    def __rtruediv__(self, other: str | Path) -> Path:
        other_str = other.as_str() if isinstance(other, Path) else other
        return Path(os.path.join(other_str, self._path))

    def exists(self) -> bool:
        """Check if the path exists on the filesystem.

        Returns:
            True if the path exists, False otherwise.
        """
        return os.path.exists(self._path)

    def is_file(self) -> bool:  # type: ignore
        """Check if the path points to a regular file.

        Returns:
            True if the path is a file, False otherwise.
        """
        return os.path.isfile(self._path)

    def is_dir(self) -> bool:  # type: ignore
        """Check if the path points to a directory.

        Returns:
            True if the path is a directory, False otherwise.
        """
        return os.path.isdir(self._path)

    def is_symlink(self) -> bool:  # type: ignore
        """Check if the path is a symbolic link.

        Returns:
            True if the path is a symlink, False otherwise.
        """
        return os.path.islink(self._path)

    def metadata(self) -> Metadata:  # type: ignore
        """Return metadata about the file or directory at this path.

        Returns:
            A Metadata object containing file type, size, permissions, and timestamps.
        """
        return metadata_from_os(self._path)

    def canonicalize(self) -> Path:  # type: ignore
        """Return the canonical absolute path, resolving symlinks.

        Returns:
            A new Path with the resolved absolute path.
        """
        return Path(os.path.realpath(self._path))

    def normalize(self) -> Path:  # type: ignore
        """Normalize the path by collapsing redundant separators.

        Returns:
            A new Path with the normalized path.
        """
        return Path(os.path.normpath(self._path))

    def display(self) -> str:
        """Return the path for display purposes.

        Returns:
            The path string.
        """
        return self._path

    def to_absolute(self) -> Path:  # type: ignore
        """Return the absolute version of this path.

        Returns:
            A new absolute Path.
        """
        return Path(os.path.abspath(self._path))

    def read_to_string(self) -> str:  # type: ignore
        """Read the file contents as a UTF-8 string.

        Returns:
            The file content as a string.
        """
        with open(self._path, 'r') as f:
            return f.read()

    def read_to_bytes(self) -> bytes:  # type: ignore
        """Read the file contents as raw bytes.

        Returns:
            The file content as bytes.
        """
        with open(self._path, 'rb') as f:
            return f.read()

    def write_str(self, data: str) -> None:  # type: ignore
        """Write a string to the file.

        Args:
            data: The string content to write.
        """
        with open(self._path, 'w') as f:
            f.write(data)

    def write_bytes(self, data: bytes) -> None:  # type: ignore
        """Write bytes to the file.

        Args:
            data: The bytes content to write.
        """
        with open(self._path, 'wb') as f:
            f.write(data)

    def create_dir(self) -> None:  # type: ignore
        """Create the directory at this path, including any necessary parent directories."""
        os.makedirs(self._path, exist_ok=True)

    def create_dir_all(self) -> None:  # type: ignore
        """Create the directory at this path and all necessary parent directories."""
        os.makedirs(self._path, exist_ok=True)

    def remove_file(self) -> None:  # type: ignore
        """Remove the file at this path."""
        os.remove(self._path)

    def remove_dir(self) -> None:  # type: ignore
        """Remove the directory at this path. Must be empty."""
        os.rmdir(self._path)

    def remove_dir_all(self) -> None:  # type: ignore
        """Remove the directory and all its contents recursively."""
        import shutil
        shutil.rmtree(self._path)

    def rename(self, to: str | Path) -> None:  # type: ignore
        """Rename or move this path to the target path.

        Args:
            to: The destination path.
        """
        to_str = to.as_str() if isinstance(to, Path) else str(to)
        os.rename(self._path, to_str)

    def copy(self, to: str | Path) -> None:  # type: ignore
        """Copy this path to the target path, preserving metadata.

        Args:
            to: The destination path.
        """
        import shutil
        to_str = to.as_str() if isinstance(to, Path) else str(to)
        shutil.copy2(self._path, to_str)

    def read_dir(self) -> ReadDir:
        """Return an iterator over the directory entries at this path.

        Returns:
            A ReadDir yielding DirEntry objects.
        """
        return ReadDir(self._path)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Path):
            return os.path.normpath(self._path) == os.path.normpath(other._path)
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Path):
            return os.path.normpath(self._path) != os.path.normpath(other._path)
        return NotImplemented

    def __lt__(self, other: Path) -> bool:
        if isinstance(other, Path):
            return os.path.normpath(self._path) < os.path.normpath(other._path)
        return NotImplemented

    def __hash__(self) -> int:
        return hash(os.path.normpath(self._path))

    def __fspath__(self) -> str:
        return self._path

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"Path({self._path!r})"


class PathBuf:
    """Mutable filesystem path that can be modified in place."""

    __slots__ = ("_path",)

    def __init__(self, path: str | os.PathLike | Path = "") -> None:
        """Create a PathBuf from a string, path-like, or Path object.

        Args:
            path: The initial path. Defaults to an empty string.
        """
        if isinstance(path, Path):
            self._path = path.as_str()
        else:
            self._path = os.fspath(path) if isinstance(path, os.PathLike) else path

    @classmethod
    def new(cls) -> PathBuf:  # type: ignore
        """Create a new empty PathBuf.

        Returns:
            A PathBuf with an empty path.
        """
        return cls("")

    @classmethod
    def from_str(cls, s: str) -> PathBuf:  # type: ignore
        """Create a PathBuf from a string.

        Args:
            s: The path string.

        Returns:
            A new PathBuf instance.
        """
        return cls(s)

    def as_path(self) -> Path:
        """Return an immutable view of this path.

        Returns:
            A Path containing the same path string.
        """
        return Path(self._path)

    def as_str(self) -> str:
        """Return the path as a string.

        Returns:
            The path string.
        """
        return self._path

    def into_string(self) -> str:  # type: ignore
        """Consume this PathBuf and return the underlying string.

        Returns:
            The path string.
        """
        return self._path

    def push(self, path: str | Path) -> None:  # type: ignore
        """Append a path component to this PathBuf.

        Args:
            path: The path component to append.
        """
        if isinstance(path, Path):
            self._path = os.path.join(self._path, path.as_str())
        else:
            self._path = os.path.join(self._path, path)

    def push_str(self, s: str) -> None:  # type: ignore
        """Append a string path component to this PathBuf.

        Args:
            s: The string to append.
        """
        self._path = os.path.join(self._path, s)

    def pop(self) -> bool:  # type: ignore
        """Remove the last path component, if possible.

        Returns:
            True if a component was removed, False if already at root.
        """
        parent = os.path.dirname(self._path)
        if parent == self._path:
            return False
        self._path = parent
        return True

    def set_extension(self, ext: str) -> bool:  # type: ignore
        """Set the file extension on this PathBuf.

        Args:
            ext: The new extension (with or without leading dot).

        Returns:
            Always returns True.
        """
        base, _ = os.path.splitext(self._path)
        if ext and not ext.startswith('.'):
            ext = '.' + ext
        self._path = base + ext
        return True

    def clear(self) -> None:  # type: ignore
        """Clear the path to an empty string."""
        self._path = ""

    def into_boxed(self) -> Path:  # type: ignore
        """Consume this PathBuf and return an immutable Path.

        Returns:
            A Path containing the path string.
        """
        return Path(self._path)

    def is_absolute(self) -> bool:  # type: ignore
        """Check if the path is absolute.

        Returns:
            True if the path is absolute, False otherwise.
        """
        return os.path.isabs(self._path)

    def parent(self) -> Path | None:  # type: ignore
        """Return the parent directory of this path.

        Returns:
            A Path representing the parent, or None at the root.
        """
        parent = os.path.dirname(self._path)
        if not parent:
            return None
        return Path(parent)

    def file_name(self) -> str | None:  # type: ignore
        """Return the final component of the path.

        Returns:
            The file or directory name, or None if the path is empty.
        """
        return os.path.basename(self._path) or None

    def extension(self) -> str | None:  # type: ignore
        """Return the file extension without the leading dot.

        Returns:
            The extension string, or None if there is no extension.
        """
        _, ext = os.path.splitext(self._path)
        return ext[1:] if ext else None

    def join(self, other: str | Path) -> PathBuf:  # type: ignore
        """Join this path with another component, returning a new PathBuf.

        Args:
            other: The path component to join.

        Returns:
            A new PathBuf with the joined path.
        """
        other_str = other.as_str() if isinstance(other, Path) else other
        return PathBuf(os.path.join(self._path, other_str))

    def canonicalize(self) -> PathBuf:  # type: ignore
        """Return the canonical absolute path, resolving symlinks.

        Returns:
            A new PathBuf with the resolved path.
        """
        return PathBuf(os.path.realpath(self._path))

    def normalize(self) -> PathBuf:  # type: ignore
        """Normalize the path by collapsing redundant separators.

        Returns:
            A new PathBuf with the normalized path.
        """
        return PathBuf(os.path.normpath(self._path))

    def exists(self) -> bool:  # type: ignore
        """Check if the path exists on the filesystem.

        Returns:
            True if the path exists, False otherwise.
        """
        return os.path.exists(self._path)

    def __truediv__(self, other: str | Path) -> PathBuf:  # type: ignore
        return self.join(other)

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"PathBuf({self._path!r})"
