"""TCP networking — streams and listeners.

Provides TcpStream for client connections and TcpListener for
server sockets with accept, incoming, and stream operations.
"""
from __future__ import annotations

from typing import Any

from .address import SocketAddr, Shutdown


class TcpStream:
    """A TCP stream connection for reading and writing bytes.

    Wraps a blocking socket. Use :meth:`connect` or :meth:`connect_timeout`
    to open a client connection, then read and write via :meth:`read` and
    :meth:`write`. Supports timeout and non-blocking configuration.

    Needs a peer listening on the address, so it is shown rather than
    executed::

        stream = TcpStream.connect(SocketAddr.from_str("127.0.0.1:8080"))
        stream.write(b"ping")
        stream.shutdown(Shutdown.both())
    """

    __slots__ = ("_stream", "_addr")

    def __init__(self, stream: Any, addr: SocketAddr | None = None) -> None:
        self._stream = stream
        self._addr = addr

    @classmethod
    def connect(cls, addr: SocketAddr) -> TcpStream:
        """Open a TCP connection to a remote socket address.

        The resulting stream is blocking. Call :meth:`set_nonblocking` or
        :meth:`set_read_timeout` to adjust behavior.

        Args:
            addr (SocketAddr): The remote address to connect to.

        Returns:
            TcpStream: The connected stream.

        Raises:
            OSError: If the connection cannot be established.
        """
        import socket
        sock = socket.socket(
            socket.AF_INET if addr.is_ipv4() else socket.AF_INET6,
            socket.SOCK_STREAM,
        )
        sock.connect(addr.to_socket_addr())
        sock.setblocking(True)
        return TcpStream(sock, addr)

    @classmethod
    def connect_timeout(cls, addr: SocketAddr, timeout: float) -> TcpStream:
        """Open a TCP connection with a connect timeout in seconds.

        Args:
            addr (SocketAddr): The remote address to connect to.
            timeout (float): Maximum time in seconds to wait to connect.

        Returns:
            TcpStream: The connected stream.

        Raises:
            OSError: If the connection fails or times out.
        """
        import socket
        sock = socket.socket(
            socket.AF_INET if addr.is_ipv4() else socket.AF_INET6,
            socket.SOCK_STREAM,
        )
        sock.settimeout(timeout)
        sock.connect(addr.to_socket_addr())
        sock.setblocking(True)
        return TcpStream(sock, addr)

    @classmethod
    def from_stream(cls, stream: Any, addr: SocketAddr | None = None) -> TcpStream:
        """Wrap an existing socket object as a TcpStream.

        Args:
            stream (Any): An already-connected socket object.
            addr (SocketAddr | None, optional): The peer address, or None.

        Returns:
            TcpStream: The wrapped stream.
        """
        return TcpStream(stream, addr)

    def peer_addr(self) -> SocketAddr | None:  # type: ignore
        """Return the remote (peer) socket address, or None if unavailable.

        Returns:
            SocketAddr | None: The peer address.
        """
        if self._addr:
            return self._addr
        if self._stream:
            try:
                addr = self._stream.getpeername()
                return SocketAddr.from_str(f"{addr[0]}:{addr[1]}")
            except Exception:
                pass
        return None

    def local_addr(self) -> SocketAddr | None:  # type: ignore
        """Return the local socket address, or None if unavailable.

        Returns:
            SocketAddr | None: The local address.
        """
        if self._stream:
            try:
                addr = self._stream.getsockname()
                return SocketAddr.from_str(f"{addr[0]}:{addr[1]}")
            except Exception:
                pass
        return None

    def shutdown(self, how: Shutdown) -> None:  # type: ignore
        """Shut down the stream in the specified direction.

        Args:
            how (Shutdown): Which side(s) to close, e.g. `Shutdown.both()`.
        """
        import socket
        if not self._stream:
            return
        if how.kind() == Shutdown.READ:
            self._stream.shutdown(socket.SHUT_RD)
        elif how.kind() == Shutdown.WRITE:
            self._stream.shutdown(socket.SHUT_WR)
        else:
            self._stream.shutdown(socket.SHUT_RDWR)

    def set_nodelay(self, nodelay: bool) -> None:  # type: ignore
        """Enable or disable the TCP_NODELAY (Nagle's algorithm) option.

        Args:
            nodelay (bool): True to disable Nagle's algorithm, False to
                enable it.
        """
        if self._stream:
            self._stream.setsockopt(
                __import__('socket').IPPROTO_TCP,
                __import__('socket').TCP_NODELAY,
                1 if nodelay else 0,
            )

    def set_nonblocking(self, nonblocking: bool) -> None:  # type: ignore
        """Set the stream to blocking or non-blocking mode.

        Args:
            nonblocking (bool): True for non-blocking mode, False for
                blocking mode.
        """
        if self._stream:
            self._stream.setblocking(not nonblocking)

    def set_read_timeout(self, dur: float | None) -> None:  # type: ignore
        """Set the read timeout in seconds, or None for no timeout.

        Args:
            dur (float | None): Timeout in seconds, or None to disable.
        """
        if self._stream:
            self._stream.settimeout(dur)

    def set_write_timeout(self, dur: float | None) -> None:  # type: ignore
        """Set the write timeout in seconds, or None for no timeout.

        Args:
            dur (float | None): Timeout in seconds, or None to disable.
        """
        if self._stream:
            self._stream.settimeout(dur)

    def read(self, buf: bytearray) -> int:  # type: ignore
        """Read bytes from the stream into the provided buffer.

        Args:
            buf (bytearray): The buffer to receive the data into.

        Returns:
            int: The number of bytes read, or 0 on end of stream.
        """
        return self._stream.recv_into(buf)  # type: ignore

    def write(self, data: bytes | bytearray) -> int:  # type: ignore
        """Write bytes to the stream and return the number written.

        Args:
            data (bytes | bytearray): The data to send.

        Returns:
            int: The number of bytes written.
        """
        return self._stream.send(data)  # type: ignore

    def write_all(self, data: bytes | bytearray) -> None:  # type: ignore
        """Write all bytes to the stream, retrying until complete.

        Args:
            data (bytes | bytearray): The data to send.

        Raises:
            OSError: If the write fails before all bytes are sent.
        """
        total = 0
        while total < len(data):
            n = self._stream.send(data[total:])  # type: ignore
            total += n

    def try_clone(self) -> TcpStream:  # type: ignore
        """Duplicate the stream's underlying socket.

        Returns:
            TcpStream: A new TcpStream sharing the same underlying socket.
        """
        import socket
        new_sock = socket.dup(self._stream)  # type: ignore
        return TcpStream(new_sock, self._addr)

    def into_inner(self) -> Any:  # type: ignore
        """Return the underlying socket object.

        Returns:
            Any: The wrapped socket.
        """
        return self._stream

    def as_raw_fd(self) -> Any:  # type: ignore
        """Return the underlying socket object.

        Returns:
            Any: The wrapped socket.
        """
        return self._stream

    def __enter__(self) -> TcpStream:
        return self

    def __exit__(self, *_: Any) -> None:
        try:
            self._stream.close()
        except Exception:
            pass

    def __repr__(self) -> str:
        return f"TcpStream({self._addr})"


class TcpListener:
    """A TCP server socket that listens for and accepts incoming connections.

    Binds to a local address with :meth:`bind`, then accepts connections
    individually with :meth:`accept` or iterates over them via
    :meth:`incoming`. Supports timeouts and non-blocking mode.

    Blocks until a client connects, so it is shown rather than executed::

        listener = TcpListener.bind(SocketAddr.from_str("127.0.0.1:8080"))
        for stream in listener.incoming():
            stream.write(b"hello")
    """

    __slots__ = ("_listener", "_addr")

    def __init__(self, listener: Any, addr: SocketAddr | None = None) -> None:
        self._listener = listener
        self._addr = addr

    @classmethod
    def bind(cls, addr: SocketAddr) -> TcpListener:
        """Bind and start listening on the given socket address.

        The underlying socket reuses the address (SO_REUSEADDR) and has a
        listen backlog of 128.

        Args:
            addr (SocketAddr): The local address to bind to.

        Returns:
            TcpListener: The listening socket.

        Raises:
            OSError: If binding fails.
        """
        import socket
        sock = socket.socket(
            socket.AF_INET if addr.is_ipv4() else socket.AF_INET6,
            socket.SOCK_STREAM,
        )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(addr.to_socket_addr())
        sock.listen(128)
        return TcpListener(sock, addr)

    @classmethod
    def from_std(cls, listener: Any, addr: SocketAddr | None = None) -> TcpListener:
        """Wrap an existing socket listener as a TcpListener.

        Args:
            listener (Any): An existing listening socket object.
            addr (SocketAddr | None, optional): The bound address, or None.

        Returns:
            TcpListener: The wrapped listener.
        """
        return TcpListener(listener, addr)

    def local_addr(self) -> SocketAddr | None:  # type: ignore
        """Return the local address this listener is bound to, or None.

        Returns:
            SocketAddr | None: The bound address.
        """
        if self._listener:
            try:
                addr = self._listener.getsockname()
                return SocketAddr.from_str(f"{addr[0]}:{addr[1]}")
            except Exception:
                pass
        return None

    def accept(self) -> tuple[TcpStream, SocketAddr]:  # type: ignore
        """Accept a new incoming connection.

        Blocks until a connection is available (or times out if
        non-blocking/timeout is set).

        Returns:
            tuple[TcpStream, SocketAddr]: The accepted stream and the peer
                address.

        Raises:
            OSError: If the accept call fails.
        """
        conn, addr = self._listener.accept()  # type: ignore
        sock_addr = SocketAddr.from_str(f"{addr[0]}:{addr[1]}")
        return TcpStream(conn, sock_addr), sock_addr

    def accept_timeout(self, timeout: float) -> tuple[TcpStream, SocketAddr] | None:  # type: ignore
        """Accept a connection with a timeout in seconds.

        Args:
            timeout (float): Maximum seconds to wait for a connection.

        Returns:
            tuple[TcpStream, SocketAddr] | None: The accepted stream and
                peer address, or None if the timeout elapsed.
        """
        import socket
        self._listener.settimeout(timeout)  # type: ignore
        try:
            return self.accept()
        except socket.timeout:
            return None
        finally:
            self._listener.setblocking(True)  # type: ignore

    def incoming(self) -> Incoming:  # type: ignore
        """Return an iterator over incoming connections.

        The returned iterator yields a :class:`TcpStream` for each accepted
        connection until an accept error or timeout occurs.

        Returns:
            Incoming: An iterator of TcpStream objects.
        """
        return Incoming(self)

    def set_nonblocking(self, nonblocking: bool) -> None:  # type: ignore
        """Set the listener to blocking or non-blocking mode.

        Args:
            nonblocking (bool): True for non-blocking, False for blocking.
        """
        if self._listener:
            self._listener.setblocking(not nonblocking)

    def into_inner(self) -> Any:  # type: ignore
        """Return the underlying socket listener object.

        Returns:
            Any: The wrapped listener socket.
        """
        return self._listener

    def __enter__(self) -> TcpListener:
        return self

    def __exit__(self, *_: Any) -> None:  # type: ignore
        pass

    def __repr__(self) -> str:
        return f"TcpListener({self._addr})"


class Incoming:
    """Iterator over incoming TCP connections from a TcpListener.

    Iterating accepts connections one at a time; an accept error or the
    listener becoming unavailable terminates iteration.

    Blocks until a client connects, so it is shown rather than executed::

        listener = TcpListener.bind(SocketAddr.from_str("127.0.0.1:8080"))
        for stream in listener.incoming():
            print(stream.peer_addr())
    """

    __slots__ = ("_listener", "_done")

    def __init__(self, listener: TcpListener) -> None:
        self._listener = listener
        self._done = False

    def __iter__(self) -> Incoming:
        """Return the iterator itself.

        Returns:
            Incoming: Self, as this is its own iterator.
        """
        return self

    def __next__(self) -> TcpStream:
        """Yield the next accepted connection.

        Returns:
            TcpStream: The next accepted stream.

        Raises:
            StopIteration: When no further connections can be accepted.
        """
        if self._done:
            raise StopIteration
        try:
            conn, _ = self._listener.accept()
            return conn
        except Exception:
            self._done = True
            raise StopIteration
