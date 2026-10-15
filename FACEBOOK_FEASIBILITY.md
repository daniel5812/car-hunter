# Facebook cloud feasibility — 2026-10-15 (Asia/Jerusalem)

## Result

The existing DeepSeek → Neon → Telegram application can run independently of the
user's computer. A reliable, permitted Facebook Marketplace/group collection path
has **not** been established. Production remains paused. A logged-in Codex browser
is not a deployed collector, and no Facebook credentials were exported or uploaded.

## Verified in this session

- Repository cloned at `2eef0cb8f9927e9af31254ebb75f99a6119b104a`.
- All 21 existing offline tests passed before this documentation-only change.
- GitHub CLI access works outside the restricted network sandbox.
- GitHub secret names confirmed: DATABASE_URL, DEEPSEEK_API_KEY,
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. Values were not retrieved.
- `Car hunter scan` is `disabled_manually`; its job also has `if: false`.
- Signed-in Marketplace search works interactively in the Codex in-app browser.
  It has not been tested on a GitHub-hosted runner.
- Facebook robots.txt returned HTTP 200. Python RobotFileParser reported
  `can_fetch('car-hunter', url) == False` for all three checked targets:
  - https://www.facebook.com/marketplace/
  - https://www.facebook.com/marketplace/item/2364282764409628/
  - https://www.facebook.com/groups/1779920948931494/
- These checks did not collect an inventory, send notifications or contact sellers.

## Collection and messaging constraints

Meta's published explanation states that automated collection without its
permission violates its terms. The robots results above are a concrete collection
blocker under this repository's source-access constraints; moving the same scraper
to a cloud server does not resolve them.

Source: https://about.fb.com/news/2021/04/how-we-combat-scraping/

Meta's own Messenger Platform collection requires a Facebook Page, a Page access
token, and pages_messaging. Its Send API requires the recipient to have messaged
the Page within the allowed window or opted in. It does not establish a supported
API for initiating personal Marketplace seller conversations from this account.

Source: https://www.postman.com/meta/messenger-platform-api/documentation/iyp204x/messenger-platform-api

The official Groups API v19 deprecation page could not be retrieved (429).
Do not treat this audit as a fresh direct verification of the removal date.
No currently supported group-reading API was established by this investigation.

Third-party Marketplace scraping services exist, but their marketing is not
evidence of Meta permission, Israeli inventory coverage, source freshness or
reliability. No service was purchased, connected, or accepted as a verified source.

## Hosting and cost

Standard GitHub-hosted runners are free for public repositories. This does not
make DeepSeek calls or third-party data services free. Actions schedules are
periodic jobs, not a continuous real-time service or a guaranteed delivery SLA.

Source: https://docs.github.com/en/billing/concepts/product-billing/github-actions

Current code already caches assessments by listing/profile digest. It does not
record token usage or enforce a monthly API spend ceiling. A future production
version should meter actual API usage and impose per-run limits before enabling
recurring analysis. Do not describe an unimplemented budget guard as active.

## User intent and remaining acceptance gates

The user prioritizes Marketplace, accepts occasional reauthentication, and wants
high-confidence automatic seller inquiries if feasible, otherwise Telegram alerts.
This relaxes the earlier no-manual-session preference but does not prove cloud
access or solve source permission/reliability. No new messages were sent.

Before production can be enabled:

1. Establish an authorized data feed or other source-access route that satisfies
   the repository rules. Native Facebook saved-search notifications may help the
   user directly; their suitability as a cloud data feed has not been verified.
2. Prove actual listing collection on a GitHub-hosted runner, including Israel and
   the selected Beersheba/south search area. Keep real publication dates distinct
   from observation times and preserve missing/ambiguous fields.
3. Validate normalized listing fixtures, duplicate handling, session expiration,
   and failure reporting without publishing raw captures or credentials.
4. Verify DeepSeek and Telegram in that route using existing secrets. Do not
   repeat a connection-test/demo message unnecessarily.
5. Only then reactivate recurring production. Seller outreach needs its own
   supported transport, deduplication, fixed inquiry text and bounded volume;
   Telegram-only remains the requested fallback.

No deployment, source integration, automatic seller outreach, or continuous
monitoring is claimed by this report.
