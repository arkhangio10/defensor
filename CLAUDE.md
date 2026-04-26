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
- **Agents**: Python 3.11 + Claude Agent SDK + FastAPI (local) / Fly.io (prod)
- **Model**: `claude-opus-4-7` (1M-context variant where needed)
- **Database**: JSON files in `tmp/cases/` — Supabase cut (not needed for demo)
- **Managed Agents**: beta header `managed-agents-2026-04-01`
- **Notifications**: Twilio cut — Follow-Up events stored in case file instead
- **Deploy**: Vercel (frontend, free Hobby plan) + Railway (Python agents, free $5 credit — no card needed for trial)

Do NOT add: LangChain, vector DBs (1M context loads the corpus directly), Docker Compose, Redis, custom auth.

## Deploy notes

- **Vercel** — free Hobby plan covers everything. No Pro needed.
- **Railway** — preferred over Fly.io. Gives $5 free credit/month, no credit card required for trial. Auto-detects Python from `requirements.txt`. Only needs a `Dockerfile` or `Procfile` — zero app code changes.
  - Fly.io alternative: requires credit card on file (~$0.05–$0.20 for 2-day demo, no Pro plan needed).
- **AGENTS_URL** is the only env var that changes between local dev and prod. Set it in Vercel dashboard pointing to the Railway app URL.

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
/app                    Next.js frontend (api/analyze, result/[caseId])
/agents                 Python agents — all implemented except orchestrator/
  vision/               ✅ reads document images → structured fields
  violation/            ✅ maps vision output → Ley 29414 violations
  channel/              ✅ deterministic routing → filing authority
  drafter/              ✅ drafts formal complaint letter (legal-register Spanish)
  memory/               ✅ case file I/O + event log (no LLM calls)
  follow_up/            ✅ 25-day autonomous follow-up loop (Managed Agents)
  orchestrator/         ❌ not built — /analyze endpoint covers this
  server.py             ✅ FastAPI: /vision /violation /channel /drafter /analyze
/legal-corpus           ✅ ley-29414.md (Ley 29414 key articles)
/country-modules        ✅ peru/ colombia/ mexico/ — config.json per country
/tests/fixtures         ✅ vision/ (3 PNG), violation/ (3 JSON), channel/ (3 JSON),
                           drafter/ (3 JSON), follow_up/ __init__, memory/ (inline)
/lib /components        ✅ types.ts, case-storage.ts, frontend components
/docs /demo             ❌ storyboard pending (Day 4)
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

- **Day 4 — Apr 26 (7pm)**: Deploy + demo storyboard + submit.
  - [ ] `Dockerfile` + `Procfile` for Railway (Python agents) — zero app code changes, just config
  - [ ] Vercel deploy config (Next.js frontend, free Hobby plan)
  - [ ] Set `ANTHROPIC_API_KEY` as env var in Railway dashboard
  - [ ] Set `AGENTS_URL=https://your-app.railway.app` in Vercel env vars
  - [ ] Demo storyboard: Abner Rivera story, live photo read, Follow-Up 100x replay, Peru→Colombia→Mexico switch
  - [ ] Final submission

Do not merge features out of day order without approval.

## When unsure

Stop and ask. Don't guess legal text, invent article numbers, or fabricate patient names. Real vulnerable people. Precision matters.
