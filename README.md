# algorithm-lower-triangular

> **One-line summary** — TODO: a single sentence on what this tool does.
> Suggested: "Timetable recommendation for Korea University students, with per-algorithm explanations."

---

## Contents

1. [Overview](#1-overview)
2. [Product](#2-product)
3. [Program structure](#3-program-structure)
4. [Core algorithms](#4-core-algorithms)
5. [Further reading](#5-further-reading)

---

## 1. Overview

### 1.1 Program description

`algorithm-lower-triangular` is a timetable recommendation tool for Korea University students. It picks the top-K class schedules that balance travel time, credit limits, and per-course importance, and explains *why* each schedule was produced — broken down by the algorithm (sort, search, greedy, DP, …) that contributed to it, which makes it useful as both a planning aid and a learning companion for an algorithms course.

The project follows a **spec-first** workflow: humans design the algorithm plan and structure as text specifications under [`claude/`](claude/), and Claude implements those specs in [`app/`](app/) (backend) and [`frontend/`](frontend/). Every behavior in the code has a matching decision document in `claude/`.

**Pointing a gen-AI assistant (Claude, GPT, etc.) at the `claude/` folder is the fastest way to get deeper context on any part of the system** — priorities ([`base/product.md`](claude/base/product.md)), the algorithm tree ([`base/drafts/algorithm-tree.md`](claude/base/drafts/algorithm-tree.md)), interface contracts ([`base/architecture.md`](claude/base/architecture.md)), per-area working rules (`<area>/team-guide.md`), and the DB schema ([`server/db/`](claude/server/db/)) all live there as plain markdown structured for both humans and AIs to navigate.

### 1.2 Tech stack

| Layer               | Choice                            | Notes                                         |
| ------------------- | --------------------------------- | --------------------------------------------- |
| Backend language    | Python 3.12                       | `.venv/` virtual environment                |
| Web framework       | FastAPI 0.136 + Starlette 1.0     | `app/main.py`                               |
| ASGI server         | `uvicorn[standard]` 0.48        | pinned in `requirements.txt`                |
| Validation / models | Pydantic v2 + pydantic-settings   | `app/schemas/`, `app/core/config.py`      |
| LLM                 | Upstage Solar (`solar-pro2`)    | stdlib `urllib`, `app/libs/llm_client.py` |
| Database            | Supabase (design only, not wired) | schema design in `claude/server/db/`        |
| Frontend language   | TypeScript                        | `frontend/src/`                             |
| Frontend framework  | React 18 + Vite 5                 |                                               |
| Frontend styling    | Tailwind CSS 3                    |                                               |
| Tests               | pytest 9                          | `tests/`                                    |
| Container           | Docker Compose                    | production-like HTTPS topology                |

### 1.3 Team members

| Name                   | Student ID | Role                                             |
| ---------------------- | ---------- | ------------------------------------------------ |
| 강규현 ( team leader ) | 2024270639 | project management, claude management            |
| 정현빈                 | 2024270652 | planning, direction making                       |
| 강은비                 | 2021270684 | llm including, code review, environment setting  |
| 박재희                 | 2024270624 | documentation, testing, presentation preparation |

### 1.4 How to run

**Environment setup (required)** — create a `.env` file at the project root and set `UPSTAGE_API_KEY` to your Upstage Solar API key (used by `app/core/config.py`):

```env
UPSTAGE_API_KEY=your_key_here
# optional overrides (defaults shown)
# UPSTAGE_API_URL=https://api.upstage.ai/v1/chat/completions
# UPSTAGE_MODEL=solar-pro2
# UPSTAGE_TIMEOUT_S=12.0
```

Without this key, LLM features (natural-language input parsing and result explanations) return `503 LLM_UNAVAILABLE`. The rest of the app — A·B·C algorithm pipeline, top-K timetables, score breakdown, infeasibility diagnostics — still works normally.

`.env` is git-ignored. Do not commit your key.

#### 1.4.1 Quick start — local without Docker (recommended for development)

Open two PowerShell windows.

```powershell
# (Terminal 1) Backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```powershell
# (Terminal 2) Frontend
cd frontend
npm install
npm run dev
```

Access:

- Timetable UI → `http://localhost:5173` (Vite proxies `/api` to port 8000)
- Backend OpenAPI → `http://localhost:8000/docs`
- Health check → `curl http://localhost:8000/healthz` → `{"status":"ok"}`

#### 1.4.2 Docker Compose — production-like (HTTPS)

> ⚠️ `docker-compose.yml` describes a **production-like HTTPS topology** (nginx TLS termination + Let's Encrypt + FastAPI).
> For local development, use 1.4.1 instead.

```bash
# Issue Let's Encrypt certificate (one-time)
EMAIL=you@example.com ./init-letsencrypt.sh

# Normal startup
docker compose up --build
```

For host preparation, domain, and port setup: TODO (add a section, or see `claude/server/team-guide.md`).

---

## 2. Product

### 2.1 Purpose

Every semester, Korea University students sit in front of a spreadsheet trying to satisfy at least four constraints at once: **no time conflicts**, **credit limits**, **prioritizing the courses they actually want to take**, and **realistic travel time** across campus buildings. Hand-solving this is error-prone — the constraint you forgot usually surfaces only after registration closes.

The school portal only checks for time conflicts. General-purpose timetable apps lack the building-distance data. No existing tool produces a schedule that is *faster than building it by hand*, *guarantees no constraint was skipped*, and **explains why each schedule was chosen at the level of individual algorithms**. This project fills that gap.

A secondary purpose: the five algorithm categories from the course (sorting, searching, greedy, dynamic programming, and "other") appear here **because they are actually needed** — not as forced demonstrations — making the project an authentic end-to-end use case for what is taught in class.

Authoritative source: [`claude/base/product.md`](claude/base/product.md) §2.

### 2.2 Expected impact

**Qualitative.** Manual Excel-based timetable building disappears; the flow collapses to *enter course candidates → review N suggested timetables → decide*. Because each decision is made *with* an understanding of why a given schedule was produced, mid-semester regret and re-planning drop. The algorithm decomposition tree also turns the tool into a learning aid — each step makes explicit *which algorithm category was used, and why it was the right fit*.

**What kinds of preferences are covered.** The tool distinguishes two kinds of preferences and handles each differently.

The first kind — *universally valued factors* — includes minimizing building-to-building travel, securing free periods between back-to-back classes, hitting a target number of class days per week, respecting credit limits, and similar concerns shared by most students. These map cleanly onto numerical knobs (`travel_time_lambda` λ₁, `compactness_lambda` λ₂, `min_break_minutes`, `target_active_days`, `time_window_lambda` λ₄, `daily_span_lambda` λ₅, …) that live in `PreferenceVector` and are exposed directly in the form.

The second kind — *personal circumstances* — is open-ended and intensely individual: "I work part-time Tuesday afternoons", "I commute by intercity bus on Fridays so morning classes are impossible", "I want my advisor Professor Hong's section regardless of the time slot", "I'm taking the LEET prep course so leave Wednesday evenings free". These do not fit cleanly into any fixed schema. Asking users to translate every life situation into λ-values, blackout windows, and professor-preference dictionaries defeats the purpose of having a tool — most users won't, and many couldn't.

**This is where the LLM comes in.** Free-text input ("금요일 아침은 통학이라 비워주세요, 이교수님 운영체제 듣고 싶어요") is parsed by Upstage Solar into a *delta* on `PreferenceVector` — blackout windows, professor preferences, must-include / exclude locks — that the algorithm then consumes like any other structured input. The LLM **translates** personal context into the universal schema; it never **decides** the timetable. That separation is the §2.4 system invariant, and it keeps the personal-context surface additive without weakening any guarantee from §2.3 #1–#3 (correctness, explainability, faithfulness to user importance).

**Quantitative** — target values, measured per [`product.md`](claude/base/product.md) §3.2:

| Metric                                        | Target      |
| --------------------------------------------- | ----------- |
| Algorithm runtime (excluding LLM)             | ≤ 50 ms    |
| End-to-end user response time (including LLM) | ≤ 3 s      |
| Constraint-violating responses                | 0           |
| Algorithm categories surfaced in the response | ≥ 4 (of 5) |
| Top-N diversity (backbone overlap)            | ≤ 80 %     |

### 2.3 Priorities — what wins when trade-offs arise

```
1. (highest) Correctness            — zero constraint violations
2.           Explainability         — "why this schedule" traceable per algorithm
3.           Faithfulness to user importance — user weights reflected as-is
4.           Diagnosis on infeasible input    — "which constraint to relax"
5.           Verifiability          — response structure a human can hand-check
6.           Response speed         — algorithm ≤ 50 ms, end-to-end ≤ 3 s
7.           Result diversity       — top-N are meaningfully different
8.           Minimal travel         — used as a tie-breaker
9.           User control           — deprioritized for this project's scope
10. (lowest) Result stability       — deprioritized for this project's scope
```

Detailed rules and trade-off exceptions: [`claude/base/product.md`](claude/base/product.md) §4.

### 2.4 System invariant

> **The timetable decision is always made by the algorithm.**
> The LLM is involved only at two points: (a) converting free-text input into a `PreferenceVector`, and (b) producing natural-language explanations of the result.
> No value the LLM produces is reflected in the result without algorithmic verification.

Breaking this invariant simultaneously damages priorities §2.3 #1, #2, and #3.

### 2.5 Non-goals

> What we explicitly *do not* do — the boundary that defines our scope.

- No course-registration automation. No GPA prediction. No recommendations based on instructor evaluations.
- No multi-semester curriculum planning. No data from other universities.
- Not mobile-first (PC browser first).
- No friend-schedule matching.

---

## 3. Program structure

### 3.1 Folder layout

```
algorithm-lower-triangular/
├── app/                          FastAPI backend
│   ├── main.py                   entry + CORS + validation error handler
│   ├── api/
│   │   ├── api.py                /api/v1 router bundle
│   │   └── endpoints/
│   │       ├── timetable.py      POST /api/v1/timetable/solve
│   │       └── utils.py          health checks, etc.
│   ├── libs/                     pure functions — the algorithm core
│   │   ├── timetable.py          root recommend() — A→B→C orchestration
│   │   ├── feasibility.py        A node
│   │   ├── valuation.py          B node
│   │   ├── selection.py          C node
│   │   ├── floyd_warshall.py · activity_selection.py · knapsack.py
│   │   ├── merge_sort.py · lcs.py · binary_search.py
│   │   ├── llm_client.py         Upstage single entry point (urllib)
│   │   └── llm_context.py        prompt assembly
│   ├── schemas/                  Pydantic contracts
│   │   ├── common.py             Course · TimeSlot · Weekday · Category · Requirement · BlackoutWindow
│   │   ├── preferences.py        PreferenceVector
│   │   ├── feasibility.py        FeasibilityResult · InfeasibilityReason
│   │   ├── valuation.py          ScoreBreakdown · ScoredSchedule · ValuationResult
│   │   └── selection.py          SelectionResult · Rationale · StageCode
│   ├── core/config.py            .env loading (pydantic-settings)
│   └── db/, crud/                Supabase client (not wired yet)
├── frontend/                     Vite + React + TypeScript + Tailwind
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/PreferenceForm.tsx  input form (left panel)
│   │   ├── api/client.ts                  {detail, code} error normalization
│   │   └── types/timetable.ts             backend-mirror types
│   ├── nginx.conf                proxies /api → backend
│   └── Dockerfile                multi-stage (node → nginx)
├── claude/                       design and decision docs (base/ is authoritative)
│   ├── base/                     product.md · architecture.md · drafts/algorithm-tree.md ...
│   ├── server/                   server-area guide + DB design (one file per table)
│   ├── frontend/                 frontend-area guide
│   └── llm-include/              prompt templates
├── tests/                        pytest
├── docker-compose.yml            production-like (HTTPS) Docker
├── Dockerfile.backend            python:3.12-slim + uvicorn
└── requirements.txt
```

### 3.2 Layer responsibilities

Detailed boundary rules: [`claude/base/architecture.md`](claude/base/architecture.md) §3. The single principle is **one-way dependency**: `frontend → server → LLM API`, and `server` reads from `llm-include` by file path (never by import).

**frontend** (`frontend/`) — owns user-facing UX, and nothing more.

- *Does*: render the preference form (`components/PreferenceForm.tsx`), POST to `/api/v1/timetable/solve`, render the response, normalize `{detail, code}` errors into user-friendly messages (`api/client.ts`), keep TypeScript types mirroring backend Pydantic (`types/timetable.ts`).
- *Does not*: call any LLM provider directly, hold any API key, talk to the database, or build prompt strings. All four belong to the server.

**server** (`app/`) — owns validation, the algorithm pipeline, and the single LLM entry point.

- *Routes* (`app/api/endpoints/`): `timetable.py` exposes `POST /api/v1/timetable/solve` and validates the body with `TimetableRequest` (Pydantic); `utils.py` carries health endpoints.
- *Schemas* (`app/schemas/`): `preferences.py` defines `PreferenceVector` — the *only* input form the algorithm tree accepts; `feasibility.py` / `valuation.py` / `selection.py` define the three internal contracts plus `InfeasibilityReason`, `StageCode`, and `ScoreBreakdown`.
- *Algorithm core* (`app/libs/`): pure functions. `timetable.recommend()` orchestrates A → B → C; the individual algorithm files (`floyd_warshall.py`, `activity_selection.py`, `knapsack.py`, `merge_sort.py`, `lcs.py`, `binary_search.py`) are reused, never duplicated.
- *LLM access* (`app/libs/llm_client.py`): the *only* module allowed to import or call an LLM provider. Prompts come from `claude/llm-include/` via `app/libs/llm_context.py` — never hardcoded in routes.
- *Configuration* (`app/core/config.py`): the *only* module that reads `.env` (Pydantic `BaseSettings`). All other code reads settings from `config.settings`, so secrets and feature flags have exactly one source of truth.

**llm-include** (`claude/llm-include/`) — owns prompt templates and domain material, nothing else.

- *Does*: holds `.md` prompts (e.g. `prompts/preference_extract.md`) and domain knowledge the LLM should reference.
- *Does not*: contain any Python module. The server reads these files **by path**, not by import — keeping prompts swappable without code changes.

### 3.3 Internal contracts between A · B · C

Three Pydantic schemas sit between the algorithm-tree nodes. Each node can be swapped or instrumented without touching the others, as long as it produces / consumes the right contract.

| Contract              | Defined in                     | Producer | Consumer            | Key fields                                                                                                                      |
| --------------------- | ------------------------------ | -------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `FeasibilityResult` | `app/schemas/feasibility.py` | A        | B (and C via reuse) | `candidates`, `must_include_mask`, `compatible[(id,id)]`, `travel_time_table`, `ordered_by_start`, `infeasibility?` |
| `ValuationResult`   | `app/schemas/valuation.py`   | B        | C                   | `top_k_candidates: list[ScoredSchedule]`, `num_total_feasible`, `best_score`, `k_threshold_score`                       |
| `SelectionResult`   | `app/schemas/selection.py`   | C        | HTTP response       | `ranked_schedules`, `pairwise_diff`, `course_rationale`, `diversity_adjustment_applied`                                 |

Each `ScoredSchedule` carries its full `ScoreBreakdown` (10 named fields — see §4.5), so every term that contributed to the score can be inspected separately by the UI and the LLM explainer.

**Short-circuit**: when `FeasibilityResult.infeasibility` is set, the root `recommend()` returns the report directly and B · C are skipped. The same `InfeasibilityReport` becomes the body of the API response (with `selection: null`).

### 3.4 Request / response flow

```
┌────────────┐                                                      ┌──────────────────┐
│  frontend  │ ─── POST /api/v1/timetable/solve ───────────────────►│ endpoints/       │
│            │      { preference, top_n?, explain? }                │   timetable.py   │
└────────────┘                                                      └──────────────────┘
                                                                            │
                                                                            ▼
              ┌─── invalid input (422) ───────────────────  TimetableRequest validation
              │                                                             │  ok
              ▼                                                             ▼
      { "detail": "...",                                       libs.timetable.recommend(
        "code": "VALIDATION_ERROR" }                             prefs, building_codes,
                                                                 base_walk_minutes, top_k)
                                                                            │
                                            ┌───────────────────────────────┴───────────────────────────────┐
                                            ▼                                                               │
                                       A — feasibility(...)                                                 │
                                            │                                                               │
                                            ├── infeasibility ─────────────────────────────┐                │
                                            │                                              │                │
                                            ▼ pass                                         ▼                │
                                       B — valuation(feas, prefs, top_k)                                    │
                                            │                                                               │
                                            ▼                                                               │
                                       C — selection(feas, val, prefs)                                      │
                                            │                                                               │
                                            ▼                                                               │
                          (optional) explain=True and UPSTAGE_API_KEY set                                   │
                            → llm_context → llm_client → Upstage Solar                                      │
                            (key missing or timeout → explanation=null, 503 LLM_UNAVAILABLE)                │
                                            │                                                               │
                                            ▼                                                               ▼
                       TimetableResponse {                                       TimetableResponse {
                         selection: SelectionResult,                               selection: null,
                         explanation: str | null,                                  infeasibility: InfeasibilityReport,
                         infeasibility: null,                                      explanation: null,
                       }                                                         }
```

**Error / status conventions** (uniform across the API):

| Where                                            | Body                                                                                        |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| Validation failure (422)                         | `{ "detail": "<field>: <reason>", "code": "VALIDATION_ERROR" }`                           |
| LLM provider unreachable (503)                   | `{ "detail": "...", "code": "LLM_UNAVAILABLE" }`                                          |
| Infeasible input (200, with `selection: null`) | the `code` carries an `InfeasibilityReason` value (e.g. `MUST_INCLUDE_PAIR_CONFLICT`) |

The shape is identical for the frontend, which uses `api/client.ts` to surface `detail` to the user and branch on `code` for retry / hint UX.

---

## 4. Core algorithms

### 4.1 A·B·C responsibility tree

```
[root] recommend()  — optimal timetable recommendation
 ├── [A] Feasibility analysis  — "which combinations pass the hard constraints"
 │    ├── A-1 Course pool filtering    hash · blackout (per-slot any) · exclude · locks
 │    ├── A-2 Conflict relations       sort · travel time (per-slot building · min_break) · group exclusion
 │    └── A-3 Pruning                  activity selection · credit reachability · group feasibility
 ├── [B] Valuation                 — "how good is each combination that passed"
 │    ├── B-1 Course value v(c)    importance × credit + category · requirement · professor + building + time-of-day
 │    ├── B-2 Transition cost      lookup into the Floyd-Warshall table precomputed in A
 │    └── B-3 Optimization + top-K  0-1 knapsack upper bound + backtracking + constraint checks
 └── [C] Selection                  — "what to show and how"
      ├── C-1 Ranking · diversity   stable merge sort + Jaccard with 5% concession
      ├── C-2 Pairwise comparison   LCS — common backbone + differing courses
      └── C-3 Rationale index       inclusion / exclusion reasons (hash + StageCode)
```

Early exit: when A produces an `InfeasibilityReason`, B and C are skipped.
Full specification: [`claude/base/drafts/algorithm-tree.md`](claude/base/drafts/algorithm-tree.md) §9.

### 4.2 Algorithm-category mapping

All five categories (sorting, searching, greedy, dynamic programming, other) are used **because they are needed**, not for show.

| Category  | Algorithm                          | Used in                        |
| --------- | ---------------------------------- | ------------------------------ |
| Sorting   | Time sort                          | A-2                            |
| Sorting   | Stable merge sort                  | C-1                            |
| Searching | Hash lookup                        | A-1, B-1, C-3                  |
| Searching | Binary search (lower_bound)        | B (demonstration)              |
| Greedy    | Activity selection                 | A-3                            |
| DP        | Floyd-Warshall                     | precomputed in A → B-2 lookup |
| DP        | 0-1 knapsack (upper-bound pruning) | B-3                            |
| DP        | LCS                                | C-2                            |
| Other     | Backtracking                       | B-3                            |

Optional (not wired) — Dijkstra · topological sort · edit distance · matrix-path DP.

### 4.3 Input model — PreferenceVector

`PreferenceVector` is the single Pydantic object the algorithm tree reads. Every input falls into one of three buckets:

1. **The course catalog** — which courses are even on the table.
2. **Hard rules** — what a valid schedule *must* or *must not* contain. Violating a hard rule produces **no schedule**, not a low-scoring one.
3. **Soft preferences** — what makes one schedule *better than another*. Higher values mean stronger preference; defaults (`0` or "unspecified") leave the system neutral.

We walk through each bucket the way a user would think about it. Exact field names and types live in [`app/schemas/preferences.py`](app/schemas/preferences.py).

#### 1. The course catalog

Each course you enter carries: a name, credit value, **category** (Major / Double-major / Liberal arts / General elective), **requirement** (Required / Elective / Optional), one or more **time slots** (day + start / end time + the building it meets in), and optionally a professor, a section label, and a `course_group_id`. Sibling sections of the same course share the `course_group_id` so the algorithm knows it should pick at most one of them.

#### 2. Hard rules — what *must* and *must not* be in the result

| What you want to say                                        | Field(s)                                       | Notes                                                             |
| ----------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------- |
| "These specific courses must be in every result."           | `must_include`                               | course IDs                                                        |
| "I never want these courses."                               | `exclude`                                    | course IDs                                                        |
| "I need at least one section of this course (any section)." | `must_include_groups`                        | group IDs                                                         |
| "Drop all sections of these courses entirely."              | `exclude_groups`                             | group IDs                                                         |
| "Don't schedule anything during these times."               | `blackout_windows`                           | day + start–end ranges (e.g.*every Friday morning*)            |
| "Keep my total credits in this range."                      | `credit_min`, `credit_max`                 | inclusive bounds                                                  |
| "I want N courses of category X (e.g. 3–4 majors)."        | `category_count_min`, `category_count_max` | per category                                                      |
| "Give me at least N minutes between back-to-back classes."  | `min_break_minutes`                          | the required gap becomes `max(walking time, min_break_minutes)` |

If no schedule can satisfy all of these, the API returns an `InfeasibilityReport` that names the blocking rule and tells the user which constraint to relax (priority §2.3 #4 — diagnosis on infeasible input).

#### 3. Soft preferences — what makes a schedule *better*

| What you want to say                                                       | Field(s)                                                                            | How it tilts the score                                                                               |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| "I really want this specific course." (per course)                         | `course_importance` (1 – 5; default 3)                                           | `importance × credit` — the largest positive term                                                |
| "I prefer / dislike this category, requirement type, or professor."        | `category_weights`, `requirement_weights`, `professor_preferences`            | per-course bonus / penalty;`professor_preferences` is the decisive signal between sibling sections |
| "I want to avoid (or seek) a particular building."                         | `building_penalties`                                                              | summed over the distinct buildings the course actually uses                                          |
| "Minimise walking between back-to-back classes."                           | `travel_time_lambda` λ₁                                                         | larger → long campus walks hurt the score more                                                      |
| "Squeeze classes into fewer days."                                         | `compactness_lambda` λ₂ + `target_active_days`                                | every active day above the target is penalised                                                       |
| "Don't spread me across too many buildings overall."                       | `diversity_lambda` λ₃                                                           | per distinct building in the whole schedule                                                          |
| "Adjacent classes should be back-to-back" — or "should always have a gap" | `back_to_back_preference`                                                         | sign decides direction                                                                               |
| "Keep my classes inside this time window (e.g. 09:00–18:00)."             | `time_window_lambda` λ₄ + `preferred_start_minute` + `preferred_end_minute` | every minute outside the window is penalised                                                         |
| "Don't make my campus day longer than necessary."                          | `daily_span_lambda` λ₅                                                          | per hour of (last class end − first class start), summed across days                                |
| "Penalise these exact slot times." (fine-grained)                          | `time_penalty_grid`                                                               | exact lookup by `"DAY HHMM-HHMM"` key                                                              |

Each row above becomes its **own line** in the schedule's `ScoreBreakdown` (10 named fields — see §4.5). That separation is what lets the UI and the LLM explainer tell a user *exactly* how much each preference moved the score for the schedule they're looking at.

#### Where does each field come from?

- **Filled directly in the React form** — course catalog · `course_importance` · `must_include` / `exclude` · `credit_min / max` · `blackout_windows` · `target_active_days` · `travel_time_lambda` · `compactness_lambda` · `min_break_minutes`.
- **Filled automatically by the LLM** (the path described in §2.2) — personal-context sentences like *"금요일 아침은 통학이라 비워주세요"* become `blackout_windows`; *"이교수님 운영체제 듣고 싶어요"* becomes a `must_include` plus a `professor_preferences` entry; *"전공 위주로 듣고 싶어요"* becomes a positive `category_weights["전공"]`, and so on. The user never has to type a field name.
- **API only** (programmatic callers can set these; sensible defaults otherwise apply) — `must_include_groups`, `exclude_groups`, `category_count_min / max`, `category_weights`, `requirement_weights`, `building_penalties`, `professor_preferences`, `time_penalty_grid`, `diversity_lambda`, `back_to_back_preference`, `time_window_lambda` (+ window bounds), `daily_span_lambda`.

### 4.4 Schedule building — B-3 in detail

> TODO: tune the depth to your presentation. Starting point below.

**Problem**: From the courses that passed A, select the top-K subsets that maximize score subject to credit range, required groups, category counts, and similar constraints.

**Approach**: 0-1 knapsack upper bound + backtracking.

1. Required courses are pre-placed into `chosen` (locked).
2. Optional courses are sorted in descending **value / credit density** — the upper bound tightens quickly.
3. At each DFS node, `knapsack_01` produces an upper bound on the remaining options; if top-K is already full and the bound cannot beat the K-th threshold, the entire branch is pruned.
4. When a subset is complete, `record()` checks three conditions:
   - meets `credit_min`
   - satisfies `must_include_groups`
   - satisfies `category_count_min/max`
5. Each retained subset is then scored by `_build_breakdown` (sum of 10 fields), sorted, and the top K returned.

Code: [`app/libs/valuation.py`](app/libs/valuation.py), `_enumerate_feasible_subsets`.

### 4.5 Output — ScoreBreakdown (10 fields)

```
total =  core_importance        
```
