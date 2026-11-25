---
name: ui-check
description: Run TraceLayer locally and take Playwright screenshots of a changed page on desktop and mobile. Use when a change is visible to users, or when asked to "test it on mobile".
---

# UI check

The goal is to look at the change the way a user would, on a laptop and on a phone. Use Playwright's device profiles, not hand-picked pixel sizes.

## 1. Run the app

```bash
cd backend && uvicorn main:app --port 8000            # needs Postgres + backend/.env
cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev -- -p 3000
```

If those ports are taken, pick others and set `NEXT_PUBLIC_API_URL` to match. Add the frontend origin to `CORS_ORIGINS` for that run.

**Agents:** `core/config.py` auto-loads `.env` from the working directory, and startup runs migrations and schedulers.
So an agent should never start the backend from `backend/` with your real `.env`. Run uvicorn from a scratch directory
with `--app-dir <repo>/backend` and `PYTHONPATH=<repo>/backend`, using `env -i` and explicit dummy values
(`APP_ENV=development`, `DATABASE_URL` pointing at a throwaway Postgres, a generated `FERNET_KEY`). Put an `alembic.ini` in
that scratch directory whose `script_location` is the absolute path to the migrations folder.
Use your own local test account. Never paste credentials into scripts or docs. Read them from env vars.

## 2. Screenshot desktop and mobile

Save as `docs/plans/<id>/screenshots/check.mjs` and run it with `node`. Playwright is in npx; run `npx playwright install chromium` once.

```js
import { chromium, devices } from "playwright";
const base = process.env.APP_URL ?? "http://localhost:3000";
const out = process.env.OUT ?? ".";
const browser = await chromium.launch();
for (const [name, profile] of [["desktop", devices["Desktop Chrome"]], ["mobile", devices["iPhone 13"]]]) {
  const page = await (await browser.newContext(profile)).newPage();
  await page.goto(`${base}/login`);           // ← the page you changed
  // ← drive it into the state you changed (fill, click, wait for text)
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: true });
}
await browser.close();
```

## 3. Look at the screenshots

Open each PNG and check:
- the change is visible and the text is readable
- nothing overflows sideways on mobile, and buttons are big enough to tap
- there are no errors in the browser console (collect them with `page.on("console")`)

Add one line per screenshot to `test-report.md`. If you couldn't run the app, say so. Don't skip it silently.
