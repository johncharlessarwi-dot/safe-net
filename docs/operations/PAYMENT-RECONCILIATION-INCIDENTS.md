# Payment reconciliation incident guide

Use this guide when a payment provider response, customer receipt, and SafeNet account balance do not agree.

## Triage
- Capture provider reference, local transaction reference, amount, currency, timestamp, and affected account.
- Do not record card data, PINs, passwords, API keys, or full payment credentials.
- Determine whether the provider response is confirmed, pending, failed, or unknown.
- Check for duplicate callbacks and delayed provider notifications.

## Reconciliation
1. Query the provider using its documented reference and authorized credentials.
2. Compare provider status with the local ledger and any customer-facing receipt.
3. Check idempotency handling and callback processing history.
4. Avoid manually crediting an account while the provider status is ambiguous.
5. Record any approved correction with a second-person review where practical.

## Closure
Notify the customer only after the state is verified. Preserve the incident reference, decision, approver, and evidence source. Escalate suspected credential compromise or repeated callback anomalies.