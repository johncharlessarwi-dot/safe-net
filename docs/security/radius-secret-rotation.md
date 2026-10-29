# RADIUS shared-secret rotation runbook

Rotate RADIUS shared secrets through a controlled change. Never commit secrets to source control or paste them into tickets, chat, or shell history.

## Preparation

- Inventory NAS/client devices and the corresponding server-side client entries.
- Identify the authorized change owner and maintenance window.
- Generate a unique, high-entropy secret for each client where supported.
- Confirm a secure out-of-band method to deliver the new value.

## Rotation

1. Stage the new secret using the approved secret-management process.
2. Coordinate the device and server configuration change to minimize mismatch time.
3. Verify authentication and accounting from each affected device.
4. Monitor rejected requests and unexpected authentication failures.
5. Remove the retired secret after successful validation.

## Recovery

Keep a time-bounded rollback plan in the change record. If rollback is needed, restore the previous value only through the approved secret channel, then schedule a corrected rotation. Record device identifiers and timestamps, never the secret itself.