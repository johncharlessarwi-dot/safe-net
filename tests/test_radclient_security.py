"""Defensive validation for outgoing RADIUS disconnect packets."""
import unittest
from unittest.mock import patch

import radclient


class RadiusPacketSecurityTests(unittest.TestCase):
    def test_rejects_oversized_attribute(self):
        with self.assertRaises(ValueError):
            radclient._attr(radclient.A_USER_NAME, b'a' * 254)

if __name__ == '__main__':
    unittest.main()
