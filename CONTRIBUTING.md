# Contributing to SafeNet RADIUS Manager

SafeNet manages network authentication, accounting, tenant configuration and payment integrations. Changes in these areas can affect network access and customer data, so contributions should be focused and carefully verified.

## Prepare your environment

1. Read [README.md](README.md), [QUICKSTART.md](QUICKSTART.md) and [SETUP.md](SETUP.md).
2. Review [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) before changing deployment behavior.
3. Work from a dedicated branch and check for an existing issue or pull request covering the same change.
4. Never use production credentials or production customer data for local development.

## Secrets and configuration

- Copy `.env.example` to a local `.env` file and keep that file out of Git.
- Generate unique, high-entropy values for `SECRET_KEY`, database passwords, RADIUS shared secrets, administrator passwords and API encryption keys.
- Never reuse example values such as `testing123`, `admin123` or other documented sample credentials in a real environment.
- Do not publish payment-provider keys, SMTP credentials, tenant secrets, database dumps, voucher exports or customer records.
- Rotate a credential immediately if it is exposed in a commit, log, screenshot or issue.
- Do not expose database or phpMyAdmin ports publicly. Follow the deployment guide's host-binding and firewall recommendations.

## Change guidelines

- Preserve existing tenant isolation and verify that every tenant-scoped query uses the correct tenant context.
- Enforce authentication and authorization on server-side routes; hiding a UI control is not access control.
- Validate RADIUS client inputs, vendor attributes and payment/webhook data at the trust boundary.
- Keep payment callbacks idempotent and verify provider signatures before changing payment state.
- Avoid logging passwords, shared secrets, API keys, full payment payloads or unnecessary personal information.
- Treat migrations and configuration changes as compatibility-sensitive; document backup and rollback steps.
- Keep network-facing changes conservative and document required firewall ports and source restrictions.

## Local verification

Use the checks appropriate to the change. For Docker Compose configuration changes:

```bash
docker compose config --quiet
```

For a local deployment, inspect service health and logs:

```bash
docker compose ps
docker compose logs --tail=100
```

For RADIUS authentication changes, test with a dedicated disposable test user and a locally generated shared secret. Never paste real secrets into issue comments or pull request descriptions. Record the expected result and the environment in which the check was run.

The repository may require external services, credentials or network devices for full end-to-end verification. State clearly which checks were run and which could not be run.

## Pull request checklist

- [ ] The problem, impact and implementation are explained.
- [ ] Tenant isolation and role permissions have been considered.
- [ ] No credentials, customer records or database dumps are included.
- [ ] Configuration examples use placeholders, not working secrets.
- [ ] Relevant Docker, application or RADIUS checks have been run.
- [ ] Migration, backup and rollback implications are documented.
- [ ] Security-sensitive changes include reproduction and verification notes.

## Security reports

Do not disclose a live vulnerability or secret in a public issue. Contact the maintainer privately with the affected component, impact, safe reproduction steps and any suggested mitigation.
