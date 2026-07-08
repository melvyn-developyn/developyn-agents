# Shared implementation conventions (read this first)

Every ticket in this folder targets the same three repos. This file captures the
patterns an implementing agent must follow so each ticket doesn't repeat them.
Paths below are relative to each repo root.

Repos (all present locally under `/Users/melvynmathews/github/medivault/`):
- `medivault-cloud` — patient/clinician SvelteKit frontend + Fastify backend. Owns the database.
- `admin-backend` — Fastify admin API. **Shares the same Postgres database** as medivault-cloud.
- `vitaspan-admin-dashboard` — SvelteKit admin frontend.

## Database (shared, single Postgres)

- **All migrations live in `medivault-cloud/backend/database-utils/migrations/`.**
  `admin-backend/db/migrations/` is empty and unused — do not add migrations there.
  Add a new table once, in medivault-cloud, even if only admin-backend reads it.
- Migration filename: `YYYYMMDDHHMMSS_kebab-case-name.js` (timestamp must sort after the
  latest existing file). Use Knex `exports.up` / `exports.down` (see any recent file, e.g.
  `20260626120000_add_trusted_individuals.js`).
- Table conventions, copied from `patient_trusted_individuals`:
  - `table.increments('id').primary();`
  - a public `table.uuid('uuid').notNullable().unique().defaultTo(knex.raw('gen_random_uuid()'));`
    on any table exposed to the frontend by id.
  - FKs to a user use `.uuid('..._uuid').references('uuid').inTable('users').onDelete('CASCADE')`
    (users are keyed by `uuid`, not `id`, in FKs).
  - `table.timestamps(true, true);` for `created_at` / `updated_at`.
  - status columns are `table.string('status')` with a string default (e.g. `'Pending'`), not enums.
- The `users` table already exists (created before these migrations). Relevant existing columns:
  `id`, `uuid`, `email`, `first_name`, `last_name`, `type` (`patient`/`clinician`), `date_of_birth`,
  `sex`, `medical_consent`, TOTP/2FA columns, `phone_number`. Add columns with
  `knex.schema.alterTable('users', …)`. There is **no** `account_status` column yet.

## Backend routes (Fastify, both backends)

- A route domain is a folder with `index.js` exporting `module.exports = (fastify, opts, done) => { … }`.
- Register it in the backend's root `index.js` with a prefix, e.g.
  `app.register(require('./consents'), { prefix: '/consents' });`
- Auth: add an `onRequest` hook that calls `await req.jwtVerify()`. Public endpoints (invite
  accept/reject by token) are listed in a `public_routes` array checked against
  `req.routeOptions.url` — see `trusted-individuals/index.js` top of module.
- After `jwtVerify`, the caller is on `req.user` (`req.user.uuid`, `req.user.email`, `req.user.type`).
- Validate every route with `typebox` schemas: `schema: { body: typebox.Object({ … }) }`.
  Common bits: `typebox.String({ format: 'email' })`, `typebox.String({ format: 'uuid' })`,
  `typebox.Optional(...)`, `typebox.Enum([...])`, `typebox.Array(...)`. All accepted request
  fields must be declared (strict schemas reject unknown fields).
- DB access is `fastify.db('table_name')` (Knex). Wrap multi-write flows in
  `fastify.db.transaction(async trx => { … })`.
- Errors: `require('../email-error.js')` is the shared error helper used as `.catch(email_error)`.
- Email: `const { send_email } = require('../email')`; templates live in `backend/email/templates/`.
- Token invites (reuse for any invite flow): `crypto.randomBytes(32).toString('hex')` for the raw
  token, store `sha256` hash only, 14-day expiry. Pattern is in `trusted-individuals/index.js`
  (`make_invite_token`, `hash_token`, `invite_expires_at`).

## admin-backend specifics

- Role gate: routes use the `authenticate` decorator — `{ onRequest: fastify.authenticate('super_user') }`
  (or `'clinic_admin'` / `'clinic_staff'`). Hierarchy is `clinic_staff < clinic_admin < super_user`.
- The admin user is `req.user` with `req.user.access_level`. Admin identity lives in the
  `admin_user` table (separate from `users`).

## Frontends

- **medivault-cloud** (patient): SvelteKit under `frontend/src/routes/`. Route groups: `(dashboard)`
  (authed app), `(welcome)` (sign-up/login). Patient settings live under
  `(dashboard)/my-profile/`. Sign-up is `frontend/src/routes/sign-up/`. Backend base URL comes
  from `PUBLIC_API_URL`.
- **vitaspan-admin-dashboard** (admin): SvelteKit under `src/routes/dashboard/`. API calls go through
  the axios wrapper in `src/http/index.js` (auto-attaches the `localStorage` JWT). Patient detail
  lives under `src/routes/dashboard/clinics/[clinic_id]/patients/`.

## After implementing

- Add/adjust OKF notes for any new API domain under `medivault-cloud/okf/api/` so future agents can
  find the endpoints. Match the style of existing files in that folder.
- Follow each repo's `AGENTS.md` / `CLAUDE.md` for lint/test commands before finishing.

## Cross-cutting rules (from the feature review)

- Prefer **request/queue workflows over destructive self-service** for deletion, closure, and consent
  withdrawal until retention policy is finalised. Never hard-delete clinical records in a
  patient-facing flow.
- Every consent change, access override, account-status change, and terms acceptance records:
  actor, timestamp, source IP, user agent (where available), and version/reason.
- Reuse existing email templates, the trusted-individual invite flow, document access-history, and
  the admin role model rather than building parallel systems.
