# CLAUDE.md — Defensor

## Identity

Spanish-language AI legal advocate for patients denied healthcare in Latin America.
Reads denial documents with vision, identifies violations of Peruvian patient-rights
law, drafts formal complaints, follows up autonomously via Managed Agents.

Built solo by Abel Mancilla (Lima) for the Built with Opus 4.7 hackathon.
**Deadline: April 26, 2026, 7pm Lima.**

**ADVOCACY tool, not clinical.** Never diagnose. Never recommend treatment.
We help patients access care they're entitled to.

## Hard rules

1. Spanish-first for every user-facing surface. English only in code/comments.
2. Never medical advice. If asked "what disease do I have?" — refuse and redirect.
3. Every legal citation references a real article linkable to a PDF in `/legal-corpus`. No invented law. If uncertain: "consulte a un abogado."
4. Every patient-facing output ends with: *"Defensor no reemplaza a un abogado. Esta es información legal, no asesoría legal."*
5. Python 3.11+, TypeScript strict, no `any`. If you can't type it, stop and ask.
6. Commit after every working feature. Judges read commit history.
7. Every agent gets ≥3 gold-standard fixtures before merge.
8. API keys in `.env.local` only. Never commit. Rotate if leaked.

## Tech stack (fixed)

- **Frontend**: Next.js 16 App Router + TS strict + Tailwind v4 + Shadcn/ui
- **Agents**: Python 3.11 + Claude Agent SDK + FastAPI (local) / Railway (prod)
- **Model**: `claude-opus-4-7` (1M-context variant where needed)
- **Storage (local dev)**: JSON files in `tmp/cases/` via `MemoryAgent`
- **Storage (prod browser)**: `sessionStorage` keyed `case:<uuid>` + `batch:lastUpload` — Vercel filesystem is ephemeral and per-invocation, so file-based storage cannot survive between requests there. The browser holds the case state for the demo session.
- **PDF support**: `pypdfium2` converts the first page of a PDF upload to PNG inside `/vision` before passing bytes to the Anthropic vision API (which only accepts images).
- **Managed Agents**: beta header `managed-agents-2026-04-01`
- **Notifications**: Twilio cut — Follow-Up events stored in case file instead
- **Deploy**: Vercel (frontend, free Hobby plan) + Railway (Python agents, free $5 credit — no card needed for trial)

Do NOT add: LangChain, vector DBs (1M context loads the corpus directly), Docker Compose, Redis, custom auth.

## Deploy notes

- **Vercel** — free Hobby plan. Serverless function timeout caps at 60s, which is shorter than a full Vision + Violation + Channel + Drafter chain on Opus 4.7. To avoid `FUNCTION_INVOCATION_TIMEOUT`, the browser calls Railway directly for `/vision` and `/analyze`; the Next.js `/api/analyze` route is no longer in the critical path.
- **Railway** — preferred over Fly.io. Gives $5 free credit/month, no credit card required for trial. Auto-detects Python from `requirements.txt`. Procfile starts `uvicorn agents.server:app`. `.python-version` pins 3.11.
  - Fly.io alternative: requires credit card on file (~$0.05–$0.20 for 2-day demo, no Pro plan needed).
- **CORS**: FastAPI allows `https://defensor-sage.vercel.app` and `http://localhost:3000` so the browser fetch from Vercel's domain succeeds.
- **Env vars**:
  - **Railway**: `ANTHROPIC_API_KEY` (required).
  - **Vercel**: `NEXT_PUBLIC_AGENTS_URL` (required, browser-side — points to Railway). `AGENTS_URL` (optional, server-side fallback for the legacy `/api/analyze` route).
- **Live URLs**: frontend `https://defensor-sage.vercel.app`, agents `https://web-production-1cda.up.railway.app`.

## Local environment

Venv lives at `../defensor` (one level above repo, outside git). Activate before every Python command or npm script that shells to Python.

- Git Bash: `source ../defensor/Scripts/activate`
- PowerShell: `..\defensor\Scripts\activate`

Next.js API routes talk to Python FastAPI at `http://localhost:8000`. Run both processes side by side.

### Commands

```
npm run dev            Next.js frontend (port 3000)
npm run agents         Python FastAPI (port 8000)
npm run test:agents    Pytest across /agents and /tests
npm run typecheck      tsc --noEmit
```

## Project structure

```
/app                    Next.js frontend
  page.tsx              ✅ upload (multi-file) + real % progress bar +
                           Maxima Legal-inspired design (navy + rose)
  result/[caseId]/      ✅ client component, reads sessionStorage,
                           shows numbered chip nav for batch uploads
  api/analyze/          ⚠️ legacy server route (kept as fallback only;
                           browser bypasses it to avoid Vercel 60s cap)
/agents                 Python agents — all implemented except orchestrator/
  vision/               ✅ reads document images → structured fields
  violation/            ✅ maps vision output → Ley 29414 violations
  channel/              ✅ deterministic routing → filing authority
  drafter/              ✅ drafts formal complaint letter (legal-register Spanish)
  memory/               ✅ case file I/O + event log (no LLM calls)
  follow_up/            ✅ 25-day autonomous follow-up loop (Managed Agents)
  orchestrator/         ❌ not built — /analyze endpoint covers this
  server.py             ✅ FastAPI: /vision /violation /channel /drafter /analyze
                           — CORSMiddleware + PDF→PNG via pypdfium2
/legal-corpus           ✅ ley-29414.md (Ley 29414 key articles)
/country-modules        ✅ peru/ colombia/ mexico/ — config.json per country
/tests/fixtures         ✅ vision/ (3 PNG), violation/ (3 JSON), channel/ (3 JSON),
                           drafter/ (3 JSON), follow_up/ __init__, memory/ (inline)
/lib /components        ✅ types.ts, case-storage.ts (legacy), button only
/docs /demo             ✅ storyboard.md (5-beat 3-min script)
Procfile, .python-version    ✅ Railway deploy config
```

## Conventions

- Spanish for user-facing. English for code/tests/docs.
- Legal citations: `Ley 29414, Art. 15`.
- Each agent: `/agents/<name>/prompt.md` + `schema.json` + `agent.py`.
- **Never** call `anthropic.messages.create` directly from a UI handler — always through an agent class.

## Opus 4.7 capabilities (name these in the demo)

- 3.75 MP vision → Vision Agent reads phone photos
- Managed Agents → Follow-Up runs 25 days autonomously
- File-system memory → patient case files persist across sessions
- 1M context → full legal corpus loads at once for legal reasoning
- Literal instruction following (xhigh effort) → Spanish legal-register generation

## Cut list (do NOT build)

- Symptom checking / disease prediction (Babylon trap)
- EsSalud portal scraping (CAPTCHA-walled, time sink)
- Patient-to-doctor messaging (scope creep)
- Payments (scope creep)
- Native mobile (web is enough for demo)

## Demo requirements

- Opens with Abner Rivera's post-mortem appointment story
- Live read of a real phone photo on stage
- Managed Agent event-history replay at 100x
- Persona switch Peru → Colombia → Mexico in 15 seconds
- Closes with a civil-society quote

## Day-by-day plan

- **Day 1 — Apr 23 ✅**: Repo + Vision Agent end-to-end. Upload → `/api/analyze` → FastAPI `/vision` → `tmp/cases/<uuid>.json` → `/result/[caseId]` renders fields. Synthetic fixture marked *SINTÉTICO / NO REAL*. Test skips without `ANTHROPIC_API_KEY`.

- **Day 2 — Apr 24 ✅** *(completed Apr 25)*: Violation + Channel + Drafter agents fully implemented.
  - `ViolationAgent` — identifies Ley 29414 violations from vision output, with field-alias normalization for model output variance.
  - `ChannelAgent` — deterministic routing table (EsSalud/MINSA/EPS/private) + LLM-generated Spanish explanation. Driven by country-module configs.
  - `DrafterAgent` — formal complaint letter in legal-register Spanish, 8192 token budget, alias normalization + `legal_articles_cited` fallback extraction.
  - `/agents/server.py` — added `/violation`, `/channel`, `/drafter`, `/analyze` (orchestration) endpoints.
  - Frontend — `lib/types.ts` extended with full type coverage; `/result/[caseId]` now shows violations + channel + letter.
  - `legal-corpus/ley-29414.md` — key articles of Ley 29414 (Art. 2, 15, 29).
  - **Note**: `claude-opus-4-7` does NOT support assistant prefill. All agents use `_extract_json()` helper with regex to extract JSON from model responses.

- **Day 3 — Apr 25 ✅**: Memory + Follow-Up Managed Agent + country modules + all fixtures.
  - `MemoryAgent` — pure file I/O over `tmp/cases/`, `FollowUpEvent` model, `StoredCaseData` schema.
  - `FollowUpAgent` — 5-step 25-day schedule (days 1/7/15/20/25), one API call per step, `replay_events()` for 100x demo. Uses `managed-agents-2026-04-01` beta architecture.
  - Country modules — `peru/`, `colombia/`, `mexico/` each with `config.json` (law, authority, routing, URLs). Channel Agent now reads these at runtime.
  - Gold-standard fixtures — 3 per agent across vision/violation/channel/drafter. 3 PNG synthetic images (synthetic, Abner Rivera EsSalud, MINSA).
  - **21/21 tests pass** live against API. TypeScript clean.
  - Supabase and Twilio cut — JSON file persistence is sufficient for demo.

- **Day 4 — Apr 26 ✅**: Deploy + demo storyboard + UX polish.
  - [x] `Procfile` + `.python-version` for Railway (Python agents)
  - [x] Vercel deploy (Next.js frontend, Hobby plan)
  - [x] `ANTHROPIC_API_KEY` set in Railway dashboard
  - [x] `NEXT_PUBLIC_AGENTS_URL=https://web-production-1cda.up.railway.app` set in Vercel
  - [x] Demo storyboard at `/demo/storyboard.md` (5 beats, 3 min)
  - [x] PDF support added (pypdfium2 → PNG conversion server-side)
  - [x] Multi-document upload (process all, batch nav on result page)
  - [x] Real % progress bar during analysis
  - [x] Maxima Legal-inspired redesign (navy + rose accents)
  - [x] Architecture pivot: browser → Railway direct (sidesteps Vercel 60s cap and ephemeral filesystem)
  - [x] CORS middleware on FastAPI for the Vercel origin
  - [ ] Final hackathon submission

### Lessons learned (Day 4)

- Vercel Hobby caps serverless functions at 60 s, and a full 4-call Opus 4.7 chain can exceed that. The fix is architectural — call the long-running backend from the browser, not from a Vercel serverless function. `export const maxDuration = 60` only ratchets the cap up to the plan max; it does not unlock more.
- Vercel's per-invocation filesystem means file-based case storage (`tmp/cases/<uuid>.json`) cannot be read back by a later request — the result page would always 404. `sessionStorage` in the browser is the simplest substitute for a demo; a real deployment would need Supabase or KV.
- `process.env.AGENTS_URL ?? "http://localhost:8000"` doesn't fall back when the env var is set to an empty string; use `||` if you want empty values to also fall back. Bit us once with `Failed to parse URL from /vision`.
- Browser-side env vars in Next.js need the `NEXT_PUBLIC_` prefix. `AGENTS_URL` (server) and `NEXT_PUBLIC_AGENTS_URL` (browser) are separate variables and both may need to be set.
- TS strict + `noUncheckedIndexedAccess` makes `array[i]` return `T | undefined`. Use `for (const [i, x] of arr.entries())` for definite element types, or `arr[i]?.foo ?? ""` at the use site.
- Anthropic vision API only accepts image MIME types — PDFs must be rasterized server-side. `pypdfium2` is a Python wheel with no system deps, perfect for Railway.

Do not merge features out of day order without approval.

## When unsure

Stop and ask. Don't guess legal text, invent article numbers, or fabricate patient names. Real vulnerable people. Precision matters.
