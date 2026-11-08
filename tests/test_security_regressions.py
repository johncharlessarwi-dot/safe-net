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
            snippe.webhook_reference({'data': {'reference': 'PAY\x00spoof'}})

    def test_webhook_reference_rejects_newline(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 'PAY\nspoof'}})

    def test_webhook_reference_rejects_carriage_return(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 'PAY\rspoof'}})

    def test_webhook_reference_rejects_tab(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 'PAY\tspoof'}})

    def test_webhook_reference_rejects_oversized_identifier(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': {'reference': 'x' * 65}})

    def test_webhook_reference_accepts_maximum_length(self):
        self.assertEqual(snippe.webhook_reference({'data': {'reference': 'x' * 64}}), 'x' * 64)

    def test_webhook_reference_rejects_missing_data_object(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference({'data': 'PAY-001'})

    def test_webhook_reference_rejects_non_object_event(self):
        with self.assertRaises(ValueError):
            snippe.webhook_reference(['PAY-001'])

    def test_signature_rejects_non_hexadecimal_digest(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '1000', 'g' * 64, self.KEY, now=1000))

    def test_signature_rejects_truncated_digest(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '1000', self.signature()[:32], self.KEY, now=1000))

    def test_signature_rejects_oversized_digest(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '1000', self.signature() + '00', self.KEY, now=1000))

    def test_signature_accepts_uppercase_hex(self):
        self.assertTrue(snippe.verify_webhook(self.BODY, '1000', self.signature().upper(), self.KEY, now=1000))

    def test_signature_rejects_huge_event_body(self):
        body = b'x' * 1_048_577
        self.assertFalse(snippe.verify_webhook(body, '1000', self.signature(body), self.KEY, now=1000))

    def test_signature_accepts_event_body_under_limit(self):
        self.assertTrue(snippe.verify_webhook(self.BODY, '1000', self.signature(), self.KEY, now=1000))

    def test_signature_rejects_excessive_signing_key(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '1000', self.signature(), 'k' * 4097, now=1000))

    def test_signature_rejects_timestamp_with_spaces(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, ' 1000 ', self.signature(), self.KEY, now=1000))

    def test_signature_rejects_timestamp_with_newline(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '1000\n', self.signature(), self.KEY, now=1000))

    def test_signature_rejects_oversized_timestamp(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '1' * 17, self.signature(), self.KEY, now=1000))

    def test_signature_rejects_nonfinite_clock(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '1000', self.signature(), self.KEY, now=float('nan')))

    def test_signature_rejects_infinite_clock(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '1000', self.signature(), self.KEY, now=float('inf')))

    def test_signature_rejects_negative_timestamp(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '-1000', self.signature(timestamp='-1000'), self.KEY, now=-1000))

    def test_signature_rejects_boolean_clock(self):
        self.assertFalse(snippe.verify_webhook(self.BODY, '1000', self.signature(), self.KEY, now=True))

    def test_error_redaction_accepts_numeric_extra_secrets(self):
        self.assertIsInstance(safetext.clean('provider unavailable', extra_secrets=[12345, None]), str)

    def test_error_redaction_masks_standalone_extra_secret(self):
        secret = 'private-special-credential'
        self.assertNotIn(secret, safetext.clean('error ' + secret, extra_secrets=secret))

    def test_error_redaction_masks_bearer_tokens(self):
        self.assertNotIn('abc123secret', safetext.clean('Bearer abc123secret'))

    def test_error_redaction_limits_huge_message(self):
        self.assertLessEqual(len(safetext.clean('x' * 50_000)), 16_384)

    def test_clickpesa_ignores_invalid_payment_rows(self):
        with patch.object(clickpesa, '_auth_header', return_value='Bearer test'), patch.object(clickpesa, '_request', return_value=[None, 'bad']):
            self.assertIsNone(clickpesa.query_payment('ref-1'))

    def test_clickpesa_ignores_invalid_payout_rows(self):
        with patch.object(clickpesa, '_auth_header', return_value='Bearer test'), patch.object(clickpesa, '_request', return_value=[None, 'bad']):
            self.assertIsNone(clickpesa.query_payout('ref-1'))

    def test_clickpesa_keeps_valid_payment_row(self):
        with patch.object(clickpesa, '_auth_header', return_value='Bearer test'), patch.object(clickpesa, '_request', return_value=[None, {'status': 'SUCCESS', 'reference': 'ref-1'}]):
            self.assertEqual(clickpesa.query_payment('ref-1')['reference'], 'ref-1')
