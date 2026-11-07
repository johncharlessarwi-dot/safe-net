import hashlib
import hmac
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('DB_PASSWORD', 'unit-test-only-password')

import snippe
import clickpesa
import safetext


class SecurityRegressionTests(unittest.TestCase):
    KEY = 'test-only-webhook-signing-key'
    BODY = b'{"event":"payment.completed"}'

    def signature(self, body=None, timestamp='1000'):
        body = self.BODY if body is None else body
        return hmac.new(self.KEY.encode(), timestamp.encode() + b'.' + body, hashlib.sha256).hexdigest()


    def test_webhook_reference_rejects_numeric_identifiers(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 12345}})
