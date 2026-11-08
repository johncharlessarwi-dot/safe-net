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
    if len(value) > 253:
        raise ValueError('RADIUS attribute exceeds maximum payload length')
    return struct.pack('!BB', kind, len(value) + 2) + value


def disconnect(nas_ip, secret, username, session_id=None, framed_ip=None, port=3799, timeout=3.0, tries=2):
    """Returns (ok, message)."""
    if isinstance(tries, bool) or not isinstance(tries, int) or not 1 <= tries <= 5:
        return False, 'invalid retries'
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 30:
        return False, 'invalid timeout'
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        return False, 'invalid UDP port'
    if not isinstance(secret, str) or not secret or len(secret) > 4096:
        return False, 'invalid shared secret'
    if not isinstance(username, str) or not username or len(username.encode()) > 253 or any(ord(c) < 32 or ord(c) == 127 for c in username):
        return False, 'invalid username'
    try:
        secret_bytes = secret.encode('utf-8')
    except UnicodeError:
        return False, 'invalid shared secret'
    attrs = _attr(A_USER_NAME, username.encode())
    if session_id is not None:
        if not isinstance(session_id, str) or not session_id or len(session_id.encode()) > 253 or any(ord(c) < 32 or ord(c) == 127 for c in session_id):
            return False, 'invalid session id'
        attrs += _attr(A_ACCT_SESSION_ID, session_id.encode())
    if framed_ip is not None:
        try:
            attrs += _attr(A_FRAMED_IP, socket.inet_aton(framed_ip))
        except (OSError, TypeError):
            return False, 'invalid framed IP'
    ident = secrets.randbelow(256)
    header = struct.pack('!BBH', DISCONNECT_REQUEST, ident, 20 + len(attrs))
    authenticator = hashlib.md5(header + b'\0' * 16 + attrs + secret_bytes).digest()
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
                expected = hashlib.md5(reply[:4] + authenticator + reply[20:] + secret_bytes).digest()
                if expected != reply[4:20]:
                    return False, 'reply with wrong secret'
                return (True, 'disconnected') if reply[0] == DISCONNECT_ACK else (False, 'router refused (NAK)')
    except OSError as e:
        return False, str(e)
    return False, 'no reply from router'
