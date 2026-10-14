# car-hunter

- Keep this a small single-user Python CLI. No server, Docker or frontend.
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
