"""Cursor and SeekFrom — in-memory I/O with seek support."""
from __future__ import annotations

"""Cursor and SeekFrom — in-memory I/O cursor.

Provides Cursor[T] for in-memory Read+Write+Seek operations and
SeekFrom for specifying seek positions (Start, Current, End).
"""

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class SeekFrom:
    """Specifies a seek position relative to the start, current position, or end of a stream."""

    __slots__ = ("_kind", "_offset")

    START = 0
    CURRENT = 1
    END = 2

    def __init__(self, kind: int, offset: int) -> None:
        """Create a SeekFrom with the specified kind and offset.

        Args:
            kind: One of SeekFrom.START, SeekFrom.CURRENT, or SeekFrom.END.
            offset: The byte offset relative to the seek kind.
        """
        self._kind = kind
        self._offset = offset

    @classmethod
    def start(cls, offset: int = 0) -> SeekFrom:
        """Create a seek position relative to the start of the stream.

        Args:
            offset: The byte offset from the start. Defaults to 0.

        Returns:
            A SeekFrom positioned at the given offset from the start.
        """
        return cls(cls.START, offset)

    @classmethod
    def current(cls, offset: int = 0) -> SeekFrom:
        """Create a seek position relative to the current position.

        Args:
            offset: The byte offset from the current position. Defaults to 0.

        Returns:
            A SeekFrom positioned at the given offset from the current position.
        """
        return cls(cls.CURRENT, offset)

    @classmethod
    def end(cls, offset: int = 0) -> SeekFrom:
        """Create a seek position relative to the end of the stream.

        Args:
            offset: The byte offset from the end. Defaults to 0.

        Returns:
            A SeekFrom positioned at the given offset from the end.
        """
        return cls(cls.END, offset)

    def kind(self) -> int:
        """Return the seek kind (START, CURRENT, or END).

        Returns:
            The integer constant representing the seek kind.
        """
        return self._kind

    def offset(self) -> int:
        """Return the byte offset.

        Returns:
            The offset relative to the seek kind.
        """
        return self._offset

    def __repr__(self) -> str:
        if self._kind == self.START:
            return f"SeekFrom::Start({self._offset})"
        if self._kind == self.CURRENT:
            return f"SeekFrom::Current({self._offset})"
        return f"SeekFrom::End({self._offset})"


class Cursor(Generic[T]):
    """In-memory cursor providing Read, Write, and Seek operations over a byte buffer."""

    __slots__ = ("_data", "_pos")

    def __init__(self, data: T) -> None:
        """Create a Cursor wrapping the given data.

        Args:
            data: The initial data (bytes, bytearray, str, or list) to wrap.
        """
        if isinstance(data, (bytes, bytearray)):
            self._data = bytearray(data)
        elif isinstance(data, str):
            self._data = bytearray(data.encode("utf-8"))
        elif isinstance(data, list):
            self._data = bytearray(data)
        else:
            self._data = bytearray(data)
        self._pos = 0

    @classmethod
    def new(cls, data: T) -> Cursor[T]:  # type: ignore
        """Create a new Cursor wrapping the given data.

        Args:
            data: The initial data to wrap.

        Returns:
            A new Cursor instance.
        """
        return cls(data)

    def inner(self) -> T:
        """Return a reference to the underlying buffer.

        Returns:
            The internal bytearray as type T.
        """
        return self._data  # type: ignore

    def into_inner(self) -> T:  # type: ignore
        """Consume this Cursor and return the underlying buffer.

        Returns:
            The internal bytearray as type T.
        """
        return self._data  # type: ignore

    def get_ref(self) -> Any:  # type: ignore
        """Return a reference to the underlying buffer.

        Returns:
            The internal bytearray.
        """
        return self._data  # type: ignore

    def get_mut(self) -> Any:  # type: ignore
        """Return a mutable reference to the underlying buffer.

        Returns:
            The internal bytearray.
        """
        return self._data  # type: ignore

    def position(self) -> int:
        """Return the current cursor position.

        Returns:
            The byte offset within the buffer.
        """
        return self._pos

    def set_position(self, pos: int) -> None:  # type: ignore
        """Set the cursor position.

        Args:
            pos: The new byte offset within the buffer.
        """
        self._pos = pos

    def position_mut(self) -> int:  # type: ignore
        """Return the current cursor position (mutable alias).

        Returns:
            The byte offset within the buffer.
        """
        return self._pos  # type: ignore

    def into_inner(self) -> T:
        """Consume this Cursor and return the underlying buffer.

        Returns:
            The internal bytearray as type T.
        """
        return self._data  # type: ignore

    def read(self, buf: bytearray) -> int:  # type: ignore
        """Read bytes from the cursor into the provided buffer.

        Args:
            buf: The buffer to read bytes into.

        Returns:
            The number of bytes read, or 0 if at the end.
        """
        available = len(self._data) - self._pos
        if available <= 0:
            return 0
        n = min(len(buf), available)
        buf[:n] = self._data[self._pos:self._pos + n]
        self._pos += n
        return n

    def write(self, data: bytes | bytearray | str) -> int:  # type: ignore
        """Write data at the current cursor position, extending the buffer if needed.

        Args:
            data: The bytes, bytearray, or string to write.

        Returns:
            The number of bytes written.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        end = self._pos + len(data)
        if end > len(self._data):
            self._data.extend(b"\x00" * (end - len(self._data)))
        self._data[self._pos:end] = data
        self._pos += len(data)
        return len(data)

    def flush(self) -> None:  # type: ignore
        """No-op flush for in-memory cursor."""
        pass

    def seek(self, style: SeekFrom) -> int:  # type: ignore
        """Seek to a position within the buffer.

        Args:
            style: The seek mode and offset.

        Returns:
            The new cursor position, clamped to valid bounds.
        """
        if style._kind == SeekFrom.START:
            self._pos = style._offset
        elif style._kind == SeekFrom.CURRENT:
            self._pos += style._offset
        elif style._kind == SeekFrom.END:
            self._pos = len(self._data) + style._offset
        self._pos = max(0, min(self._pos, len(self._data)))
        return self._pos

    def fill_buf(self) -> bytes:  # type: ignore
        """Return all unread data from the cursor.

        Returns:
            The bytes from the current position to the end of the buffer.
        """
        return bytes(self._data[self._pos:])

    def consume(self, amt: int) -> None:  # type: ignore
        """Advance the cursor position by up to amt bytes.

        Args:
            amt: The number of bytes to advance.
        """
        self._pos = min(self._pos + amt, len(self._data))

    def has_consumed(self) -> bool:  # type: ignore
        """Check if the cursor has reached the end of the buffer.

        Returns:
            True if all data has been consumed, False otherwise.
        """
        return self._pos >= len(self._data)

    def read_until(self, byte: int) -> bytes:  # type: ignore
        """Read bytes from the cursor until the specified byte is encountered.

        Args:
            byte: The byte value to read up to and including.

        Returns:
            The bytes read, including the delimiter byte.
        """
        chunk = self.fill_buf()
        idx = chunk.find(bytes([byte]))
        if idx >= 0:
            result = chunk[:idx + 1]
            self.consume(idx + 1)
            return result
        self.consume(len(chunk))
        return chunk

    def read_line(self) -> str:  # type: ignore
        """Read a single line from the cursor.

        Returns:
            The line content as a string, including the newline character.
        """
        return self.read_until(ord("\n")).decode("utf-8")

    def remaining(self) -> int:
        """Return the number of bytes remaining from the current position.

        Returns:
            The count of unread bytes.
        """
        return max(0, len(self._data) - self._pos)

    def is_empty(self) -> bool:
        """Check if the cursor has reached the end of the buffer.

        Returns:
            True if no data remains, False otherwise.
        """
        return self._pos >= len(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return not self.is_empty()

    def __repr__(self) -> str:
        return f"Cursor(pos={self._pos}, len={len(self._data)})"
