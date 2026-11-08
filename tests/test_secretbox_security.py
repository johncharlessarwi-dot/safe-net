"""Regression tests for encrypted tenant credential handling."""
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

import secretbox


class SecretboxSecurityTests(unittest.TestCase):
    def test_valid_ciphertext_round_trip(self):
        with patch.object(secretbox.Config, 'DATA_ENCRYPTION_KEY', Fernet.generate_key()):
            self.assertEqual(secretbox.decrypt(secretbox.encrypt('test-token')), 'test-token')

    def test_invalid_utf8_plaintext_fails_closed(self):
        key = Fernet.generate_key()
        with patch.object(secretbox.Config, 'DATA_ENCRYPTION_KEY', key):
            bad_plaintext = Fernet(key).encrypt(b'\\xff').decode()
            self.assertEqual(secretbox.decrypt(bad_plaintext), '')


if __name__ == '__main__':
    unittest.main()
