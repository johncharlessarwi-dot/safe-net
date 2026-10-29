import os
import unittest

# Config requires a database password at import time; keep tests self-contained.
os.environ.setdefault('DB_PASSWORD', 'unit-test-only-password')

import snippe


class SnippeWebhookPayloadTests(unittest.TestCase):
    def test_extracts_reference_from_valid_event(self):
        self.assertEqual(
            snippe.webhook_reference({"data": {"reference": "PAY-123"}}),
            "PAY-123",
        )

    def test_missing_reference_is_acknowledged_as_empty(self):
        self.assertEqual(snippe.webhook_reference({"data": {}}), "")

    def test_rejects_non_object_payloads(self):
        for event in (None, [], "text", 42, True):
            with self.subTest(event=event):
                with self.assertRaises(ValueError):
                    snippe.webhook_reference(event)

    def test_rejects_non_object_data(self):
        for data in (None, [], "text", 42, True):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    snippe.webhook_reference({"data": data})


if __name__ == "__main__":
    unittest.main()
