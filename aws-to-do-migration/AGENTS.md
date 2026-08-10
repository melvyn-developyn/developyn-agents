# Agent Notes

## Current Project Context

This workspace is being used to coordinate migration of multiple AWS-hosted WordPress EC2 sites onto a Docker-based DigitalOcean host, then safely upgrade and decommission AWS resources to reduce cost.

Primary DigitalOcean host:

- `root@142.93.41.146`
- Ubuntu `24.04.3 LTS`
- Hostname: `ubuntu-s-4vcpu-8gb-lon1`

Core stack paths on the DigitalOcean host:

- WordPress Compose stack: `/srv/wordpress/compose/docker-compose.yml`
- WordPress env/secrets: `/srv/wordpress/compose/.env`
- Site files: `/srv/wordpress/sites/`
- MariaDB data: `/srv/wordpress/db/mariadb/`
- Backups: `/srv/wordpress/backups/`
- Caddy config: `/etc/caddy/Caddyfile`
- Caddy per-site logs: `/var/log/caddy/sites/`
- Beszel monitoring Compose: `/srv/wordpress/monitoring/beszel/docker-compose.yml`
- Beszel data: `/srv/wordpress/monitoring/beszel/data/`

## Running Containers

WordPress containers on DigitalOcean:

- `wp-ace-sections` -> `127.0.0.1:8081`, image `wordpress:php8.1-apache`
- `wp-bradleygas` -> `127.0.0.1:8082`, image `wordpress:php8.1-apache`
- `wp-pedmore` -> `127.0.0.1:8083`, image `wordpress:php8.4-apache`
- `wp-oakhill` -> `127.0.0.1:8084`, image `wordpress:php7.4-apache`
- `wp-meirglobal` -> `127.0.0.1:8085`, image `wordpress:php7.4-apache`
- `wp-aps-ltd` -> `127.0.0.1:8086`, image `wordpress:php7.4-apache`
- `wp-telehandlers` -> `127.0.0.1:8087`, image `wordpress:php7.4-apache`
- `wp-ledgability` -> `127.0.0.1:8088`, image `wordpress:php8.1-apache`
- `wp-venturema` -> `127.0.0.1:8089`, image `wordpress:php7.4-apache`
- `wp-nationalhire` -> `127.0.0.1:8091`, image `wordpress:php7.4-apache`
- `wp-igs` -> `127.0.0.1:8092`, image `wordpress:php7.4-apache`
- `wp-developyn` -> `127.0.0.1:8093`, image `wordpress:php7.4-apache`
- `wp-mariadb` -> `mariadb:10.6`

Monitoring containers:

- `beszel`
- `beszel-agent`

Beszel dashboard:

- `https://monitor.developyn.com`

## Timesheet Manager Migration

Replacement timesheet app deployed on DigitalOcean:

- Container: `wp-timesheet-manager` -> `127.0.0.1:8094`, image `developyn-timesheet-manager:latest`
- Source: `/srv/wordpress/apps/timesheet-manager/app`
- Data: `/srv/wordpress/apps/timesheet-manager/data/timesheet.sqlite3`
- Runtime env: `/srv/wordpress/apps/timesheet-manager/.env` (mode 600)
- Backups: `/srv/wordpress/backups/timesheet-manager/`
- Caddy block added for `timesheet.developyn.com` -> `127.0.0.1:8094`
- Imported 6 users, 28 projects, 92 project-developer links, 463 timesheet entries from old Postgres DB
- Old Postgres DB EC2: `Timesheet Manager Database`, `i-09d457b392edc08b7`, IP `52.211.236.240`
- DNS cut over in Route 53: `timesheet.developyn.com A 142.93.41.146`, change `/change/C03093491H1DHH3OZK9UU`, `INSYNC`.
- HTTPS verified: login `200`, health `200`, HTTP redirects to HTTPS, Let's Encrypt cert issued.
- Old AWS timesheet resources fully deleted: Lambda functions, API Gateway, 2 CloudFront distributions, S3 bucket, Route 53 `dev.timesheet.developyn.com` CNAME, IAM roles/policies, Postgres EC2, Elastic IP, security group.

## Holiday Tracker Migration

Holiday Tracker app migrated and cut over on DigitalOcean:

- Container: `wp-holiday-tracker` -> `127.0.0.1:8095`, image `developyn-holiday-tracker:latest`
- Source: `/srv/wordpress/apps/holiday-tracker/app`
- Data: `/srv/wordpress/apps/holiday-tracker/data/db.sqlite` (SQLite, ~21MB, mounted as volume)
- Backups: `/srv/wordpress/backups/holiday-tracker/`
- Caddy block added for `holiday.developyn.com` -> `127.0.0.1:8095`
- App: Node 12 / Express / Sequelize / SQLite (TimeOff.Management fork at `git@github.com:Developyn/timeoff-management.git`)
- Entry point: `node bin/wwww` (4 w's)
- Config: `config/app.json` (Google login for `developyn.com`, AWS SES email, session/crypto secrets)
- Cron jobs: Christmas auto-book, weekly absence reminders
- DNS cut over in Route 53: `holiday.developyn.com A 142.93.41.146`, change `/change/C0794096VN1TSZ1LAQ51`, `INSYNC`.
- Old EC2: `i-0bfb44fecf53d4710`, IP `34.243.119.87`, Ubuntu `18.04`, key `admin` — terminated, security group deleted.
- HTTPS verified: login `200`, homepage `302` redirect to login, HTTP redirects to HTTPS, Let's Encrypt cert issued.

## Completed Work

- Deleted approved AWS Serverless/CloudFormation cleanup scope in `eu-west-1`, including `*webshop*`, `boilerfix-service-dev`, `developynblog-dev`, `stripe-service-dev`, and `stripe-service-production` stacks.
- Emptied blocked Serverless deployment buckets before stack deletion.
- Verified matching Lambda functions for cleaned scopes are gone.
- Audited June AWS bill and identified major costs from public IPv4, EBS, snapshots, WAF, and Route 53.
- Audited 12 running WordPress EC2 instances in `eu-west-1`.
- Confirmed SSH access as `ubuntu` to all 12 WordPress servers after loading local SSH keys.
- Removed a roughly `9G` IGS WordPress debug log and disabled debug logging there.
- Created and configured the DigitalOcean host with Docker, Docker Compose, Caddy, UFW, swap, Docker log rotation, and journald retention.
- Migrated and cut over live sites:
  - `acesectionsltd.co.uk`
  - `bradleygasservices.co.uk`
  - `pedmoreroofing.com`
  - `developyn.com`
  - `telehandlers.co.uk`
- Migrated but not cut over yet:
  - `oakhilloptical.co.uk`
  - `meirglobal.org`
  - `aps-ltd.com`
  - `ledgability.co.uk`
  - `venturema.co.uk`
  - `nationalhiresolutions.co.uk`
  - `igs-uk.org`
- Configured Caddy HTTPS for live sites and monitoring.
- Added missing WordPress `.htaccess` rewrite rules for Ace and Bradley.
- Installed Beszel monitoring for host and containers.
- Enabled per-site Caddy access logs.
- Created DNS migration plan in `dns-update-plan-for-developyn-and-pedmore.txt`.

## Bradley Upgrade State

Bradley has been upgraded and verified.

Backup before upgrade:

- `/srv/wordpress/backups/bradleygas/pre-upgrade-20260630205743`
- Latest backup pointer: `/srv/wordpress/backups/bradleygas/latest-pre-upgrade-backup.txt`

Changes completed:

- Disabled WordPress debug logging.
- Updated WordPress core from `6.1.10` to `7.0`.
- Updated all plugins and themes.
- Fixed stale `wp-super-cache` `WPCACHEHOME` path from `/var/www/wordpress/wp-content/plugins/wp-super-cache/` to `/var/www/html/wp-content/plugins/wp-super-cache/`.
- Switched only Bradley from `wordpress:php7.4-apache` to `wordpress:php8.1-apache`.

Verification completed:

- `wp-bradleygas` running on PHP `8.1.34`.
- WordPress reports version `7.0`.
- Homepage returns `200`.
- `www` returns redirect `301`.
- `/wp-admin/` redirects to login with `302`.
- `/wp-json/` returns `200`.
- `sitemap_index.xml` returns `200`.
- CSS asset returns `200`.
- No post-switch `5xx` found.
- No recent PHP fatal, parse, or uncaught errors found in container logs.

## Pedmore Upgrade State

Pedmore has been upgraded and verified.

Backup before upgrade:

- `/srv/wordpress/backups/pedmore/pre-upgrade-20260701034046`
- Latest backup pointer: `/srv/wordpress/backups/pedmore/latest-pre-upgrade-backup.txt`

Changes completed:

- Disabled WordPress debug logging.
- Updated WordPress core from `6.1.10` to `7.0`.
- Updated all plugins and themes.
- Switched only Pedmore from `wordpress:php7.4-apache` to `wordpress:php8.4-apache`.

Verification completed:

- `wp-pedmore` running on PHP `8.4.22`.
- WordPress reports version `7.0`.
- Public homepage renders successfully from outside the server.
- Public `www` hostname renders successfully from outside the server.
- Direct container checks passed: homepage redirects as expected, `/wp-admin/` redirects to login, and `/wp-json/` returns `200`.
- `sitemap_index.xml` and `sitemap.xml` return `200`.
- No recent PHP fatal, parse, or uncaught errors found in container logs.

## Ace Upgrade State

Ace has been upgraded and verified.

Backup before upgrade:

- `/srv/wordpress/backups/ace-sections/pre-upgrade-20260701021347`
- Latest backup pointer: `/srv/wordpress/backups/ace-sections/latest-pre-upgrade-backup.txt`

Changes completed:

- Disabled WordPress debug logging.
- Updated WordPress core from `5.7.15` to `7.0`.
- Updated all plugins and themes.
- Switched only Ace from `wordpress:php7.4-apache` to `wordpress:php8.1-apache`.

Verification completed:

- `wp-ace-sections` running on PHP `8.1.34`.
- WordPress reports version `7.0`.
- Homepage returns `200`.
- `www` returns `200`.
- `/wp-admin/` redirects to login with `302`.
- `/wp-json/` returns `200`.
- `sitemap.xml` returns `200`.
- No post-switch `5xx` found.
- No recent PHP fatal, parse, or uncaught errors found in container logs.

## Developyn Upgrade State

Developyn has been upgraded and verified (2026-07-13).

Backup before upgrade:

- `/srv/wordpress/backups/developyn/wp-php-upgrade-20260712225800` (DB dump `developyn-db.sql`, `html.tar.gz` excl. cache, `docker-compose.yml.bak`)

Changes completed:

- Switched only Developyn from `wordpress:php7.4-apache` to `wordpress:php8.3-apache`.
- Updated WordPress core from `6.9.4` to `7.0.1` (via WP-CLI, DB already at latest schema).
- Updated 13 of 14 plugins with available updates (Forminator `1.54.0`->`1.55.1`, Yoast `27.7`->`28.0`, Otter `3.1.11`->`3.2.0`, Redirection `5.7.5`->`5.9.0`, etc.). Backup: `/srv/wordpress/backups/developyn/plugins-upgrade-20260712230532` (DB + `plugins.tar.gz`). The paid `all-in-one-wp-migration-unlimited-extension` stayed at `2.82` — CLI can't fetch it without the ServMask license; update it from wp-admin if needed.

Verification completed:

- `wp-developyn` running on PHP `8.3.32`, WordPress `7.0.1`.
- `core verify-checksums` passes (only a harmless stray `wp-admin/.pid`).
- Homepage, `/about/`, `/services/`, `/contact/` return `200`; `/wp-admin/` `302` to login.
- 30 active plugins unchanged (none deactivated by a fatal).
- No PHP fatal/parse errors in container logs; page cache purged.

Earlier (2026-07-13): all 76 Forminator forms had their reCAPTCHA v3 score threshold raised `0.5` -> `0.7` to cut contact-form spam.

2026-07-15: disabled the customer-facing Forminator auto-response labelled `Thanks for contacting Developyn` on all 74 standard contact/lead forms. All 76 `Admin Email` notifications remain enabled, and the `free-ebook` form's `Inquirer Email` transactional response was retained. Pre-change Forminator metadata backup: `/srv/wordpress/backups/developyn/forminator-autoresponder-removal-20260714223012/forminator-form-meta-before.json` (SHA-256 `e6532cca76fe1412b2b334b5b3d09737292ac7b71df0a18c53fb56825a8e82d8`). Verification confirmed no unintended configuration differences, `/contact/` and the homepage returned `200`, and no relevant container errors were logged.

2026-07-22: optimised Developyn's mobile Lighthouse performance from `55` to `88` (FCP `4.4s` -> `1.3s`, LCP `10.4s` -> `3.2s`, TBT `100ms` -> `50ms`, payload `2.68MB` -> `1.04MB`). Added `/wp-content/mu-plugins/developyn-performance.php`; deactivated duplicate `olympus-google-fonts`; moved three jQuery custom-code snippets to the footer; consent-gated Site Kit/GTM; lazy-loaded reCAPTCHA when the footer form approaches/focuses; converted six large homepage images to WebP; made non-critical styles asynchronous; removed duplicate font faces and Font Awesome on the homepage; fixed the breadcrumb console exception. Added 30-day static-asset cache headers to the Developyn Caddy block. Functional checks covered homepage/services/contact/login, desktop/mobile carousel behaviour, browser console, and reCAPTCHA-on-focus. Final report: repo file `developyn-lighthouse-final-1.report.html`. Two rotating optimisation backup slots only: immutable baseline `/srv/wordpress/backups/developyn/performance-optimization/current-state` and latest rollback `/srv/wordpress/backups/developyn/performance-optimization/pre-change`; both archives and checksums verified.

2026-07-22: redesigned the live Developyn Industries and News pages. The page bodies now use `[developyn_industries]` and `[developyn_insights]`, rendered by `/wp-content/mu-plugins/developyn-content-hubs.php` (repo source: `developyn-content-hubs.php`). Industries now provides an 18-sector image directory with accessible category filtering and a contact CTA. News now provides a featured editorial layout, topic filters, search, reading times, and pagination capped at 12 posts per page. Both hubs are responsive, use one H1 and one main landmark, preserve existing URLs and Yoast metadata, and omit the obsolete duplicate Schema.org summary/assets on these two pages. Desktop/mobile interaction checks passed for filters, topic/search results, pagination, all industry links, representative news links, horizontal overflow, browser errors, and HTTP responses. Final mobile Lighthouse: Industries `86/92/96/100` (performance/accessibility/best practices/SEO; FCP `1.2s`, LCP `3.7s`, TBT `0ms`); News `95/93/96/100` (FCP `1.2s`, LCP `2.6s`, TBT `50ms`). Remaining accessibility deductions are from malformed telephone links in the shared legacy footer. Reports: `industries-lighthouse-final.json` and `news-lighthouse-final.json`. Rollback backup: `/srv/wordpress/backups/developyn/performance-optimization/pre-change`; it and immutable `current-state` were checksum-verified after completion.

2026-07-22: completed the Education & Training industry-subpage redesign pilot at `/education-and-training/` (page ID `9664`). Its body now uses `[developyn_industry_education]`, rendered by the existing `developyn-content-hubs.php` MU plugin. The pilot introduces a split image hero, focused conversion paths, five solution modules, learner/platform outcomes, a three-step implementation section, and a final contact CTA while preserving the URL, `wp-custom-template-industry` template, featured image, Yoast title/description/focus keyword, canonical, Open Graph image, and Yoast JSON-LD. The duplicate All in One Schema.org visible summary/assets are omitted on this page. Desktop/mobile checks passed for one H1/main landmark, all six content links, no overflow, no browser errors, existing Industries/News rendering, and `200` responses. Mobile Lighthouse: `96/93/96/100`, FCP/LCP `1.1s`, TBT `10ms`, CLS `0.003`, payload `392KiB`; remaining accessibility deductions are from the shared legacy footer telephone links. Report: `education-lighthouse-final.json`. A checksum-verified rollback was created before the pilot; the rotating slot was subsequently refreshed before the full industry rollout described below.

2026-07-22: rolled the approved content-hub design across the remaining 17 industry subpages. Each body now uses `[developyn_industry_page]`, backed by a shared data-driven renderer in `developyn-content-hubs.php`; Education retains its pilot shortcode. Every sector has page-specific headlines, imagery, five solution modules, five outcomes, relevant internal links and a tailored CTA. Construction, Manufacturing and MedTech also retain prominent proof/delivery context, including the existing induction results and MedTech compliance/timeframe claims. All original slugs, `wp-custom-template-industry` templates, featured-image metadata, Yoast titles/descriptions/focus keywords, canonicals, Open Graph metadata and Yoast JSON-LD were preserved. The obsolete All in One Schema.org visible summary/assets and stale Otter block CSS metadata are omitted. Verification covered all 18 pages at `1440px` and `390px`: one H1/main landmark, five solutions, five outcomes, three delivery steps, loaded hero image, correct canonical/description, no duplicate schema summary, no overflow, no browser errors, no failed content links and `200` responses. Representative mobile Lighthouse: Automotive `95/93/96/100` (LCP `2.8s`), Construction `91/93/96/100` (LCP `3.2s`), MedTech `95/93/96/100` (LCP `2.5s`); residual accessibility deductions remain in the shared legacy footer. Reports: `automotive-lighthouse-final.json`, `construction-lighthouse-final.json`, `medtech-lighthouse-final.json`. Immediately before rollout, `/srv/wordpress/backups/developyn/performance-optimization/pre-change` was recreated and validated by checksums, gzip integrity and a 75-table live/dump comparison; it includes the approved Education pilot state.

## Spam / Security Hardening (2026-07-21)

Live-diagnosed the persistent Developyn form spam from Caddy logs + DB. Root cause was NOT the v3 threshold: honeypot is already on (Forminator native + WP-Armour plugin) and insufficient, and there is **no Akismet / zero content filtering** (all 407 Forminator entries are `is_spam=0`). Worst form is id `7026` (`contact-form-location-landing-2`), 78 entries/30d. Caddy logs also showed ~32.5k/day POSTs to `xmlrpc.php` and ~5.2k/day to `wp-login.php` with no throttling.

Changes applied and verified:

- Caddy: added `@xmlrpc path /xmlrpc.php` -> `respond 403` to the `developyn.com` block. Backup at `/etc/caddy/Caddyfile.bak-<ts>`. Verified `xmlrpc.php` returns `403`, homepage/`/contact/` still `200`.
- fail2ban: installed; jail `caddy-wp` (`/etc/fail2ban/filter.d/caddy-wp.conf` + `/etc/fail2ban/jail.d/caddy-wp.conf`), `backend = polling` (Ubuntu default is `systemd`, which does not read the Caddy files), watches `/var/log/caddy/sites/*.log`, bans IPs with >20 POSTs to `wp-login.php`/`xmlrpc.php` in 600s for 3600s. Covers all sites. Confirmed banning on start.

Pending (needs keys from owner):

- Install + enable **Akismet** on the contact/lead forms (highest-leverage remaining lever) — needs Akismet API key.
- Swap reCAPTCHA **v3 -> hCaptcha/Turnstile** (interactive) via the hCaptcha plugin global toggle — needs hCaptcha site+secret keys.

Security review flagged (not yet actioned): EOL PHP 7.4 on 7 containers + WP `5.6.17` on Meir; `all-in-one-wp-migration` (+ paid unlimited ext, stuck at `2.82`) active on live Developyn; risky active plugins `theme-editor`/`svg-support`/`custom-css-js`/`insert-headers-and-footers`; REST user enumeration; Beszel auth + off-host backups to confirm. Good posture confirmed: root SSH key-only (password auth off), UFW 22/80/443 only, `.env` `600`, per-site MariaDB users isolated (`developyn@%` scoped to `developyn` schema).

### wp2shell RCE (CVE-2026-63030 + CVE-2026-60137, 2026-07-21)

DigitalOcean advisory: unauthenticated RCE chain via the WP REST batch endpoint. Patched cores: `7.1beta2`/`7.0.2`/`6.9.5`/`6.8.6`. Already-probed in Developyn's Caddy logs before mitigation.

Mitigation (block `/wp-json/batch/v1` + `?rest_route=/batch/v1` -> 403) applied everywhere:

- Main host `142.93.41.146`: Caddy snippet `(wp2shell)` defined + `import wp2shell` in all 15 site blocks. Backup `/etc/caddy/Caddyfile.bak-wp2shell-<ts>`.
- Core versions on main host (read from `wp-includes/version.php`): patched already via WP auto-update = developyn/bradley/ace/pedmore `7.0.2`, nationalhire `6.9.5`. Still on vulnerable versions but mitigated by Caddy = telehandlers `6.6.5` (LIVE), aps-ltd/ledgability `6.8.5`, igs `6.4.8`, venturema/oakhill `6.3.8`, meirglobal `5.6.17`.
- 5 other DO droplets (separate hosts, same SSH key — see memory `other-do-wordpress-hosts`): trueform/trueformdigital already `7.0.2`; houghton `6.6.5` (apache vhost `<If>` block, `AllowOverride None` so no .htaccess), goldcrest `6.7.5` + prisymlabels `6.7.1` (.htaccess block). All 3 apache hosts verified 403 on batch endpoint, homepage 200.

Core patching (2026-07-21): the 4 LIVE unpatched sites updated to `6.8.6` via wp-cli (backup DB+files first, verified home/wp-admin/batch after each): telehandlers (main host), houghton, goldcrest, prisymlabels. wp-cli reused from an existing on-host phar (`/srv/wordpress/wp-cli.phar`, WP-CLI 2.12.0) on the main host; the 3 apache droplets already had `/usr/bin/wp`. Note: prisymlabels has 8.3G uploads on a 25G disk — its 7.8G file backup filled the disk to 96% and made the first update fail silently (disk full); retry succeeded once space was checked, then removed the uploads `html.tar.gz` (a core update never touches `wp-content/uploads`) leaving the 74M `db.sql`. Backups: main host `/srv/wordpress/backups/telehandlers/wp2shell-patch-*`; droplets `/var/backups/wp2shell-*`.

TODO (defense-in-depth, mitigated not patched): update cores to `6.8.6`+ on the 6 STAGED (non-public) main-host sites: aps-ltd, ledgability, igs, venturema, oakhill, meirglobal (meir is `5.6.17`, a large jump — do at cutover with extra care).

## Important DNS Context

Do not change DNS or Route 53 in this session without explicit user permission.

Developyn has been cut over in Route 53:

- `developyn.com. A 142.93.41.146`
- `www.developyn.com. CNAME developyn.com.`
- Old AWS IP: `18.201.140.243`
- Route 53 change ID: `/change/C07171083W2SIC03XBQ6D`, reported `INSYNC`.
- Caddy HTTPS is enabled for `developyn.com` and `www.developyn.com`.
- Fresh pre-cutover backup: `/srv/wordpress/backups/developyn/pre-cutover-20260707233556`
- Latest backup pointer: `/srv/wordpress/backups/developyn/latest-pre-cutover-backup.txt`
- `WP_HOME`/`WP_SITEURL` are set to `https://developyn.com`.
- Public checks passed: homepage `200`, `www` canonicalizes to apex with `200`, `/wp-json/` `200`, and `/sitemap.xml` `200`.
- Real Let's Encrypt certificates were issued for apex and `www`.
- No recent PHP fatal, parse, uncaught, memory, or Caddy `5xx` errors found after cutover.

Pedmore has been cut over in Route 53:

- `pedmoreroofing.com. A 142.93.41.146`
- `www.pedmoreroofing.com. CNAME pedmoreroofing.com`
- Old AWS IP: `3.249.101.94`
- Route 53 change ID: `/change/C07201272HSFBEU983RI5`, reported `INSYNC`.
- Caddy HTTPS is enabled for `pedmoreroofing.com` and `www.pedmoreroofing.com`.
- Fresh pre-cutover backup: `/srv/wordpress/backups/pedmore/pre-cutover-20260630220620`
- Latest backup pointer: `/srv/wordpress/backups/pedmore/latest-pre-cutover-backup.txt`
- Pedmore debug logging is disabled and `WP_HOME`/`WP_SITEURL` are set to `https://pedmoreroofing.com`.
- Some local resolvers may briefly cache the old AWS IP during DNS propagation.

Oakhill DNS is hosted at One.com:

- Old IP: `54.155.196.25`
- Target new IP: `142.93.41.146`
- User must update One.com when ready.

Meir Global is staged on DigitalOcean but DNS is not cut over:

- Domain: `meirglobal.org`
- Old AWS IP: `34.244.46.39`
- Target new IP for future cutover: `142.93.41.146`
- Container: `wp-meirglobal` on `127.0.0.1:8085`
- Site files: `/srv/wordpress/sites/meirglobal/html`
- Database: `meirglobal` in `wp-mariadb`
- Caddy block is HTTP-only for `meirglobal.org` and `www.meirglobal.org`.
- WordPress reports version `5.6.17`; PHP container is `7.4`.
- Debug logging disabled in staged `wp-config.php`.
- Standard WordPress `.htaccess` rewrite rules added because the migrated copy had no `.htaccess`.
- Staged backup: `/srv/wordpress/backups/meirglobal/staged-20260630230914`
- Latest staged backup pointer: `/srv/wordpress/backups/meirglobal/latest-staged-backup.txt`
- Staged checks passed via host-header local Caddy: homepage `200`, `/wp-admin/` `302`, `/wp-json/` `200`, no recent PHP fatal/parse/uncaught logs.
- Future DNS records needed: apex `A -> 142.93.41.146`; `www` CNAME to apex or `A -> 142.93.41.146`.

Additional sites staged on DigitalOcean but not cut over:

- `aps-ltd.com`: old AWS IP `3.250.158.116`, container `wp-aps-ltd` on `127.0.0.1:8086`, DB `aps_ltd`, backup `/srv/wordpress/backups/aps-ltd/staged-20260630232707`, WordPress `6.8.5`, staged URLs intentionally set to `http://aps-ltd.com` for local host-header testing.
- `telehandlers.co.uk`: **CUT OVER 2026-07-13**. Old AWS IP `52.211.87.147`, container `wp-telehandlers` on `127.0.0.1:8087`, DB `telehandlers`, WordPress `6.6.5`. DNS moved OFF GoDaddy (`domaincontrol.com`) to **DigitalOcean DNS** — owner switched registrar (123reg) NS to `ns1/2/3.digitalocean.com`; zone has only apex `A -> 142.93.41.146` + `www` CNAME→apex (no mail/MX/TXT/CAA on this domain). Fresh content re-sync done before cutover (DB current to 2026-07-08, uploads 39M). Search-replace cleaned 4 dev subdomains (`*.wordpress.developyn.com`), forced http→https, fixed `/var/www/wordpress`→`/var/www/html`; wp-config reverse-proxy TLS snippet added. HTTPS live (Let's Encrypt, apex+www). Pre-cutover backup `/srv/wordpress/backups/telehandlers/pre-cutover-20260713093822` (pointer at `latest-pre-cutover-backup.txt`); original staged backup `/srv/wordpress/backups/telehandlers/staged-20260630232729`.
- `ledgability.co.uk`: old AWS IP `54.217.50.179`, container `wp-ledgability` on `127.0.0.1:8088`, DB `ledgability`, backup `/srv/wordpress/backups/ledgability/staged-20260630233429`, WordPress `6.8.5`, PHP container `8.1` to match source PHP 8.1.
- `venturema.co.uk`: old AWS IP `3.249.250.224`, container `wp-venturema` on `127.0.0.1:8089`, DB `venturema`, backup `/srv/wordpress/backups/venturema/staged-20260630233524`, WordPress `6.3.8`. AWS instance/tag referred to this as `venturemma`, but the live domain/config is `venturema.co.uk`.
- `nationalhiresolutions.co.uk`: old AWS IP `34.241.136.6`, container `wp-nationalhire` on `127.0.0.1:8091`, DB `nationalhire`, backup `/srv/wordpress/backups/nationalhire/staged-20260630234655`, WordPress `6.9.4`, staged URLs intentionally set to `http://nationalhiresolutions.co.uk` for local host-header testing.
- `igs-uk.org`: old AWS IP `54.246.37.144`, container `wp-igs` on `127.0.0.1:8092`, DB `igs`, backup `/srv/wordpress/backups/igs/staged-20260701000352`, WordPress `6.4.8`. IGS debug logging was already disabled and no large debug log remains. Staged `wp-config.php` memory limit was raised from `15M` to `256M` because the migrated copy hit PHP memory fatals during local checks.
- `developyn.com`: cut over to DigitalOcean in Route 53; old AWS IP `18.201.140.243`, container `wp-developyn` on `127.0.0.1:8093`, DB `developyn`, staged backup `/srv/wordpress/backups/developyn/staged-20260630235718`, fresh pre-cutover backup `/srv/wordpress/backups/developyn/pre-cutover-20260707233556`, WordPress `6.9.4`, live URLs set to `https://developyn.com`.

For all additional staged sites above:

- Caddy blocks are HTTP-only for apex and `www` hostnames.
- No DNS or Route 53 changes were made during staging.
- Standard WordPress `.htaccess` rewrite rules were added/confirmed.
- Stale `wp-super-cache` paths from `/var/www/wordpress` were replaced with `/var/www/html` where present.
- Debug logging was disabled in staged `wp-config.php`.
- Staged checks passed via host-header local Caddy: homepage `200`, `/wp-json/` `200`, login/admin reachable, and no recent PHP fatal/parse/uncaught logs.
- Future DNS records generally needed: apex `A -> 142.93.41.146`; `www` CNAME to apex or `A -> 142.93.41.146`.

`developyn.com` DNS migration is high-risk:

- Current Route 53 zone has about `153` records.
- Includes Google/Zoho mail, SES DKIM, ACM validation, CloudFront aliases, and many app/client/WordPress records.
- Do not hand-copy casually or migrate from memory.

## Old AWS WordPress EC2s

Old source EC2s should remain running temporarily for rollback until migrated sites are stable.

Known old instances/IPs:

- `wordpress-ace-sections` `34.255.195.223`
- `wordpress-bradley_gas_services` `34.245.102.186`
- `wordpress-meirglobal.org` `34.244.46.39`
- `wordpress-Pedmoreroofing` `3.249.101.94`
- `wordpress-ledgability.co.uk` `54.217.50.179`
- `wordpress-Oakhill` `54.155.196.25`
- `wordpress-igs` `54.246.37.144`
- `wordpress-developyn.com` `18.201.140.243`
- `wordpress-venturemma` `3.249.250.224`
- `wordpress-nationalhiresolutions.co.uk` `34.241.136.6`
- `wordpress-aps-ltd.com` `3.250.158.116`
- `wordpress-telehandlers` `52.211.87.147`

## Next Steps

Recommended next action:

1. Monitor Pedmore briefly after the PHP 8.4 upgrade.
2. Finish testing Oakhill container before DNS cutover once One.com access is available.
3. Collect DNS access/details from clients for staged sites and plan cutovers one at a time.
4. Coordinate Oakhill DNS change through One.com once access is available.
5. After migrated/cut-over sites are stable for several days, stop old AWS EC2 instances for a rollback window, then terminate and release public IPv4s later.
6. Treat `developyn.com` DNS as a separate high-risk migration because of mail, SES, ACM, CloudFront, app/client records, and many subdomains.

## Operational Notes

- Use safe, incremental migrations with backups and rollback.
- User accepts a short 5-10 minute write-freeze/data-loss window for site cutovers.
- Use Caddy for reverse proxy and HTTPS; no Certbot is needed.
- Caddy issues certificates automatically when hostname blocks omit `http://`.
- If DNS has not propagated, Let's Encrypt can fail or rate-limit temporarily.
- Do not lose uploaded/user files on content-heavy sites such as IGS.
- Local Mac `/etc/hosts` edits are blocked through tools because `sudo` requires an interactive password.
- Prefer AWS CLI against the configured default AWS account/profile.
- AWS account: `630423658649`; IAM user: `arn:aws:iam::630423658649:user/Melvyn`.
- Zsh quoting can be fragile for complex remote commands; use simpler commands or `bash -lc` remotely when needed.
