# Verification — 2026-10-14 (Asia/Jerusalem)

Project: `C:\Users\Daniel.Dahan\Desktop\car-hunter`.
The configured workspace path with a space did not exist; the existing repository with a hyphen was used.

## Confirmed live checks

The local `.env` had the key `DATABASE_URL:`. Its name was corrected to
`DATABASE_URL`; the value was never printed. Environment files are ignored by Git.

Initial Telegram check sent exactly one message: `חיבור car-hunter תקין`.
The API returned:

```text
TELEGRAM: 200 ok= True message_id= 3
```

`python -m car_hunter check`:

```text
DATABASE SELECT 1: 1
DATABASE schema: ready
```

`python -m unittest discover -s tests -v`:

```text
Ran 6 tests in 0.001s
OK
```

`python tests/check_live_db.py`:

```text
DATABASE insert/update/dedup: PASS (one row, updated price=51000)
DATABASE synthetic test rollback: PASS (zero test rows retained)
```

`python -m car_hunter stats`:

```text
{}
```

This proves actual Neon connectivity and the save/update/primary-key behavior using
synthetic data in a rolled-back transaction. It does not prove real listing extraction.
The empty count means no real listings have been collected.

Editable Python package installation and bytecode compilation succeeded.
`git check-ignore .env artifacts/yad2.html` returned both paths;
`git ls-files .env` returned no tracked environment file.

## Source feasibility: observed actual responses

Playwright Chromium, headless, normal navigation:

| Source | HTTP | Actual title/result |
| --- | --- | --- |
| Yad2 `/vehicles/cars` | 200 | Radware Bot Manager Captcha; no listing links |
| Homeless `/private/home.asp` | 403 | Just a moment... / Performing security verification |
| Homeless mobile `/private` | 403 | Just a moment... / Performing security verification |

Ordinary httpx requests also returned challenges: Homeless 403; Yad2 200,
title `Radware Page`, text `Verifying your browser before proceeding...`, no ad links.
HTTP 200 was not treated as proof of successful collection.

Captured HTML/text is under ignored `artifacts/`. No CAPTCHA bypass was attempted.
No source-specific selectors or fabricated listing data were introduced.

## Not yet working

- Real ad extraction and persistence: blocked by source challenges.
- DeepSeek scoring: intentionally follows verified working collection; not implemented/tested yet.
- Structured real-ad Telegram notifications and scheduled GitHub Actions: not implemented/tested yet.

Next: obtain authorized normal access or real listing/detail HTML, implement the first
verified source parser, then test a real ad through extraction → Neon → scoring → Telegram.
