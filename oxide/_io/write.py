"""Write trait for byte and string writing.

Provides the `Write` trait for writing bytes, bytearrays, and strings
to a stream, along with convenience helpers to write all data and flush.
"""
from __future__ import annotations

from typing import Any


class Write:
    """Abstract base class for byte and string writing operations.

    Implementations of `write` send bytes to an underlying sink. The
    default `write_all` and `flush` build on `write` to provide
    convenient, complete writes.

    Examples:
        >>> class Writer(Write):
        ...     def __init__(self): self.data = b""
        ...     def write(self, data):
        ...         self.data += data
        ...         return len(data)
        >>> w = Writer()
        >>> w.write_all("hi there")
        >>> w.data
        b'hi there'
    """

    def write(self, data: bytes | bytearray | str) -> int:  # type: ignore
        """Write data to the stream.

        Writes as much of `data` as possible and returns the number of
        bytes written. A short write does not necessarily mean an error.

        Args:
            data: The bytes, bytearray, or string to write.

        Returns:
            The number of bytes written.
        """
        raise NotImplementedError

    def write_all(self, data: bytes | bytearray | str) -> None:  # type: ignore
        """Write all data to the stream, blocking until complete.

        Encodes strings as UTF-8 and calls `write` repeatedly until the
        entire payload has been written.

        Args:
            data: The bytes, bytearray, or string to write completely.
        """
        total = 0
        if isinstance(data, str):
            data = data.encode("utf-8")
        while total < len(data):
            n = self.write(data[total:])
            total += n

    def flush(self) -> None:  # type: ignore
        """Flush any buffered data to the underlying stream."""
        pass

    def by_ref(self) -> Any:
        """Return a reference to this writer.

        Returns:
            This `Write` instance itself.
        """
        return self
