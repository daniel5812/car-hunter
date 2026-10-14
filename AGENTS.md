# car-hunter

- USER HOLD (2026-10-14): all production scanning is paused until source reliability is resolved and the user explicitly authorizes reactivation. Do not enable the GitHub workflow, schedule, push triggers, scan job, or live notifications during this hold. Read-only source research and offline tests remain allowed.

- Keep this a small single-user Python CLI. No server, Docker or frontend.
- Production must run unattended in GitHub Actions. No local computer dependency, manually renewed session, manual CAPTCHA or stealth bypass. Prove source collection on a GitHub-hosted runner before enabling it.
- Check source access terms and robots. Focus is excluded because its cloud-fetched terms explicitly prohibit automated collection; ad was not selected because the first audited sample was stale. Zehcan has no discovered terms link and its robots endpoint returns HTML, which is not an explicit grant of permission.
- Do not confuse publisher publication/update/bump dates with first_seen/last_seen, crawl time, footer copyright dates or related content. Missing publisher dates stay null.
- Field claims from seller prose must have source evidence. Private vehicle ownership is not private seller type. EV driving range is not odometer mileage. Preserve conflicts instead of guessing corrected values.
- Use psycopg for PostgreSQL. Load local secrets from `.env`; environment variables take precedence.
- Never print connection strings, API keys, bot tokens, environment contents or raw HTTP exceptions. Never commit `.env`, browser captures or contact exports.
- Telegram sends must be explicitly requested with a CLI flag or by the user. Do not repeat the connection-test message unintentionally.
- Inspect live Playwright HTML before changing extraction selectors. Never invent selectors, ad IDs, results, prices or missing fields. Do not bypass CAPTCHAs or access controls.
- Deduplicate using `(source, ad_id)` in Postgres. Preserve first-seen and notification state on updates.
- Store the full purchase price only; financing/monthly payments must not become purchase prices.
- Listing claims are unverified seller statements. Reliability, performance, consumption and dimensions need sources for the exact variant. DeepSeek must not supply invented facts.
- Budget target is ILS 50,000. Mark over-budget ads; do not invent an agreed maximum. Prefer automatic, 2017+, low mileage, private sellers and Beersheba/south. Do not impose an unapproved mileage cap.
- Reference: Mazda 2 Demio 2016 1.5L 112 hp, size up to Mazda 3; balanced reliability, performance and economy, urban/intercity 10–20k km/year.
- Validate parsing with captured real HTML fixtures or focused edge-case tests. Run `python -m unittest discover -s tests` and the CLI checks appropriate to changes. Live tests may write to Neon; notification tests send real messages.
