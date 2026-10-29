# NAS client inventory and review guide

Maintain an authoritative inventory of every network access server (NAS) permitted to communicate with SafeNet.

## Required inventory fields

- Stable device identifier and operator/owner.
- Management address or approved address range.
- Site and environment (production, staging, lab).
- Secret reference identifier—not the secret value.
- Date added, last reviewed, and retirement status.

## Review controls

- Remove retired or unknown clients promptly.
- Restrict management access to approved network ranges.
- Use unique shared secrets per client where possible.
- Review accounting destinations and time synchronization.
- Alert on unexpected source addresses and repeated authentication failures.

## Change process

Require an owner, reason, reviewer, and validation evidence for each client addition or modification. Reconcile the inventory with the server configuration on a regular schedule.