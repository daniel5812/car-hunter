# Yad2 feasibility — 2026-10-14

Decision: STOP at access conditions. No Yad2 adapter added.

## Verified cloud execution

- Run: https://github.com/daniel5812/car-hunter/actions/runs/38580385620
- Job: 115908412697; GitHub-hosted Ubuntu 24.04, Azure westus2.
- Checked at 2026-10-14 17:25:39 Asia/Jerusalem (14:25:39 UTC).
- Ordinary HTTP GET of https://www.yad2.co.il/robots.txt: 200; robots permits the unfiltered /vehicles/cars page for this user agent. This is not permission under the terms.
- Ordinary HTTP GET of https://www.2.yad2.co.il/eula: 200; title: תקנון אתר יד2.
- Official terms explicitly prohibit collecting data using automated software, including spiders and scrapers, with an exception for ordinary viewing as a reasonable user. The clause begins: "שלא לאסוף נתונים מהנכסים הדיגיטליים".
- The terms were inspected before the experiment and independently confirmed in the runner HTML. No guessed inventory endpoints were used.

## Scope and limitations

The cloud access gate completed successfully and reported decision STOP. A green workflow means the gate executed correctly, not successful listing extraction.

No HTTP request to the search page was made in this cloud experiment. Playwright was not launched. Listing HTML, hydration data and browser-loaded JSON were not requested. No CAPTCHA or other protection was bypassed. There was no manual session, cookie import, proxy, stealth configuration or endpoint guessing.

Verified listings: 0. The target of five real ads in each of two independent cloud collection runs was not achieved. No second collection run was started after the access gate failed. Therefore this experiment cannot establish whether a cloud browser would receive a CAPTCHA; the existing local Radware observations are separate evidence only.

The experiment workflow exists only on the isolated yad2-feasibility-20261014 branch, has no schedule, and runs only on changes to its own workflow file. It does not check out the project, load project secrets, write to Neon or send Telegram messages. Existing project workflows and adapters were not modified.

Any later collection experiment needs a permitted access arrangement with Yad2; this result does not establish one.
