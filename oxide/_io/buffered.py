"""BufReader and BufWriter for buffered I/O with configurable capacity.

Provides `BufReader` for buffered reading and `BufWriter` for buffered
writing over an inner reader/writer, with configurable buffer capacity
and automatic flushing.
"""

from typing import Any

from .cursor import SeekFrom
from .read import BufSplitIter, LinesIter


class BufReader:
    """Buffered reader that wraps an inner reader with a configurable buffer capacity.

    Reads from an underlying reader in chunks into an internal buffer
    to reduce the number of small read calls. Implements the `Read`
    and `BufRead` interfaces and supports seeking if the inner reader
    is seekable.

    Examples:
        >>> from .cursor import Cursor
        >>> inner = Cursor(b"hello world")
        >>> r = BufReader(inner)
        >>> r.read_to_string()
        'hello world'
    """

    __slots__ = ("_inner", "_buffer", "_pos", "_capacity")

    def __init__(self, inner: Any, capacity: int = 8192) -> None:
        """Create a new BufReader with the given capacity.

        Args:
            inner: The underlying reader to buffer.
            capacity: The buffer capacity in bytes. Defaults to 8192.
        """
        self._inner = inner
        self._buffer = bytearray()
        self._pos = 0
        self._capacity = capacity

    @classmethod
    def with_capacity(cls, capacity: int, inner: Any) -> BufReader:  # type: ignore
        """Create a BufReader with a specific buffer capacity.

        Args:
            capacity: The buffer capacity in bytes.
            inner: The underlying reader to buffer.

        Returns:
            A new BufReader instance.
        """
        return cls(inner, capacity)

    def inner(self) -> Any:
        """Return a reference to the underlying reader.

        Returns:
            The inner reader instance.
        """
        return self._inner

    def into_inner(self) -> Any:  # type: ignore
        """Consume this BufReader and return the underlying reader.

        Note that any buffered but unread data is discarded.

        Returns:
            The inner reader instance.
        """
        return self._inner

    def buffer(self) -> bytes:  # type: ignore
        """Return the remaining buffered data that has not yet been consumed.

        Returns:
            The unread buffered bytes.
        """
        return bytes(self._buffer[self._pos:])

    def capacity(self) -> int:
        """Return the buffer capacity in bytes.

        Returns:
            The maximum number of bytes the buffer can hold.
        """
        return self._capacity

    def set_capacity(self, capacity: int) -> None:  # type: ignore
        """Set a new buffer capacity.

        Args:
            capacity: The new buffer capacity in bytes.
        """
        self._capacity = capacity

    def fill_buf(self) -> bytes:  # type: ignore
        """Fill the buffer from the underlying reader and return available data.

        If the current buffer is exhausted, read a fresh chunk of up to
        `capacity` bytes from the inner reader.

        Returns:
            The buffered bytes available for reading.
        """
        if self._pos >= len(self._buffer):
            self._buffer = bytearray()
            self._pos = 0
            read_buf = bytearray(self._capacity)
            n = self._inner.read(read_buf)
            self._buffer = bytearray(read_buf[:n])
        return bytes(self._buffer[self._pos:])

    def consume(self, amt: int) -> None:  # type: ignore
        """Consume up to amt bytes from the buffer.

        Args:
            amt: The number of bytes to consume from the buffer.
        """
        self._pos = min(self._pos + amt, len(self._buffer))

    def has_consumed(self) -> bool:
        """Check if all buffered data has been consumed.

        Returns:
            True if the buffer has been fully consumed, False otherwise.
        """
        return self._pos >= len(self._buffer)

    def read(self, buf: bytearray) -> int:  # type: ignore
        """Read bytes into the provided buffer, using buffered data when available.

        If buffered data is available it is used first; otherwise data
        is read directly from the inner reader.

        Args:
            buf: The buffer to read bytes into.

        Returns:
            The number of bytes read, or 0 at the end of the stream.
        """
        buffered = self.fill_buf()
        if not buffered:
            return self._inner.read(buf)  # type: ignore
        n = min(len(buf), len(buffered))
        buf[:n] = buffered[:n]
        self.consume(n)
        return n

    def read_exact(self, buf: bytearray) -> None:  # type: ignore
        """Read exactly len(buf) bytes, raising an error if insufficient data.

        Args:
            buf: The buffer to fill completely with bytes.

        Raises:
            IOError: If the stream ends before the buffer is filled.
        """
        total = 0
        needed = len(buf)
        while total < needed:
            n = self.read(buf[total:])
            if n == 0:
                raise IOError("failed to fill whole buffer")
            total += n

    def read_to_end(self) -> bytes:  # type: ignore
        """Read all remaining bytes from the stream.

        Returns:
            A bytes object containing all remaining data.
        """
        chunks = [bytes(self._buffer[self._pos:])]
        self._buffer = bytearray()
        self._pos = 0
        while True:
            read_buf = bytearray(8192)
            n = self._inner.read(read_buf)
            if n == 0:
                break
            chunks.append(bytes(read_buf[:n]))
        return b"".join(chunks)

    def read_to_string(self) -> str:  # type: ignore
        """Read all remaining bytes and decode as UTF-8.

        Returns:
            The remaining stream content as a string.
        """
        return self.read_to_end().decode("utf-8")

    def read_until(self, byte: int) -> bytes:  # type: ignore
        """Read bytes until the specified byte is encountered.

        Args:
            byte: The byte value to read up to and including.

        Returns:
            The bytes read, including the delimiter byte.
        """
        buf = bytearray()
        while True:
            chunk = self.fill_buf()
            if not chunk:
                rest = self._inner.read_until(byte)  # type: ignore
                buf.extend(rest)
                return bytes(buf)
            idx = chunk.find(bytes([byte]))
            if idx >= 0:
                buf.extend(chunk[:idx + 1])
                self.consume(idx + 1)
                return bytes(buf)
            buf.extend(chunk)
            self.consume(len(chunk))

    def read_line(self) -> str:  # type: ignore
        """Read a single line from the buffer.

        Returns:
            The line content as a string, including the newline character.
        """
        return self.read_until(ord("\n")).decode("utf-8")

    def split(self, byte: int) -> BufSplitIter:  # type: ignore
        """Create an iterator that splits the buffer on the specified byte.

        Args:
            byte: The byte value to split on.

        Returns:
            A BufSplitIter yielding chunks between delimiters.
        """
        return BufSplitIter(self, byte)

    def lines(self) -> LinesIter:  # type: ignore
        """Create an iterator over lines in the buffer.

        Returns:
            A LinesIter yielding each line as a string.
        """
        return LinesIter(self)

    def seek(self, style: SeekFrom) -> int:  # type: ignore
        """Seek to a position in the underlying stream.

        Args:
            style: The seek mode and offset.

        Returns:
            The new stream position.

        Raises:
            IOError: If the underlying stream is not seekable.
        """
        if hasattr(self._inner, 'seek'):
            self._buffer = bytearray()
            self._pos = 0
            return self._inner.seek(style)  # type: ignore
        raise IOError("underlying stream is not seekable")

    def __enter__(self) -> BufReader:
        """Enter the context manager.

        Returns:
            This BufReader instance.
        """
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager without closing the underlying reader."""
        pass

    def __repr__(self) -> str:
        return f"BufReader(buffered={len(self._buffer) - self._pos})"


class BufWriter:
    """Buffered writer that wraps an inner writer with a configurable buffer capacity."""

    __slots__ = ("_inner", "_buffer", "_pos", "_closed", "_capacity")

    def __init__(self, inner: Any, capacity: int = 8192) -> None:
        """Create a new BufWriter with the given capacity.

        Args:
            inner: The underlying writer to buffer.
            capacity: The buffer capacity in bytes. Defaults to 8192.
        """
        self._inner = inner
        self._buffer = bytearray()
        self._pos = 0
        self._capacity = capacity
        self._closed = False

    @classmethod
    def with_capacity(cls, capacity: int, inner: Any) -> BufWriter:  # type: ignore
        """Create a BufWriter with a specific buffer capacity.

        Args:
            capacity: The buffer capacity in bytes.
            inner: The underlying writer to buffer.

        Returns:
            A new BufWriter instance.
        """
        return cls(inner, capacity)

    def inner(self) -> Any:
        """Return a reference to the underlying writer.

        Returns:
            The inner writer instance.
        """
        return self._inner

    def into_inner(self) -> Any:  # type: ignore
        """Flush buffered data and consume this BufWriter, returning the underlying writer.

        Returns:
            The inner writer instance.
        """
        self.flush()
        return self._inner

    def buffer(self) -> bytes:  # type: ignore
        """Return the buffered data that has not yet been flushed.

        Returns:
            The unflushed buffered bytes.
        """
        return bytes(self._buffer[self._pos:])

    def capacity(self) -> int:
        """Return the buffer capacity in bytes.

        Returns:
            The maximum number of bytes the buffer can hold.
        """
        return self._capacity

    def write(self, data: bytes | bytearray | str) -> int:  # type: ignore
        """Write data to the buffer, flushing when necessary.

        Args:
            data: The bytes, bytearray, or string to write.

        Returns:
            The number of bytes written.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        if len(data) > self._capacity:
            self.flush()
            return self._inner.write(data)  # type: ignore
        if len(self._buffer) + len(data) > self._capacity:
            self.flush()
        self._buffer.extend(data)
        return len(data)

    def write_all(self, data: bytes | bytearray | str) -> None:  # type: ignore
        """Write all data to the buffer.

        Args:
            data: The bytes, bytearray, or string to write completely.
        """
        self.write(data)

    def flush(self) -> None:  # type: ignore
        """Flush buffered data to the underlying writer."""
        if self._buffer:
            self._inner.write(bytes(self._buffer))  # type: ignore
            if hasattr(self._inner, 'flush'):
                self._inner.flush()
            self._buffer = bytearray()
            self._pos = 0

    def write_fmt(self, args: Any) -> None:  # type: ignore
        """Write formatted string representation of args to the buffer.

        Args:
            args: The object whose string representation will be written.
        """
        self.write(str(args))

    def seek(self, style: SeekFrom) -> int:  # type: ignore
        """Flush buffered data and seek to a position in the underlying stream.

        Args:
            style: The seek mode and offset.

        Returns:
            The new stream position.

        Raises:
            IOError: If the underlying stream is not seekable.
        """
        self.flush()
        if hasattr(self._inner, 'seek'):
            return self._inner.seek(style)  # type: ignore
        raise IOError("underlying stream is not seekable")

    def into_raw_fd(self) -> None:  # type: ignore
        """Flush buffered data before returning the raw file descriptor."""
        self.flush()

    def __enter__(self) -> BufWriter:
        """Enter the context manager.

        Returns:
            This BufWriter instance.
        """
        return self

    def __exit__(self, *_: Any) -> None:  # type: ignore
        """Exit the context manager, flushing any remaining buffered data."""
        self.flush()

    def __del__(self) -> None:
        try:
            self.flush()
        except Exception:
            pass

    def __repr__(self) -> str:
        return f"BufWriter(buffered={len(self._buffer)})"
