"""Read and BufRead traits for byte and buffered reading.

Provides the `Read` trait for raw byte reading and the `BufRead` trait
for buffered reading, along with the `BufSplitIter` and `LinesIter`
helper iterators used to split on delimiters and iterate over lines.
"""

from typing import Any

from .cursor import Cursor


class Read:
    """Abstract base class for byte reading operations.

    Implementations of `read` return bytes from a stream or buffer.
    The default implementations of the other methods build on `read`
    to provide convenience reading helpers.

    Examples:
        >>> class Reader(Read):
        ...     def __init__(self, data): self.data = data
        ...     def read(self, buf):
        ...         n = min(len(buf), len(self.data))
        ...         buf[:n] = self.data[:n]
        ...         self.data = self.data[n:]
        ...         return n
        >>> r = Reader(b"hello world")
        >>> r.read_to_string()
        'hello world'
    """

    def read(self, buf: bytearray) -> int:  # type: ignore
        """Read bytes into the provided buffer.

        Reads up to `len(buf)` bytes into `buf`. Returns 0 when the
        end of the stream is reached.

        Args:
            buf: The mutable bytearray to read bytes into.

        Returns:
            The number of bytes read, or 0 if the end of the stream
            has been reached.
        """
        raise NotImplementedError

    def read_exact(self, buf: bytearray) -> None:  # type: ignore
        """Read exactly len(buf) bytes, raising an error if insufficient data.

        Repeatedly calls `read` until the buffer is completely filled.
        Raises `IOError` if the stream ends before the buffer is full.

        Args:
            buf: The bytearray to fill completely with bytes.

        Raises:
            IOError: If the stream ends before the buffer is fully filled.
        """
        view = memoryview(buf)
        total = 0
        needed = len(buf)
        while total < needed:
            n = self.read(view[total:])
            if n == 0:
                raise IOError("failed to fill whole buffer")
            total += n

    def read_to_end(self) -> bytes:
        """Read all remaining bytes from the stream.

        Reads repeatedly in 8192-byte chunks until the end of the
        stream and returns the concatenation.

        Returns:
            A bytes object containing all remaining data.
        """
        chunks = []
        while True:
            buf = bytearray(8192)
            n = self.read(buf)
            if not n:
                break
            chunks.append(bytes(buf[:n]))
        return b"".join(chunks)

    def read_to_string(self) -> str:
        """Read all remaining bytes and decode as UTF-8.

        Returns:
            The remaining stream content decoded as a UTF-8 string.
        """
        return self.read_to_end().decode("utf-8")

    def by_ref(self) -> Any:
        """Return a reference to this reader.

        Returns:
            This `Read` instance itself.
        """
        return self


class BufRead:
    """Abstract base class for buffered reading operations.

    Builds on `Read`-style sources by exposing an internal buffer.
    Subclasses implement `fill_buf` and `consume`; convenience methods
    such as `read_line`, `split`, and `lines` are built on top.

    Examples:
        >>> class BR(BufRead):
        ...     def __init__(self, data): self.data = bytearray(data); self.pos = 0
        ...     def fill_buf(self): return bytes(self.data[self.pos:])
        ...     def consume(self, amt): self.pos += amt
        >>> br = BR(b"a\\nb\\nc")
        >>> br.read_line()
        'a\\n'
    """

    def fill_buf(self) -> bytes:  # type: ignore
        """Fill and return the internal buffer.

        Returns:
            The buffered bytes currently available for reading, or an
            empty bytes object when the underlying source is exhausted.
        """
        raise NotImplementedError

    def consume(self, amt: int) -> None:  # type: ignore
        """Consume up to amt bytes from the buffer.

        Advances the buffer position forwards by `amt` bytes.

        Args:
            amt: The number of bytes to consume from the buffer.
        """
        pass

    def has_consumed(self) -> bool:  # type: ignore
        """Check if all buffered data has been consumed.

        Returns:
            True if the buffer has been fully consumed, False otherwise.
        """
        return False

    def read_until(self, byte: int) -> bytes:  # type: ignore
        """Read bytes until the specified byte is encountered.

        Returns the bytes read, including the delimiter byte itself.

        Args:
            byte: The byte value to read up to and including.

        Returns:
            The bytes read, including the delimiter byte, or an empty
            bytes object if the stream ends first.
        """
        buf = bytearray()
        while True:
            chunk = self.fill_buf()
            if not chunk:
                break
            idx = chunk.find(bytes([byte]))
            if idx >= 0:
                buf.extend(chunk[:idx + 1])
                self.consume(idx + 1)
                return bytes(buf)
            buf.extend(chunk)
            self.consume(len(chunk))
        return bytes(buf)

    def read_line(self) -> str:
        """Read a single line from the buffer.

        Returns the line as a UTF-8 decoded string, including the
        trailing newline character.

        Returns:
            The line content as a string, including the newline character.
        """
        return self.read_until(ord("\n")).decode("utf-8")

    def split(self, byte: int) -> BufSplitIter:  # type: ignore
        """Create an iterator that splits the buffer on the specified byte.

        The returned iterator yields chunks of bytes between the given
        delimiter, including the delimiter at the end of each chunk.

        Args:
            byte: The byte value to split the stream on.

        Returns:
            A BufSplitIter yielding chunks up to and including each
            delimiter occurrence.
        """
        return BufSplitIter(self, byte)

    def lines(self) -> LinesIter:  # type: ignore
        """Create an iterator over the lines in the buffer.

        The returned iterator yields each line as a UTF-8 string.

        Returns:
            A LinesIter yielding each line as a string.
        """
        return LinesIter(self)


class BufSplitIter:
    """Iterator that yields byte chunks split by a delimiter.

    Iterate over a `BufRead` source, yielding each chunk of bytes up to
    and including a delimiter byte.

    Examples:
        >>> from .buffered import BufReader
        >>> br = BufReader(Cursor(b"a,b,c"))
        >>> list(BufSplitIter(br, ord(",")))
        [b'a,', b'b,', b'c']
    """

    __slots__ = ("_reader", "_byte", "_done")

    def __init__(self, reader: BufRead, byte: int) -> None:
        """Initialize the split iterator.

        Args:
            reader: The BufRead instance to read from.
            byte: The byte value to split on.
        """
        self._reader = reader
        self._byte = byte
        self._done = False

    def __iter__(self) -> BufSplitIter:
        """Return this iterator.

        Returns:
            This BufSplitIter instance.
        """
        return self

    def __next__(self) -> bytes:
        """Return the next chunk between delimiters.

        Returns:
            The next chunk of bytes, including the delimiter byte.

        Raises:
            StopIteration: If there are no more chunks to yield.
        """
        if self._done:
            raise StopIteration
        result = self._reader.read_until(self._byte)
        if not result:
            self._done = True
            raise StopIteration
        return result


class LinesIter:
    """Iterator that yields lines from a buffered reader.

    Iterate over a `BufRead` source, yielding each line as a UTF-8
    decoded string including its trailing newline.

    Examples:
        >>> from .buffered import BufReader
        >>> br = BufReader(Cursor(b"one\\ntwo\\n"))
        >>> list(LinesIter(br))
        ['one\\n', 'two\\n']
    """

    __slots__ = ("_reader", "_done")

    def __init__(self, reader: BufRead) -> None:
        """Initialize the lines iterator.

        Args:
            reader: The BufRead instance to read lines from.
        """
        self._reader = reader
        self._done = False

    def __iter__(self) -> LinesIter:
        """Return this iterator.

        Returns:
            This LinesIter instance.
        """
        return self

    def __next__(self) -> str:
        """Return the next line.

        Returns:
            The next line as a UTF-8 string, including the newline.

        Raises:
            StopIteration: If there are no more lines to yield.
        """
        if self._done:
            raise StopIteration
        line = self._reader.read_line()
        if not line:
            self._done = True
            raise StopIteration
        return line
