# BusinessIntelligence.ai — CafeCo KPI-to-Action Engine

A production-grade Streamlit prototype of a **Causal KPI Intelligence-to-Action Engine** for CafeCo, a fictional Indian café chain. The system takes a business user through the full analytical journey — **what happened → why it happened → what if we changed something → what should we do** — combining deterministic analytics, business rules, RAG-based evidence retrieval, and OpenAI LLM narrative generation.

> All data in this prototype is **fully synthetic** — nothing here represents a real business. The dataset is committed as CSV files under `data/synthetic/` and can be regenerated at any time.

---

## 1. Solution Approach

The engine enforces a strict separation between **quantitative truth** and **narrative**:

- **KPI values, baselines, materiality scores, driver rankings, and counterfactual estimates** are all produced by deterministic Python (pandas, scipy, business rules). No LLM touches these numbers.
- **Retrieval-Augmented Generation (RAG)** pulls relevant unstructured evidence (internal emails, ops reports, customer feedback) for a given KPI movement using semantic search over embeddings.
- **The LLM's sole job** is to read the already-computed numbers and retrieved evidence, and explain them in plain language tailored to the active persona. It cannot invent figures or override provided rankings.
- **When evidence is contradictory**, or history is too short to support a strong claim, the engine explicitly says so and abstains from issuing a confident answer.

This mirrors how a real analytics team works: analysts compute the numbers; a writer drafts the memo — the memo cannot change the numbers.

### Requirement mapping

| Project Requirement | How It Is Addressed |
|---|---|
| 1. Detect & prioritise material KPI movements | `kpi_engine.py`: Welch's t-test + business-impact threshold; materiality badge on every KPI card |
| 2. Reconcile heterogeneous data sources | `context.py` joins transactions, staffing, inventory, promotions and feedback before any analysis runs |
| 3. Identify & rank explanatory drivers | `driver_analysis.py`: volume/price decomposition + correlation + business rule scoring; ranked driver bars |
| 4. Generate persona-specific narratives | `narrative.py` + OpenAI API: separate system prompts per persona; LLM only reads pre-computed inputs |
| 5. Communicate uncertainty & abstain when contradictory | Contradiction detector in `retriever.py`; explicit "Contradictory Evidence" alert blocks narrative when triggered |
| 6. Recommend practical actions grounded in business levers | `action_simulator.py` + `persona_config.py`: driver → lever → action → owner → monitoring plan, with persona decision-rights enforcement |
| 7. Learn from analyst & business-user feedback | Feedback store with verdict + driver correction + comment; architecture doc explains how it would tune driver weights and LLM prompts in production |
| 8. Security, cost, latency & scalability constraints | Per-session telemetry page; entitlement enforcement at analytics layer (not just UI); OpenAI fallback to template when API unavailable |

---

## 2. Architecture

```
                         Streamlit UI (app/main.py)
                                   │
                     Persona + Location Entitlement Filter
                         (app/entitlement/entitlement.py)
                                   │
        ─────────────────────────────────────────────────────
        │                          │                         │
  Structured Analytics       RAG / Evidence Layer     LLM (OpenAI API)
  (app/analytics/*)          (app/rag/*)               (app/llm/*)
  ─ KPI engine               ─ ingest → chunk          ─ narrative generation
  ─ Baselines / materiality  ─ embed (OpenAI /         ─ recommendation narration
  ─ Driver decomposition       TF-IDF fallback)        ─ persona-specific prompts
  ─ Counterfactuals          ─ in-memory vector search
  ─ Action simulator         ─ entitlement-filtered
        │                          │                         │
        ─────────────────────────────────────────────────────
                                   │
                      Analysis Context object
                        (app/analytics/context.py)
                                   │
              ───────────────────────────────────────
              │                                     │
       Feedback Store                        Telemetry Log
       (app/feedback/*)                      (app/telemetry/*)
```

### Analytical method table

| Layer | Technique | Used For |
|---|---|---|
| Deterministic | pandas aggregation | KPI current & baseline values |
| Statistics | Welch's t-test (scipy) | Statistical significance of a movement |
| Business rules | Threshold checks | Promotion-ended / stockout flags, business-impact materiality |
| Deterministic | Volume × price decomposition | Splitting revenue into transaction-volume vs pricing/mix effects |
| Statistics | Pearson correlation | Wait-time vs transaction-volume signal |
| RAG | OpenAI embeddings + cosine similarity | Retrieving emails/reports/feedback for a driver query |
| RAG fallback | TF-IDF (scikit-learn) | Used when OpenAI embeddings are unavailable |
| LLM | OpenAI API (`gpt-4o-mini`) | Narrating pre-computed numbers and evidence per persona |
| Deterministic | Assumption-based simulation | Counterfactual and action-simulator impact estimates |

---

## 3. Implementation

### Project layout

```
app/
  config/           settings.py (all config), KPI semantic contract
  data/             synthetic_generator.py, loader.py (CSV → DataFrames)
  analytics/        kpi_engine.py, driver_analysis.py, counterfactual.py,
                    action_simulator.py, context.py
  rag/              ingest.py, embeddings.py (OpenAI + TF-IDF), retriever.py
  llm/              openai_client.py, prompts.py, narrative.py
  entitlement/      entitlement.py — persona → allowed locations
  personas/         persona_config.py — decision-rights per persona
  feedback/         feedback_store.py — in-memory capture
  telemetry/        telemetry.py — latency/token/cost logging
  components/       ui_helpers.py — shared Streamlit UI components
  views/            one module per page (executive_overview, kpi_explorer, ...)
  style.css         all custom CSS (loaded at startup, not embedded in Python)
  main.py           app entry point: sidebar nav, persona/location controls
data/synthetic/     six committed CSV files (transactions, staffing, inventory,
                    promotions, feedback, documents)
tests/              unit tests for the analytics core
.env                API credentials (git-ignored; see .env.example)
```

### Synthetic dataset

`data/synthetic/` contains six CSV files committed to the repository:

| File | ~Rows | Grain |
|---|---|---|
| `transactions.csv` | 245K | Transaction / day / store |
| `staffing.csv` | 20K | Store / hour / day |
| `inventory.csv` | 7.2K | Store / product / day |
| `promotions.csv` | 2 | Campaign |
| `feedback.csv` | 700 | Individual feedback item |
| `documents.csv` | 7 | Internal doc (emails, ops reports) |

`app/data/loader.py` loads these CSVs if present; if missing, it auto-regenerates equivalent data from `synthetic_generator.py` using a fixed seed. Either way, `get_datasets()` wraps the result with `st.cache_resource` so it runs only once per session.

**Seeded scenarios in the generator:**
- Staffing shortage at Mumbai/Bandra with a supporting internal email (drives the wait-time driver and its evidence)
- Cold Brew stockout in Delhi (drives the inventory driver)
- Summer promotion ending before the current period (drives the promotion driver)
- Chai Frappe launched ~21 days ago to demonstrate sparse-history handling
- Conflicting reports at Ahmedabad/Satellite (sales says volume declined; the store manager's email and customer feedback say traffic looked normal) — demonstrates the abstention/contradictory-evidence path

### Persona & entitlement system

Three personas are supported. Selecting a persona pins the app to a simulated entitlement:

| Persona | Location Access | All India View |
|---|---|---|
| CEO / Executive | All cities and stores | ✅ Yes |
| Regional Manager | All cities and stores | ❌ No |
| Store Manager | Individual stores only | ❌ No |

Entitlement is enforced at the **analytics layer**, not just hidden in the UI — every DataFrame is filtered in `entitlement.py` before any KPI or driver calculation runs. The location dropdown only ever shows the locations the active persona is entitled to.

### RAG pipeline

```
Documents + Feedback → chunk (90-word windows, 15-word overlap)
  → embed (OpenAI text-embedding-3-small / TF-IDF fallback)
  → in-memory vector store
  → cosine similarity search (query = driver evidence queries)
  → entitlement filter (only chunks from allowed locations)
  → top-k chunks → LLM prompt context
```

Only the top-k retrieved chunks for a specific query are included in any LLM prompt — the full corpus is never sent. A contradiction detector checks retrieved chunks for conflicting signals before the narrative is generated.

### LLM integration

- All inference goes through `app/llm/openai_client.py` — a thin wrapper around the OpenAI Python SDK.
- Credentials are loaded from `.env` at the project root via `python-dotenv`; the path is resolved as an absolute path relative to `settings.py` so it works regardless of the shell's working directory.
- If the API is unreachable or the key is missing, the app falls back to a clearly-labelled deterministic template narrative — the rest of the prototype keeps working.
- `llm_calls` is reported as `1` only when `openai_client.chat()` receives a successful response; the telemetry page shows the real count.

### CSS architecture

All custom styling lives in `app/style.css` and is injected once at startup via `st.markdown()`. No styles are embedded in Python source files — `main.py` reads the file at runtime, making it easy to iterate on design without touching application logic.

---

## 4. Key Features

### Executive Overview (main page)
- **Material movement alert banner** — highlights revenue movement, direction, materiality label, and p-value
- **4-column KPI card grid** — Revenue, Transactions, Average Ticket, Wait Time (current, delta, baseline, significance)
- **Revenue trend chart with baseline** — 30-day comparable trend with annotated baseline band
- **Driver contribution chart** — ranked horizontal bars showing each driver's attributed share
- **Why did it happen? — interleaved claims + evidence** — 3 insight cards, each followed immediately by its supporting evidence chunk (source type, date, relevance score, quoted text)
- **Strategic Takeaway** — LLM-generated narrative synthesis (gpt-4o-mini), grounded strictly in pre-computed inputs
- **Contradictory evidence path** — when signals conflict, a warning banner replaces the narrative and no recommendation is issued
- **Inline counterfactual** — "What if wait time had stayed at baseline?" with actual vs counterfactual revenue comparison
- **Products & Stores breakdown** — tabbed tables for product-level and store-network performance
- **Recommended Action** — driver → lever → action → owner → monitoring plan, filtered by persona decision rights
- **Analyst Feedback** — one-click verdict buttons (Correct / Partially Correct / Incorrect) + optional comment, scoped to the current insight

### KPI Explorer
- Per-KPI trend chart, movement summary, materiality verdict, driver ranking, and semantic KPI contract

### Driver Analysis
- Ranked driver table with method, confidence, direction, and evidence query
- Expandable evidence per driver — RAG chunks specific to that driver on demand
- Contradiction warning per driver — flags when evidence conflicts
- Alternative hypotheses — explicitly surfaces 2nd/3rd ranked drivers
- Unexplained residual component — honest attribution gap instead of forced 100%

### Counterfactuals
- Five levers: Wait Time, Staffing, Pricing, Promotion, Inventory
- Interactive sliders/toggles per lever
- Actual vs counterfactual vs difference metrics with assumption disclosure

### Action Simulator
- Driver → lever mapping auto-suggestion
- Staffing slider tied to the counterfactual engine (same mathematics, action framing)
- Owner, confidence, and monitoring plan in one view
- Persona decision-rights enforcement — warns when the active persona cannot act on the chosen lever

### Data Sources
- Source metadata table: grain, cadence, freshness, quality score, owner, lineage
- Live row counts for each in-memory dataset this session

### KPI Contract
- Semantic contract for every KPI: definition, formula, business significance, data source, update frequency

### Feedback
- Submit verdicts and driver corrections on any insight
- Session-level audit log
- Architecture explanation of how feedback would tune driver weights and LLM prompts in production

### Telemetry
- Per-analysis log: latency, retrieval count, LLM calls, input/output tokens, estimated cost
- Inference server status panel — checks whether the OpenAI API is reachable
- Session aggregate metrics: total LLM calls, total tokens, estimated cost, average latency

---

## 5. Installing and Running

### 5.1 Python environment

```bash
# Create virtual environment
python -m venv venv

# Activate
# macOS / Linux:
source venv/bin/activate
# Windows PowerShell:
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 5.2 API credentials

```bash
# Copy the example file
cp .env.example .env
```

Then open `.env` and set your key:

```env
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini          # optional override
OPENAI_EMBED_MODEL=text-embedding-3-small   # optional override
```

If `OPENAI_API_KEY` is not set, the app runs with a deterministic template fallback — LLM calls will show as 0 in telemetry.

### 5.3 Running the app

```bash
streamlit run app/main.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 5.4 Running tests

```bash
pytest tests/
```

---

## 6. Suggested Demo Flow

1. **CEO / Executive + All India** — note the material movement alert, KPI cards, trend chart, ranked drivers, and interleaved evidence under each claim.
2. **Switch to Store Manager** — the location dropdown narrows to individual stores only; the narrative and recommendation change to store-level actions.
3. **Switch to Regional Manager** — confirm "All India" is no longer available in the location dropdown.
4. **Switch location to Ahmedabad/Satellite** (as CEO) — trigger the contradictory-evidence / abstention path.
5. **Driver Analysis** — expand "Wait Time / Staffing" to see the Bandra staffing email and ops report surfaced as linked evidence.
6. **Counterfactuals** — try the Wait Time lever and observe the actual vs counterfactual revenue comparison.
7. **Action Simulator** — pick a driver; note how the recommendation is blocked or allowed depending on persona decision rights.
8. **Submit feedback** on Executive Overview, then view the Feedback page history.
9. **Telemetry** — check per-analysis latency, retrieval count, LLM calls, token usage, and estimated cost.

---

## 7. Known Limitations (Prototype Scope)

- **No authentication** — entitlement is simulated via the persona dropdown as specified. In production, this would be replaced by an SSO/RBAC system.
- **In-memory vector store** — rebuilt each session; not a production vector database (Pinecone, Weaviate, pgvector, etc.).
- **Counterfactual and action-simulator impact estimates** use documented business-assumption elasticities, not fitted causal models. This is explicitly surfaced in the UI.
- **LLM cost on Telemetry** reflects actual OpenAI API token pricing and is shown for observability; in the fallback (no API key) state, cost will show as near-zero template token estimates.
- **Feedback store** is in-memory per session. A production deployment would persist verdicts to a database for ongoing driver weight tuning.
