# BusinessIntelligence.ai — CafeCo Round 2 Prototype

A working Streamlit prototype of a KPI Intelligence-to-Action Engine for CafeCo, a
fictional Indian cafe chain. The prototype takes a business user from **what
happened** to **why it happened** to **what if we change something** to **what
should we do**, combining deterministic analytics, business rules, RAG-based
evidence retrieval and an OpenAI LLM (via the OpenAI API) for narrative generation.

All data in this prototype is synthetic — nothing here represents a real business.
The dataset is committed as CSV files under `data/synthetic/`, with a generator
script available to regenerate it if needed.

---

## 1. Solution approach

The core idea behind this prototype is a strict separation between **quantitative
truth** and **narrative**:

- KPI values, baselines, materiality scores, driver rankings and counterfactual
  estimates are all produced by deterministic code (pandas, scipy, simple business
  rules). None of these numbers are generated or altered by an LLM.
- Retrieval-augmented generation (RAG) is used to pull relevant unstructured
  evidence (internal emails, operations reports, customer feedback) for a given KPI
  movement, using semantic search over embeddings.
- The LLM's only job is to read the numbers and the retrieved evidence and explain
  them in plain language, tailored to the persona asking. It cannot invent figures
  or override the ranking it's given.
- When evidence is contradictory, or history is too short to support a strong claim,
  the engine says so explicitly instead of forcing a confident answer.

This mirrors how a real analytics team would work: analysts compute the numbers,
and someone (or something) writes the memo — the memo doesn't get to change the
numbers.

---

## 2. Architecture

```
                         Streamlit UI (app/main.py)
                                   |
                     Persona + Location entitlement filter
                                   |
        ------------------------------------------------------------
        |                         |                                |
  Structured Analytics      RAG / Evidence Layer           LLM (OpenAI API)
  (app/analytics/*)         (app/rag/*)                    (app/llm/*)
  - KPI engine               - ingest -> chunk                - narrative
  - Baselines/materiality    - embed (OpenAI embeddings)        generation
  - Driver decomposition     - in-memory vector search         - recommendation
  - Counterfactuals          - entitlement-filtered retrieval    narration
  - Action simulator
        |                         |                                |
        ------------------------------------------------------------
                                   |
                         Analysis Context (app/analytics/context.py)
                                   |
                  Feedback store          Telemetry log
                  (app/feedback/*)        (app/telemetry/*)
```

Analytical logic is intentionally kept separate from narrative generation, so any
piece of the pipeline (data source, embedding backend, LLM provider) can be swapped
without touching the others.

### Where each method is used

| Layer | Technique | Used for |
|---|---|---|
| Deterministic | pandas aggregation | KPI current/baseline values |
| Statistics | Welch's t-test (scipy) | Statistical significance of a movement |
| Business rules | threshold checks | Promotion-ended / stockout flags, business-impact materiality |
| Deterministic | volume x price decomposition | Splitting revenue movement into transaction-volume vs pricing/mix effects |
| Statistics | Pearson correlation | Wait-time vs transaction-volume signal |
| RAG | embeddings + cosine similarity | Retrieving relevant emails/reports/feedback for a driver |
| LLM | OpenAI API (gpt-4o-mini) | Narrating the (already computed) numbers and evidence per persona |
| Deterministic | assumption-based simulation | Counterfactual / action-simulator impact estimates |

---

## 3. Implementation

### Project layout

```
app/
  config/            settings, KPI semantic contract
  data/              synthetic data generator + loader (see note below)
  analytics/         KPI engine, driver analysis, counterfactuals, action simulator, context builder
  rag/               ingestion/chunking, embeddings, vector store, retriever
  llm/               OpenAI client, prompts, narrative generation
  entitlement/       persona -> location filtering (simulated, no auth)
  personas/          persona decision-rights (which levers each persona can act on)
  feedback/          in-memory feedback capture
  telemetry/         latency/token/cost logging
  components/        shared Streamlit UI helpers
  views/             one module per page, called from main.py
  main.py            app entry point, sidebar nav, persona/location controls
data/synthetic/      committed CSV dataset — see below
tests/               a handful of unit tests for the analytical core
```

### About the data folder

`data/synthetic/` contains the committed synthetic dataset as six CSV files:

| File | Rows | Grain |
|---|---|---|
| `transactions.csv` | ~245K | Transaction / day / store |
| `staffing.csv` | ~20K | Store / hour / day |
| `inventory.csv` | ~7.2K | Store / product / day |
| `promotions.csv` | 2 | Campaign |
| `feedback.csv` | ~700 | Individual feedback item |
| `documents.csv` | 7 | Individual document (emails/reports) |

`app/data/loader.py` loads these CSVs directly if they're present, so every run of
the app sees exactly the data that's checked into the repo. If the CSVs are ever
removed or the folder is empty, the app falls back automatically to
`app/data/synthetic_generator.py`, which builds an equivalent dataset in memory
using a fixed random seed — so the app still works out of the box even without the
committed files. Either way, `get_datasets()` wraps the result with
`st.cache_resource` so this only runs once per session.

The generator module (`app/data/synthetic_generator.py`) is also the source of
truth for the data model — every column, grain and seeded scenario is defined in
one readable place, and is what produced the committed CSVs in the first place.

To regenerate the CSVs yourself (e.g. after changing the generator), run:

```bash
python -c "
from app.data.synthetic_generator import generate_all
data = generate_all()
for name, df in data.items():
    df.to_csv(f'data/synthetic/{name}.csv', index=False)
"
```

Seeded scenarios in the generator:
- a staffing shortage at Mumbai/Bandra with a supporting internal email (drives the
  wait-time driver and its evidence)
- a Cold Brew stockout in Delhi (drives the inventory driver)
- the summer promotion ending just before the current period (drives the promotion
  driver)
- Chai Frappe, a product launched ~21 days ago, to demonstrate sparse-history
  handling
- conflicting reports at Ahmedabad/Satellite (sales says volume declined, the store
  manager's email and customer feedback say traffic looked normal) to demonstrate
  the abstention/contradictory-evidence path

### Persona & entitlement simulation

There is no login system. Selecting a persona in the top-right dropdown pins that
persona to a simulated entitlement (`app/config/settings.py`):

- CEO, CFO, Operations Manager, Marketing Manager and Business Analyst see all of
  India.
- Regional Manager is pinned to Mumbai.
- Store Manager is pinned to Mumbai / Bandra only.

The location dropdown only ever offers locations within that entitlement, and
`app/entitlement/entitlement.py` filters every dataframe by entitlement **before**
any KPI or driver calculation runs — the restriction is enforced in the analytics
layer, not just hidden in the UI.

### RAG pipeline

`Documents/feedback -> chunk -> embed -> vector store -> retrieve -> filter by
entitlement -> hand to LLM`. Only the top-k retrieved chunks for a specific query
are ever included in an LLM prompt — the full document set is never sent.

### LLM integration (OpenAI API)

All narrative generation and embeddings search goes through `app/llm/openai_client.py`, which communicates with the OpenAI API. If the API is unreachable, the app falls back to a clearly-labelled template narrative so the rest of the prototype keeps working.

The credentials and model configuration are securely loaded from a local `.env` file (which is ignored by Git). A `.env.example` file is provided to help users configure their credentials.

---

## 4. Key features

- Executive Overview: material movement alert, KPI cards, trend chart with
  baseline, driver contribution chart, evidence-grounded "why did it happen"
  narrative, quick counterfactual, product/store tables, persona-filtered
  recommendation, feedback capture.
- KPI Explorer: per-KPI trend, movement, materiality, drivers and contract.
- Driver Analysis: ranked drivers with method, confidence, evidence and
  alternative hypotheses.
- Counterfactuals: interactive what-if simulator across wait time, staffing,
  pricing, promotions and inventory.
- Action Simulator: interactive driver -> lever -> action -> expected impact -> owner ->
  confidence -> monitoring plan, filtered by persona decision rights. Fully interactive controls exist for Wait Time / Staffing, Promotion Ended, Pricing / Product Mix, and Inventory Stockout drivers.
- Evidence Explorer: free-text semantic search over all ingested documents and
  feedback, with contradiction detection.
- Data Sources: source metadata (grain, cadence, freshness, quality, lineage).
- KPI Contract: the semantic contract for each KPI.
- Feedback: capture + session history + explanation of how it would be used (with custom high-contrast dark-mode theme friendly text color).
- Telemetry: per-analysis latency, retrieval count, LLM calls, tokens and
  estimated cost.
  estimated cost.

See `FEATURES.md` for a flat one-line-per-feature list.

---

## 5. Installing and running

### 5.1 Python environment

To set up a local virtual environment:

```bash
# Create visual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows (cmd):
venv\Scripts\activate.bat
# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 5.2 API Credentials

Before launching the app, set up your credentials:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your `OPENAI_API_KEY`:
   ```env
   OPENAI_API_KEY=your-actual-api-key-here
   ```
3. Optionally, configure a custom base URL and override default models if using a proxy or custom LLM gateway.

### 5.3 Running the app

Start the Streamlit web server:

```bash
streamlit run app/main.py
```

Open the URL (typically [http://localhost:8501](http://localhost:8501)) in your web browser.

### 5.4 Running the tests

To execute the unit tests test suite for the analytics engine:

```bash
pytest tests/
```

---

## 6. Suggested demo flow

1. Leave persona at CEO / Executive, location at All India — note the material
   movement alert and the ranked drivers on Executive Overview.
2. Switch persona to Store Manager — the location dropdown narrows to Mumbai /
   Bandra only, and the narrative and recommendation change to store-level actions.
3. Open Driver Analysis and expand "Wait Time / Staffing" to see the linked
   evidence (the Bandra staffing email and operations report).
4. Switch location to Ahmedabad (as a persona with access, e.g. Business Analyst)
   to see the contradictory-evidence / abstention behaviour.
5. Visit KPI Explorer, select a KPI, and check the KPI Contract tab.
6. Go to Counterfactuals and try the Wait Time lever.
7. Go to Action Simulator, pick a driver, and note how the recommendation is
   blocked or allowed depending on the selected persona's decision rights.
8. Submit feedback on Executive Overview, then check the Feedback page's history.
9. Check the Telemetry page to see latency, token and cost tracking for every
   analysis run so far, and whether Ollama was actually used.

---

## 7. Known limitations (prototype scope)

- No authentication — entitlement is simulated via the persona dropdown, as
  specified for this round.
- The vector store is in-memory and rebuilt each session; it isn't a production
  vector database.
- Counterfactual and action-simulator impact estimates use documented business
  assumptions (elasticities), not fitted causal models — this is explicitly
  surfaced in the UI, not hidden.
- Estimated LLM cost on the Telemetry page is a nominal figure for demonstrating
  cost tracking; actual local Ollama inference has no per-token API cost.
