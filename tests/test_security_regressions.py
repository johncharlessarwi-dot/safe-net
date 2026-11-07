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

    def test_webhook_reference_rejects_boolean_identifiers(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': True}})

    def test_webhook_reference_rejects_list_identifiers(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': ['PAY']}})

    def test_webhook_reference_rejects_dict_identifiers(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': {'id': 'PAY'}}})

    def test_webhook_reference_allows_missing_identifier(self):
        self.assertEqual(snippe.webhook_reference({'data': {}}), '')

    def test_webhook_reference_allows_empty_identifier(self):
        self.assertEqual(snippe.webhook_reference({'data': {'reference': ''}}), '')

    def test_webhook_reference_allows_plain_identifier(self):
        self.assertEqual(snippe.webhook_reference({'data': {'reference': 'PAY-001'}}), 'PAY-001')

    def test_webhook_reference_rejects_null_byte(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 'PAY\\x00spoof'}})

    def test_webhook_reference_rejects_newline(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 'PAY\\nspoof'}})

    def test_webhook_reference_rejects_carriage_return(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 'PAY\\rspoof'}})

    def test_webhook_reference_rejects_tab(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 'PAY\\tspoof'}})

    def test_webhook_reference_rejects_oversized_identifier(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 'x' * 65}})

    def test_webhook_reference_accepts_maximum_length(self):
        self.assertEqual(snippe.webhook_reference({'data': {'reference': 'x' * 64}}), 'x' * 64)

    def test_webhook_reference_rejects_missing_data_object(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': 'PAY-001'})
