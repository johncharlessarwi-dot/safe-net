# RADIUS accounting and log review guide

Use this guide when reviewing authentication and accounting activity in SafeNet. Apply the deployment's approved retention and access policies.

## Review access
- Restrict accounting exports and raw authentication logs to named operators with a business need.
- Use individual accounts and record the reason for privileged access.
- Do not copy shared secrets, passwords, access tokens, or full credential payloads into tickets or chat.
- Redact subscriber identifiers when sharing diagnostic examples outside the operations team.

## Routine checks
- Compare accepted and rejected authentication attempts by NAS client and time window.
- Investigate repeated failures, unexpected source addresses, and unusual request volume.
- Reconcile accounting start, interim-update, and stop events for incomplete sessions.
- Check for duplicate session identifiers and implausible session durations.
- Confirm device clocks are synchronized before interpreting event ordering.

## Incident handling
1. Preserve the relevant time window and source references.
2. Identify affected NAS clients without exposing their shared secrets.
3. Escalate suspected credential compromise for controlled rotation.
4. Record confirmed facts separately from hypotheses.
5. Restrict exported evidence and delete temporary copies when the review ends.

## Review record
Capture the reviewer, period, systems examined, exception references, decisions, and follow-up owner. Do not retain unnecessary raw personal data in the review summary.
