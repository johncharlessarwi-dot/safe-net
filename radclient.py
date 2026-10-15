"""RADIUS Disconnect-Request (RFC 5176) to a router, e.g. MikroTik over the VPN.

Standard library only. The router must accept incoming RADIUS on port 3799
(MikroTik: /radius incoming set accept=yes).
"""
import hashlib
import secrets
import socket
import struct

DISCONNECT_REQUEST, DISCONNECT_ACK, DISCONNECT_NAK = 40, 41, 42
A_USER_NAME, A_FRAMED_IP, A_ACCT_SESSION_ID = 1, 8, 44


def _attr(kind, value):
    return struct.pack('!BB', kind, len(value) + 2) + value


def disconnect(nas_ip, secret, username, session_id=None, framed_ip=None, port=3799, timeout=3.0, tries=2):
    """Returns (ok, message)."""
    attrs = _attr(A_USER_NAME, username.encode()[:253])
    if session_id:
        attrs += _attr(A_ACCT_SESSION_ID, session_id.encode()[:253])
    if framed_ip:
        try:
            attrs += _attr(A_FRAMED_IP, socket.inet_aton(framed_ip))
        except OSError:
            pass
    ident = secrets.randbelow(256)
    header = struct.pack('!BBH', DISCONNECT_REQUEST, ident, 20 + len(attrs))
    authenticator = hashlib.md5(header + b'\0' * 16 + attrs + secret.encode()).digest()
    packet = header + authenticator + attrs
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            for _ in range(tries):
                sock.sendto(packet, (nas_ip, port))
                try:
                    reply, _ = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                if len(reply) < 20 or reply[1] != ident:
                    continue
                expected = hashlib.md5(reply[:4] + authenticator + reply[20:] + secret.encode()).digest()
                if expected != reply[4:20]:
                    return False, 'reply with wrong secret'
                return (True, 'disconnected') if reply[0] == DISCONNECT_ACK else (False, 'router refused (NAK)')
    except OSError as e:
        return False, str(e)
    return False, 'no reply from router'
