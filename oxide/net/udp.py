"""UDP networking — datagram sockets.

Provides UdpSocket for send_to, recv_from, and connected UDP operations.
"""
from __future__ import annotations

import os
from typing import Any

from .address import SocketAddr


class UdpSocket:
    """A UDP datagram socket for sending and receiving messages.

    Wraps a datagram socket. Use :meth:`bind` to create a local socket and
    :meth:`send_to`/:meth:`recv_from` for connectionless I/O, or
    :meth:`connect` followed by :meth:`send`/:meth:`recv` for connected
    operation.

    Needs a peer on the destination address, so it is shown rather than
    executed::

        sock = UdpSocket.bind(SocketAddr.from_str("0.0.0.0:0"))
        peer = SocketAddr.from_str("127.0.0.1:8080")
        sock.send_to(b"hello", peer)
    """

    __slots__ = ("_socket", "_addr")

    def __init__(self, sock: Any, addr: SocketAddr | None = None) -> None:
        self._socket = sock
        self._addr = addr

    @classmethod
    def bind(cls, addr: SocketAddr) -> UdpSocket:
        """Bind a UDP socket to the given local address.

        Args:
            addr (SocketAddr): The local address to bind to.

        Returns:
            UdpSocket: The bound socket.

        Raises:
            OSError: If binding fails.
        """
        import socket
        sock = socket.socket(
            socket.AF_INET if addr.is_ipv4() else socket.AF_INET6,
            socket.SOCK_DGRAM,
        )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(addr.to_socket_addr())
        return UdpSocket(sock, addr)

    @classmethod
    def from_std(cls, socket: Any, addr: SocketAddr | None = None) -> UdpSocket:
        """Wrap an existing socket object as a UdpSocket.

        Args:
            socket (Any): An existing datagram socket.
            addr (SocketAddr | None, optional): The bound address, or None.

        Returns:
            UdpSocket: The wrapped socket.
        """
        return UdpSocket(socket, addr)

    def local_addr(self) -> SocketAddr | None:  # type: ignore
        """Return the local socket address, or None if unavailable.

        Returns:
            SocketAddr | None: The local address.
        """
        if self._socket:
            try:
                addr = self._socket.getsockname()
                return SocketAddr.from_str(f"{addr[0]}:{addr[1]}")
            except Exception:
                pass
        return None

    def send_to(self, buf: bytes | bytearray, target: SocketAddr) -> int:  # type: ignore
        """Send a datagram to the specified target address.

        Args:
            buf (bytes | bytearray): The datagram data to send.
            target (SocketAddr): The destination address.

        Returns:
            int: The number of bytes sent.
        """
        return self._socket.sendto(buf, target.to_socket_addr())  # type: ignore

    def recv_from(self, buf_size: int) -> tuple[bytes, SocketAddr]:  # type: ignore
        """Receive a datagram and return the data and source address.

        Args:
            buf_size (int): Maximum number of bytes to receive.

        Returns:
            tuple[bytes, SocketAddr]: The received data and the peer
                address that sent it.
        """
        data, addr = self._socket.recvfrom(buf_size)  # type: ignore
        sock_addr = SocketAddr.from_str(f"{addr[0]}:{addr[1]}")
        return data, sock_addr

    def recv(self, buf_size: int) -> bytes:  # type: ignore
        """Receive a datagram from a connected socket.

        Args:
            buf_size (int): Maximum number of bytes to receive.

        Returns:
            bytes: The received data.
        """
        return self._socket.recv(buf_size)  # type: ignore

    def send(self, data: bytes | bytearray) -> int:  # type: ignore
        """Send a datagram on a connected socket.

        The socket must have been connected via :meth:`connect`.

        Args:
            data (bytes | bytearray): The datagram data to send.

        Returns:
            int: The number of bytes sent.
        """
        return self._socket.send(data)  # type: ignore

    def connect(self, addr: SocketAddr) -> None:  # type: ignore
        """Connect the socket to a remote address for send/recv.

        After connecting, only datagrams to/from the connected address are
        exchanged. Use :meth:`send`/:meth:`recv` afterwards.

        Args:
            addr (SocketAddr): The remote address to connect to.
        """
        self._socket.connect(addr.to_socket_addr())  # type: ignore
        self._addr = addr

    def set_broadcast(self, on: bool) -> None:  # type: ignore
        """Enable or disable broadcast transmission on this socket.

        Args:
            on (bool): True to allow broadcasting, False to disable it.
        """
        self._socket.setsockopt(
            __import__('socket').SOL_SOCKET,
            __import__('socket').SO_BROADCAST,
            1 if on else 0,
        )

    def set_nonblocking(self, nonblocking: bool) -> None:  # type: ignore
        """Set the socket to blocking or non-blocking mode.

        Args:
            nonblocking (bool): True for non-blocking, False for blocking.
        """
        self._socket.setblocking(not nonblocking)

    def set_read_timeout(self, dur: float | None) -> None:  # type: ignore
        """Set the read timeout in seconds, or None for no timeout.

        Args:
            dur (float | None): Timeout in seconds, or None to disable.
        """
        self._socket.settimeout(dur)

    def set_ttl(self, ttl: int) -> None:  # type: ignore
        """Set the IP time-to-live for outgoing packets.

        Args:
            ttl (int): The time-to-live value, typically 1-255.
        """
        import socket
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)

    def take_error(self) -> Exception | None:  # type: ignore
        """Return and clear any pending socket error, or None.

        Used to check for asynchronous errors that may not be raised by
        normal receive calls (e.g. ICMP port unreachable).

        Returns:
            Exception | None: An OSError describing the pending error, or
                None if none is pending.
        """
        try:
            err = self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err != 0:
                return OSError(err, os.strerror(err))
        except Exception:
            pass
        return None

    def into_inner(self) -> Any:  # type: ignore
        """Return the underlying socket object.

        Returns:
            Any: The wrapped socket.
        """
        return self._socket

    def __enter__(self) -> UdpSocket:
        return self

    def __exit__(self, *_: Any) -> None:  # type: ignore
        pass

    def __repr__(self) -> str:
        return f"UdpSocket({self._addr})"
