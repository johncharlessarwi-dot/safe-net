"""Defensive validation for outgoing RADIUS disconnect packets."""
import unittest
from unittest.mock import patch

import radclient


class RadiusPacketSecurityTests(unittest.TestCase):
    def test_rejects_oversized_attribute(self):
        with self.assertRaises(ValueError):
            radclient._attr(radclient.A_USER_NAME, b'a' * 254)

    def test_rejects_oversized_username_without_socket(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            ok, message = radclient.disconnect('127.0.0.1', 'testsecret', 'u' * 254)
        self.assertFalse(ok)
        self.assertEqual(message, 'invalid username')
        socket_factory.assert_not_called()

    def test_rejects_oversized_session_id_without_socket(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            ok, message = radclient.disconnect('127.0.0.1', 'testsecret', 'user', session_id='s' * 254)
        self.assertFalse(ok)
        self.assertEqual(message, 'invalid session id')
        socket_factory.assert_not_called()
    def test_rejects_empty_shared_secret_without_socket(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            ok, message = radclient.disconnect('127.0.0.1', '', 'username')
        self.assertFalse(ok)
        self.assertEqual(message, 'invalid shared secret')
        socket_factory.assert_not_called()
    def test_rejects_username_control_characters(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            ok, _ = radclient.disconnect('127.0.0.1', 'testsecret', 'alice' + chr(0) + 'bob')
        self.assertFalse(ok)
        socket_factory.assert_not_called()
    def test_rejects_invalid_udp_port(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            for port in (0, 65536, True, '3799'):
                with self.subTest(port=port):
                    self.assertEqual(radclient.disconnect('127.0.0.1', 'testsecret', 'user', port=port)[0], False)
        socket_factory.assert_not_called()
    def test_rejects_session_id_control_characters(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            ok, message = radclient.disconnect('127.0.0.1', 'testsecret', 'user', session_id='abc' + chr(10) + 'unsafe')
        self.assertFalse(ok)
        self.assertEqual(message, 'invalid session id')
        socket_factory.assert_not_called()
    def test_rejects_invalid_timeouts_without_socket(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            for timeout in (0, -1, True, '3', float('nan'), float('inf')):
                with self.subTest(timeout=timeout):
                    self.assertFalse(radclient.disconnect('127.0.0.1', 'testsecret', 'user', timeout=timeout)[0])
        socket_factory.assert_not_called()
    def test_rejects_invalid_retry_counts_without_socket(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            for tries in (0, -1, 6, True, '2', 1.5):
                with self.subTest(tries=tries):
                    self.assertFalse(radclient.disconnect('127.0.0.1', 'testsecret', 'user', tries=tries)[0])
        socket_factory.assert_not_called()
    def test_rejects_malformed_framed_ip_without_socket(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            ok, message = radclient.disconnect('127.0.0.1', 'testsecret', 'user', framed_ip='not-an-ip')
        self.assertFalse(ok)
        self.assertEqual(message, 'invalid framed IP')
        socket_factory.assert_not_called()

    def test_rejects_oversized_shared_secret_without_socket(self):
        with patch.object(radclient.socket, 'socket') as socket_factory:
            ok, message = radclient.disconnect('127.0.0.1', 's' * 4097, 'user')
        self.assertFalse(ok)
        self.assertEqual(message, 'invalid shared secret')
        socket_factory.assert_not_called()

if __name__ == '__main__':
    unittest.main()
