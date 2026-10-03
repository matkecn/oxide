"""Address types — IP addresses and socket addresses.

Provides Ipv4Addr, Ipv6Addr, IpAddr, SocketAddr, and Shutdown
for network addressing.
"""
from __future__ import annotations


class Shutdown:
    """Represents the direction(s) in which a socket connection is closed.

    A shutdown applies to the read side, write side, or both sides of a
    connection. Use the class methods to obtain the appropriate mode.

    Examples:
        >>> Shutdown.read()
        Shutdown::Read
        >>> Shutdown.both()
        Shutdown::Both
    """

    __slots__ = ("_kind",)

    READ = 0
    WRITE = 1
    BOTH = 2

    def __init__(self, kind: int) -> None:
        self._kind = kind

    @classmethod
    def read(cls) -> Shutdown:
        """Create a shutdown mode that closes only the read side.

        Returns:
            Shutdown: A shutdown configured for `Shutdown.READ`.
        """
        return cls(cls.READ)

    @classmethod
    def write(cls) -> Shutdown:
        """Create a shutdown mode that closes only the write side.

        Returns:
            Shutdown: A shutdown configured for `Shutdown.WRITE`.
        """
        return cls(cls.WRITE)

    @classmethod
    def both(cls) -> Shutdown:
        """Create a shutdown mode that closes both the read and write sides.

        Returns:
            Shutdown: A shutdown configured for `Shutdown.BOTH`.
        """
        return cls(cls.BOTH)

    def kind(self) -> int:
        """Return the raw integer constant backing this shutdown mode.

        Returns:
            int: One of `Shutdown.READ`, `Shutdown.WRITE`, or `Shutdown.BOTH`.
        """
        return self._kind

    def __repr__(self) -> str:
        if self._kind == self.READ:
            return "Shutdown::Read"
        if self._kind == self.WRITE:
            return "Shutdown::Write"
        return "Shutdown::Both"


class Ipv4Addr:
    """An IPv4 address stored as four 0-255 octets.

    Comparable, hashable, and immutable. Supports construction from
    octets, dotted-quad strings, or raw bytes, and provides common
    classification predicates.

    Examples:
        >>> addr = Ipv4Addr.new(127, 0, 0, 1)
        >>> addr.is_loopback()
        True
        >>> str(addr)
        '127.0.0.1'
    """

    __slots__ = ("_octets",)

    def __init__(self, a: int = 0, b: int = 0, c: int = 0, d: int = 0) -> None:
        """Construct an IPv4 address from up to four octets.

        With no arguments the address defaults to ``0.0.0.0``.

        Args:
            a (int, optional): First octet. Defaults to ``0``.
            b (int, optional): Second octet. Defaults to ``0``.
            c (int, optional): Third octet. Defaults to ``0``.
            d (int, optional): Fourth octet. Defaults to ``0``.
        """
        self._octets = (a, b, c, d)

    @classmethod
    def new(cls, a: int, b: int, c: int, d: int) -> Ipv4Addr:  # type: ignore
        """Create an IPv4 address from four individual octets.

        Args:
            a (int): First (most significant) octet.
            b (int): Second octet.
            c (int): Third octet.
            d (int): Fourth (least significant) octet.

        Returns:
            Ipv4Addr: The constructed IPv4 address.
        """
        return cls(a, b, c, d)

    @classmethod
    def from_str(cls, s: str) -> Ipv4Addr:  # type: ignore
        """Parse a dotted-quad string into an Ipv4Addr.

        Args:
            s (str): A string like ``"192.168.0.1"``.

        Returns:
            Ipv4Addr: The parsed address.

        Raises:
            ValueError: If the string does not contain exactly four
                dot-separated integer parts.
        """
        parts = s.split(".")
        if len(parts) != 4:
            raise ValueError(f"invalid IPv4 address: {s}")
        return cls(*[int(p) for p in parts])

    @classmethod
    def from_bytes(cls, bytes: bytes | bytearray) -> Ipv4Addr:  # type: ignore
        """Create an IPv4 address from exactly four bytes.

        Args:
            bytes (bytes | bytearray): Exactly four bytes in network order.

        Returns:
            Ipv4Addr: The constructed address.

        Raises:
            ValueError: If fewer or more than four bytes are provided.
        """
        if len(bytes) != 4:
            raise ValueError("IPv4 address must be 4 bytes")
        return cls(bytes[0], bytes[1], bytes[2], bytes[3])

    @classmethod
    def localhost(cls) -> Ipv4Addr:  # type: ignore
        """Return the loopback address ``127.0.0.1``.

        Returns:
            Ipv4Addr: The localhost loopback address.
        """
        return cls(127, 0, 0, 1)

    @classmethod
    def unspecified(cls) -> Ipv4Addr:  # type: ignore
        """Return the unspecified address ``0.0.0.0``.

        Returns:
            Ipv4Addr: The catch-all unspecified address.
        """
        return cls(0, 0, 0, 0)

    @classmethod
    def broadcast(cls) -> Ipv4Addr:  # type: ignore
        """Return the broadcast address ``255.255.255.255``.

        Returns:
            Ipv4Addr: The all-hosts broadcast address.
        """
        return cls(255, 255, 255, 255)

    @classmethod
    def loopback(cls) -> Ipv4Addr:  # type: ignore
        """Return the loopback address ``127.0.0.1``.

        Alias for :meth:`localhost`.

        Returns:
            Ipv4Addr: The localhost loopback address.
        """
        return cls(127, 0, 0, 1)

    def octets(self) -> tuple[int, int, int, int]:
        """Return the address as a tuple of four octets.

        Returns:
            tuple[int, int, int, int]: The four octets in network order.
        """
        return self._octets

    def to_str(self) -> str:  # type: ignore
        """Return the address in dotted-quad notation.

        Returns:
            str: The address as ``"a.b.c.d"``.
        """
        return ".".join(str(o) for o in self._octets)

    def to_bytes(self) -> bytes:  # type: ignore
        """Return the address as four raw bytes in network order.

        Returns:
            bytes: The packed octets.
        """
        return bytes(self._octets)

    def is_loopback(self) -> bool:  # type: ignore
        """Return whether the address is in the ``127.0.0.0/8`` loopback range.

        Returns:
            bool: True if the first octet is ``127``.
        """
        return self._octets[0] == 127

    def is_unspecified(self) -> bool:  # type: ignore
        """Return whether the address is ``0.0.0.0``.

        Returns:
            bool: True if all octets are zero.
        """
        return self._octets == (0, 0, 0, 0)

    def is_broadcast(self) -> bool:  # type: ignore
        """Return whether the address is ``255.255.255.255``.

        Returns:
            bool: True if all octets are ``255``.
        """
        return self._octets == (255, 255, 255, 255)

    def is_multicast(self) -> bool:  # type: ignore
        """Return whether the address is in the ``224.0.0.0/4`` multicast range.

        Returns:
            bool: True if the first octet's top four bits are ``1110``.
        """
        return (self._octets[0] & 0xF0) == 0xE0

    def is_private(self) -> bool:  # type: ignore
        """Return whether the address is in a private RFC 1918 range.

        Covers ``10.0.0.0/8``, ``172.16.0.0/12``, and ``192.168.0.0/16``.

        Returns:
            bool: True if the address is private.
        """
        return (
            self._octets[0] == 10
            or (self._octets[0] == 172 and 16 <= self._octets[1] <= 31)
            or (self._octets[0] == 192 and self._octets[1] == 168)
        )

    def is_link_local(self) -> bool:  # type: ignore
        """Return whether the address is in the ``169.254.0.0/16`` link-local range.

        Returns:
            bool: True if the address is link-local.
        """
        return self._octets[0] == 169 and self._octets[1] == 254

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Ipv4Addr):
            return self._octets == other._octets
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Ipv4Addr):
            return self._octets != other._octets
        return NotImplemented

    def __lt__(self, other: Ipv4Addr) -> bool:
        if isinstance(other, Ipv4Addr):
            return self._octets < other._octets
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._octets)

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return f"Ipv4Addr({self.to_str()!r})"


class Ipv6Addr:
    """An IPv6 address stored as eight 16-bit segments.

    Comparable, hashable, and immutable. Supports construction from
    segments, standard textual notation, or raw bytes, and provides
    common classification and conversion predicates.

    Examples:
        >>> addr = Ipv6Addr.localhost()
        >>> str(addr)
        '::1'
        >>> Ipv6Addr.from_str("::1") == addr
        True
    """

    __slots__ = ("_segments",)

    def __init__(self, *segments: int) -> None:
        """Construct an IPv6 address from eight 16-bit segments.

        With no arguments the address defaults to all zeros.

        Args:
            *segments (int): Either zero segments (yielding ``::``) or
                exactly eight 16-bit segments.

        Raises:
            ValueError: If a number other than zero or eight segments is
                provided.
        """
        if len(segments) == 0:
            self._segments = (0,) * 8
        elif len(segments) == 8:
            self._segments = tuple(segments)
        else:
            raise ValueError("IPv6 address must have 0 or 8 segments")

    @classmethod
    def new(cls, a: int, b: int, c: int, d: int, e: int, f: int, g: int, h: int) -> Ipv6Addr:  # type: ignore
        """Create an IPv6 address from eight 16-bit segments.

        Args:
            a (int): First (most significant) segment.
            b (int): Second segment.
            c (int): Third segment.
            d (int): Fourth segment.
            e (int): Fifth segment.
            f (int): Sixth segment.
            g (int): Seventh segment.
            h (int): Eighth (least significant) segment.

        Returns:
            Ipv6Addr: The constructed address.
        """
        return cls(a, b, c, d, e, f, g, h)

    @classmethod
    def from_str(cls, s: str) -> Ipv6Addr:  # type: ignore
        """Parse a standard IPv6 textual form into an Ipv6Addr.

        Accepts notations such as ``"::1"``, ``"fe80::1"``, or
        ``"2001:db8::1"``.

        Args:
            s (str): The IPv6 address string.

        Returns:
            Ipv6Addr: The parsed address.

        Raises:
            ValueError: If the string is not a valid IPv6 address.
        """
        import ipaddress
        addr = ipaddress.IPv6Address(s)
        b = addr.packed
        segments = []
        for i in range(0, 16, 2):
            segments.append((b[i] << 8) | b[i + 1])
        return cls(*segments)

    @classmethod
    def from_bytes(cls, data: bytes | bytearray) -> Ipv6Addr:  # type: ignore
        """Create an IPv6 address from exactly 16 bytes.

        Args:
            data (bytes | bytearray): Exactly 16 bytes in network order.

        Returns:
            Ipv6Addr: The constructed address.

        Raises:
            ValueError: If fewer or more than 16 bytes are provided.
        """
        if len(data) != 16:
            raise ValueError("IPv6 address must be 16 bytes")
        segments = []
        for i in range(0, 16, 2):
            segments.append((data[i] << 8) | data[i + 1])
        return cls(*segments)

    @classmethod
    def localhost(cls) -> Ipv6Addr:  # type: ignore
        """Return the loopback address ``::1``.

        Returns:
            Ipv6Addr: The loopback address.
        """
        return cls(0, 0, 0, 0, 0, 0, 0, 1)

    @classmethod
    def unspecified(cls) -> Ipv6Addr:  # type: ignore
        """Return the unspecified address ``::`` (all zeros).

        Returns:
            Ipv6Addr: The unspecified address.
        """
        return cls(0, 0, 0, 0, 0, 0, 0, 0)

    @classmethod
    def loopback(cls) -> Ipv6Addr:  # type: ignore
        """Return the loopback address ``::1``.

        Alias for :meth:`localhost`.

        Returns:
            Ipv6Addr: The loopback address.
        """
        return cls(0, 0, 0, 0, 0, 0, 0, 1)

    @classmethod
    def multicast(cls, scope: int = 2) -> Ipv6Addr:  # type: ignore
        """Return the multicast address for the given scope.

        Args:
            scope (int): The 4-bit scope field embedded in the first
                segment. Defaults to ``2`` (link-local).

        Returns:
            Ipv6Addr: A multicast address of the form ``ffXx::``.
        """
        return cls(0xFF00 | scope, 0, 0, 0, 0, 0, 0, 0)

    @classmethod
    def link_local(cls) -> Ipv6Addr:  # type: ignore
        """Return the link-local address ``fe80::1``.

        Returns:
            Ipv6Addr: A representative link-local unicast address.
        """
        return cls(0xFE80, 0, 0, 0, 0, 0, 0, 0x0001)

    def segments(self) -> tuple[int, ...]:
        """Return the address as a tuple of eight 16-bit segments.

        Returns:
            tuple[int, ...]: The eight segments in network order.
        """
        return self._segments

    def to_str(self) -> str:  # type: ignore
        """Return the address in standard colon-separated textual notation.

        Returns:
            str: The canonical compressed notation, e.g. ``"::1"``.
        """
        import ipaddress
        b = bytearray(16)
        for i, seg in enumerate(self._segments):
            b[i * 2] = seg >> 8
            b[i * 2 + 1] = seg & 0xFF
        return str(ipaddress.IPv6Address(bytes(b)))

    def to_bytes(self) -> bytes:  # type: ignore
        """Return the address as 16 raw bytes in network order.

        Returns:
            bytes: The packed segments.
        """
        b = bytearray(16)
        for i, seg in enumerate(self._segments):
            b[i * 2] = seg >> 8
            b[i * 2 + 1] = seg & 0xFF
        return bytes(b)

    def is_loopback(self) -> bool:  # type: ignore
        """Return whether the address is the loopback address ``::1``.

        Returns:
            bool: True if the address is ``::1``.
        """
        return self._segments == (0, 0, 0, 0, 0, 0, 0, 1)

    def is_unspecified(self) -> bool:  # type: ignore
        """Return whether the address is the unspecified address ``::``.

        Returns:
            bool: True if all segments are zero.
        """
        return self._segments == (0, 0, 0, 0, 0, 0, 0, 0)

    def is_multicast(self) -> bool:  # type: ignore
        """Return whether the address is in the ``ff00::/8`` multicast range.

        Returns:
            bool: True if the address is multicast.
        """
        return (self._segments[0] & 0xFF00) == 0xFF00

    def is_unicast_link_local(self) -> bool:  # type: ignore
        """Return whether the address is in the ``fe80::/10`` unicast link-local range.

        Returns:
            bool: True if the address is unicast link-local.
        """
        return (self._segments[0] & 0xFFC0) == 0xFE80

    def to_ipv4_mapped(self) -> Ipv4Addr:  # type: ignore
        """Convert an IPv4-mapped IPv6 address to its equivalent Ipv4Addr.

        The IPv4-mapped form is ``::ffff:a.b.c.d`` or ``::a.b.c.d``,
        where the low 32 bits encode the IPv4 address.

        Returns:
            Ipv4Addr: The embedded IPv4 address.

        Raises:
            ValueError: If the address is not IPv4-mapped.
        """
        if self._segments[0] == 0 and self._segments[1] == 0 and self._segments[2] == 0 and self._segments[3] == 0 and self._segments[4] == 0:
            return Ipv4Addr(
                (self._segments[6] >> 8) & 0xFF,
                self._segments[6] & 0xFF,
                (self._segments[7] >> 8) & 0xFF,
                self._segments[7] & 0xFF,
            )
        raise ValueError("not an IPv4-mapped address")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Ipv6Addr):
            return self._segments == other._segments
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Ipv6Addr):
            return self._segments != other._segments
        return NotImplemented

    def __lt__(self, other: Ipv6Addr) -> bool:
        if isinstance(other, Ipv6Addr):
            return self._segments < other._segments
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._segments)

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return f"Ipv6Addr({self.to_str()!r})"


class IpAddr:
    """A type-erased IP address that is either IPv4 or IPv6.

    Holds exactly one of an :class:`Ipv4Addr` or :class:`Ipv6Addr`.
    Use :meth:`v4`, :meth:`v6`, or :meth:`from_str` to construct, then
    inspect with :meth:`is_ipv4`/:meth:`is_ipv6`.

    Examples:
        >>> IpAddr.from_str("127.0.0.1").is_ipv4()
        True
        >>> str(IpAddr.from_str("::1"))
        '::1'
    """

    __slots__ = ("_v4", "_v6")

    def __init__(self, v4: Ipv4Addr | None = None, v6: Ipv6Addr | None = None) -> None:
        if v4 is not None and v6 is not None:
            raise ValueError("IpAddr cannot be both v4 and v6")
        self._v4 = v4
        self._v6 = v6

    @classmethod
    def v4(cls, addr: Ipv4Addr) -> IpAddr:
        """Wrap an Ipv4Addr as an IpAddr.

        Args:
            addr (Ipv4Addr): The IPv4 address to wrap.

        Returns:
            IpAddr: An IpAddr containing the IPv4 address.
        """
        return cls(v4=addr)

    @classmethod
    def v6(cls, addr: Ipv6Addr) -> IpAddr:
        """Wrap an Ipv6Addr as an IpAddr.

        Args:
            addr (Ipv6Addr): The IPv6 address to wrap.

        Returns:
            IpAddr: An IpAddr containing the IPv6 address.
        """
        return cls(v6=addr)

    @classmethod
    def from_str(cls, s: str) -> IpAddr:
        """Parse a string as either an IPv4 or IPv6 address.

        IPv4 is attempted first; if that fails the string is parsed as
        IPv6.

        Args:
            s (str): The address string, e.g. ``"192.168.0.1"`` or
                ``"::1"``.

        Returns:
            IpAddr: The parsed address.

        Raises:
            ValueError: If the string is neither a valid IPv4 nor IPv6
                address.
        """
        try:
            return cls.v4(Ipv4Addr.from_str(s))
        except ValueError:
            pass
        return cls.v6(Ipv6Addr.from_str(s))

    def is_ipv4(self) -> bool:  # type: ignore
        """Return whether this address is IPv4.

        Returns:
            bool: True if the address is IPv4.
        """
        return self._v4 is not None

    def is_ipv6(self) -> bool:  # type: ignore
        """Return whether this address is IPv6.

        Returns:
            bool: True if the address is IPv6.
        """
        return self._v6 is not None

    def as_ipv4(self) -> Ipv4Addr | None:
        """Return the inner Ipv4Addr, or None if this is not IPv4.

        Returns:
            Ipv4Addr | None: The IPv4 address, or None.
        """
        return self._v4

    def as_ipv6(self) -> Ipv6Addr | None:  # type: ignore
        """Return the inner Ipv6Addr, or None if this is not IPv6.

        Returns:
            Ipv6Addr | None: The IPv6 address, or None.
        """
        return self._v6

    def to_ipv4(self) -> Ipv4Addr | None:  # type: ignore
        """Return the Ipv4Addr if present, or None.

        Alias for :meth:`as_ipv4`.

        Returns:
            Ipv4Addr | None: The IPv4 address, or None.
        """
        return self._v4

    def to_ipv6(self) -> Ipv6Addr | None:  # type: ignore
        """Return the Ipv6Addr if present, or None.

        Alias for :meth:`as_ipv6`.

        Returns:
            Ipv6Addr | None: The IPv6 address, or None.
        """
        return self._v6

    def is_loopback(self) -> bool:  # type: ignore
        """Return whether the contained address is a loopback address.

        Returns:
            bool: True if the address is loopback, or False if neither
                variant is set.
        """
        if self._v4:
            return self._v4.is_loopback()
        if self._v6:
            return self._v6.is_loopback()
        return False

    def __eq__(self, other: object) -> bool:
        if isinstance(other, IpAddr):
            return self._v4 == other._v4 and self._v6 == other._v6
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, IpAddr):
            return self._v4 != other._v4 or self._v6 != other._v6
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._v4, self._v6))

    def __str__(self) -> str:
        if self._v4:
            return str(self._v4)
        return str(self._v6)

    def __repr__(self) -> str:
        if self._v4:
            return f"IpAddr::V4({self._v4!r})"
        return f"IpAddr::V6({self._v6!r})"


class SocketAddr:
    """A socket address combining an IP address and a port number.

    Wraps an :class:`IpAddr` together with a 16-bit port. Provides
    constructors for IPv4 and IPv6, parsing from textual form, and
    accessors for inspecting and mutating the components.

    Examples:
        >>> addr = SocketAddr.from_str("127.0.0.1:8080")
        >>> addr.port()
        8080
        >>> str(addr)
        '127.0.0.1:8080'
    """

    __slots__ = ("_ip", "_port")

    def __init__(self, ip: IpAddr, port: int) -> None:
        self._ip = ip
        self._port = port

    @classmethod
    def new(cls, ip: IpAddr, port: int) -> SocketAddr:
        """Create a socket address from an IP address and port.

        Args:
            ip (IpAddr): The IP address.
            port (int): The port number.

        Returns:
            SocketAddr: The constructed socket address.
        """
        return cls(ip, port)

    @classmethod
    def from_str(cls, s: str) -> SocketAddr:
        """Parse a socket address from its textual form.

        Accepts ``"host:port"`` for IPv4 and ``"[ipv6]:port"`` for IPv6,
        e.g. ``"127.0.0.1:8080"`` or ``"[::1]:8080"``.

        Args:
            s (str): The socket address string.

        Returns:
            SocketAddr: The parsed socket address.

        Raises:
            ValueError: If the string is not a well-formed socket address.
        """
        if s.startswith("["):
            bracket = s.find("]")
            if bracket < 0:
                raise ValueError(f"invalid socket address: {s}")
            ip_str = s[1:bracket]
            rest = s[bracket + 1:]
            if not rest.startswith(":"):
                raise ValueError(f"invalid socket address: {s}")
            port = int(rest[1:])
            return cls(IpAddr.v6(Ipv6Addr.from_str(ip_str)), port)
        colon = s.rfind(":")
        if colon < 0:
            raise ValueError(f"invalid socket address: {s}")
        ip_str = s[:colon]
        port = int(s[colon + 1:])
        return cls(IpAddr.from_str(ip_str), port)

    @classmethod
    def new_v4(cls, ip: Ipv4Addr, port: int) -> SocketAddr:
        """Create a socket address from an IPv4 address and port.

        Args:
            ip (Ipv4Addr): The IPv4 address.
            port (int): The port number.

        Returns:
            SocketAddr: The constructed IPv4 socket address.
        """
        return cls(IpAddr.v4(ip), port)

    @classmethod
    def new_v6(cls, ip: Ipv6Addr, port: int) -> SocketAddr:
        """Create a socket address from an IPv6 address and port.

        Args:
            ip (Ipv6Addr): The IPv6 address.
            port (int): The port number.

        Returns:
            SocketAddr: The constructed IPv6 socket address.
        """
        return cls(IpAddr.v6(ip), port)

    def ip(self) -> IpAddr:  # type: ignore
        """Return the IP address portion.

        Returns:
            IpAddr: The IP address.
        """
        return self._ip

    def port(self) -> int:
        """Return the port number portion.

        Returns:
            int: The port number.
        """
        return self._port

    def is_ipv4(self) -> bool:  # type: ignore
        """Return whether the underlying IP address is IPv4.

        Returns:
            bool: True if the IP is IPv4.
        """
        return self._ip.is_ipv4()

    def is_ipv6(self) -> bool:  # type: ignore
        """Return whether the underlying IP address is IPv6.

        Returns:
            bool: True if the IP is IPv6.
        """
        return self._ip.is_ipv6()

    def set_ip(self, ip: IpAddr) -> None:
        """Replace the IP address portion.

        Args:
            ip (IpAddr): The new IP address.
        """
        self._ip = ip

    def set_port(self, port: int) -> None:  # type: ignore
        """Replace the port number.

        Args:
            port (int): The new port number.
        """
        self._port = port

    def to_socket_addr(self) -> tuple[str, int]:  # type: ignore
        """Return a ``(host, port)`` tuple for low-level socket APIs.

        Returns:
            tuple[str, int]: The host as a string and the port.
        """
        return (str(self._ip), self._port)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SocketAddr):
            return self._ip == other._ip and self._port == other._port
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, SocketAddr):
            return self._ip != other._ip or self._port != other._port
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._ip, self._port))

    def __str__(self) -> str:
        if self._ip.is_ipv6():
            return f"[{self._ip}]:{self._port}"
        return f"{self._ip}:{self._port}"

    def __repr__(self) -> str:
        return f"SocketAddr({self})"
