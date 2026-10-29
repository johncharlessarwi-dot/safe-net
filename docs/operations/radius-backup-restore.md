# SafeNet backup and restore checks

This runbook helps operators verify recovery readiness for SafeNet configuration and accounting data. Adapt the exact commands to the deployment's database and container environment.

## Backup scope

- Database records required for users, plans, NAS clients, configuration, and accounting.
- Application configuration excluding plaintext secrets from exported artifacts.
- Deployment manifests and versioned configuration templates.
- Encryption keys and secret references handled through the approved secret manager.

## Restore validation

1. Restore into an isolated environment.
2. Confirm schema compatibility with the deployed application version.
3. Verify user, plan, NAS, and accounting record counts against the backup manifest.
4. Confirm secret references resolve without exposing secret values.
5. Test a non-production authentication and accounting flow.
6. Record recovery time and any missing data.

## Safety

Do not restore over production during a drill. Restrict backup access, encrypt backup media, and test restores periodically. Treat accounting records as sensitive operational data.