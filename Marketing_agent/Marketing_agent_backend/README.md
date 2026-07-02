# Hackathon Launch & Marketing Agent — backend v2

Rebuilt for the Tier-1 scope we agreed on: **pure content generation**,
registrations captured on **your own form**, **no external API credentials**
required to run it.

## What changed from v1

- `config.py` — now also exports `GOOGLE_API_KEY` (from your `GEMINI_API_KEY`) since the real Google ADK reads that env var.
- `memory.py` — rewritten to use **Qdrant in local mode** (no Docker, no cloud account, no API key — just a folder on disk at `qdrant_data/`). Uses the free, offline `BAAI/bge-small-en` embedding model for semantic search.
- `mcp_server.py` — **new**. A small MCP server that exposes the memory layer as a tool (`search_past_campaigns`) so agents can look up similar past content before writing new copy.
- `agents.py` — rewritten on real **Google ADK** (`google.adk.agents.Agent`, `SequentialAgent`, `Runner`), not raw `google.genai` calls. Two agents (`brief_analyst` → `content_generator`) run in a shared session, which is the actual **A2A handoff** — the second agent sees the first agent's plan directly in conversation history. The content generator also has the MCP tool wired in.
- `main.py` — new endpoints matching the hackathon brief (see below). The old `/api/generate-campaign` is gone, replaced by `/api/generate-launch-kit`.
- `requirements.txt` — fixed. **`lyzr-automata` and `lyzr` are both removed** — see the note below, this isn't optional.

## About Lyzr — read this before your pitch

I checked: **every version of the `lyzr` package on PyPI requires Python
<3.12**, and your machine runs Python 3.13. It is not currently
`pip install`-able on your setup — that's not a fixable config issue, it's
the package itself. Two honest paths forward:

1. **Leave it out** (what I did here). The workflow-orchestration role Lyzr would have played — sequencing brief → generate → route — is handled directly by the ADK `SequentialAgent`. If a judge asks, the accurate answer is "we evaluated Lyzr but its current PyPI release doesn't support Python 3.13, so orchestration is handled natively by ADK's SequentialAgent instead."
2. **Get literal Lyzr working**, if you specifically need the import for judging criteria: install Python 3.11 separately, create a second virtual environment with it just for a Lyzr-based orchestration layer, and have that call into this backend. That's real extra setup — say the word and I'll help you wire it that way instead.

I'd only do #2 if something explicitly requires the literal package name to appear in your code.

## Setup

```powershell
cd Marketing_agent_backend
pip install -r requirements.txt
```

Your `.env` only needs the one key you already have:
```
GEMINI_API_KEY=your_key_here
```

Then run it the same way as before:
```powershell
python -m uvicorn main:app --reload
```

First run will download the embedding model (~130MB, one-time, needs
internet, no key required) — you'll see it happen in the terminal the first
time `/api/generate-launch-kit` is called.

## Endpoints

### `POST /api/generate-launch-kit`
```json
{ "name": "...", "theme": "...", "audience": "college students | working professionals | mixed", "rounds": 3 }
```
Returns `{ "raw": "...", "sections": { "tagline": "...", "instagram_poster": "...", "whatsapp_message": "...", "email": "...", "linkedin_post": "...", "platform_listing_blurb": "..." } }`.
Only the sections relevant to the audience get filled in with real content by the model; the pipeline always includes tagline and platform listing blurb.

### `POST /api/round-reminder`
```json
{ "round_number": 1, "days_left": 2 }
```
Returns `{ "message": "..." }` — call this once per day per round from your own scheduler (e.g. a cron job or APScheduler) to get the 3/2/1-days-left messages.

### `POST /api/registration-event`
```json
{ "candidate_name": "...", "hackathon_name": "...", "total_registrations_today": 500, "problem_statement": "..." }
```
Fire this from your own registration form's backend right after you save a new registration. Returns `{ "organizer_alert": "...", "candidate_message": "..." }`.

### `POST /api/analyze-vision-assets`
Unchanged from before — multipart form with `campaign_name` and `image`.

## What's genuinely automated vs. what still needs a human click

Everything above **writes the text**. It does not send WhatsApp messages, post
to Instagram/LinkedIn, submit listings to Unstop/Devpost/HackerEarth, or send
real emails — none of that is wired up, since you don't have those
credentials yet and that was the explicit Tier 1 scope. When you're ready
for Tier 2, the natural next additions are: SMTP/SendGrid for real email
sending (easiest), and Google Calendar/Zoom OAuth for the final-round
scheduler (moderate effort) — both from your original feature list.

## Frontend heads-up

The existing frontend (`index.html` / `app.js`) still points at the old
`/api/generate-campaign` endpoint and expects the old response shape. It
will break against this backend until it's updated to call
`/api/generate-launch-kit` and render the new section list. Say the word and
I'll update it to match.
