"""Regression tests for encrypted tenant credential handling."""
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

import secretbox


class SecretboxSecurityTests(unittest.TestCase):
    def test_rejects_oversized_plaintext(self):
        with self.assertRaises(ValueError):
            secretbox.encrypt('a' * 16_385)

    def test_rejects_invalid_unicode_plaintext(self):
        with self.assertRaises(ValueError):
            secretbox.encrypt(chr(0xD800))

    def test_valid_ciphertext_round_trip(self):
        with patch.object(secretbox.Config, 'DATA_ENCRYPTION_KEY', Fernet.generate_key()):
            self.assertEqual(secretbox.decrypt(secretbox.encrypt('test-token')), 'test-token')

    def test_non_string_ciphertexts_fail_closed(self):
        for token in (True, 123, [], {}, b'raw-bytes'):
            with self.subTest(token=token):
                self.assertEqual(secretbox.decrypt(token), '')

    def test_oversized_ciphertexts_fail_closed(self):
        self.assertEqual(secretbox.decrypt('A' * 65_537), '')

    def test_invalid_utf8_plaintext_fails_closed(self):
        key = Fernet.generate_key()
        with patch.object(secretbox.Config, 'DATA_ENCRYPTION_KEY', key):
            bad_plaintext = Fernet(key).encrypt(b'\xff').decode()
            self.assertEqual(secretbox.decrypt(bad_plaintext), '')


if __name__ == '__main__':
    unittest.main()
