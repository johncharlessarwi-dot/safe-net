import hashlib
import hmac
import os
import unittest

os.environ.setdefault('DB_PASSWORD', 'unit-test-only-password')

import snippe


class SnippeWebhookSignatureTests(unittest.TestCase):
    KEY = 'test-only-webhook-signing-key'
    BODY = b'{"event":"payment.completed"}'
    TIMESTAMP = '1000'

    def signature(self, body=BODY, timestamp=TIMESTAMP):
        return hmac.new(self.KEY.encode(), timestamp.encode() + b'.' + body, hashlib.sha256).hexdigest()

    def test_accepts_correct_signature_at_epoch_zero_offset(self):
        self.assertTrue(snippe.verify_webhook(self.BODY, self.TIMESTAMP, self.signature(), self.KEY, now=1000))
        self.assertTrue(snippe.verify_webhook(self.BODY, '0', self.signature(timestamp='0'), self.KEY, now=0))

    def test_rejects_tampered_or_replayed_webhooks(self):
        self.assertFalse(snippe.verify_webhook(self.BODY + b'!', self.TIMESTAMP, self.signature(), self.KEY, now=1000))
        self.assertFalse(snippe.verify_webhook(self.BODY, self.TIMESTAMP, self.signature(), self.KEY, now=1401))

    def test_rejects_malformed_inputs_without_raising(self):
        cases = ((b'\xff', self.TIMESTAMP, self.signature()),
                 ({'event': 'payment.completed'}, self.TIMESTAMP, self.signature()),
                 (self.BODY, self.TIMESTAMP, 1234),
                 (self.BODY, 'bad-timestamp', self.signature()))
        for body, timestamp, signature in cases:
            with self.subTest(body=body, timestamp=timestamp):
                self.assertFalse(snippe.verify_webhook(body, timestamp, signature, self.KEY, now=1000))


if __name__ == '__main__':
    unittest.main()
