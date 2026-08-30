# Feature list (personal reference)

Flat list of everything built in this prototype, one line each — what it is and
what it's for.

## Executive Overview
- Material movement alert — flags the biggest KPI swing with materiality + top driver in one line.
- KPI cards (Revenue, Transactions, Avg Ticket, Wait Time) — at-a-glance current value + % vs baseline.
- Revenue trend chart with baseline line — shows the shape of the movement over time, not just a number.
- Driver contribution bar chart — visual breakdown of what's driving the movement.
- "Why did it happen" LLM narrative — plain-language explanation grounded in the computed numbers + evidence.
- Evidence panel — shows the actual emails/feedback snippets the narrative is based on.
- Quick counterfactual snapshot — "what if wait time were back at baseline" shown inline.
- Product table with new-product callout — revenue/units/ticket per product, flags Chai Frappe as sparse-history.
- Store table — revenue/transactions/ticket/wait time per store.
- Recommended action block — driver -> lever -> action -> impact -> owner -> confidence -> monitoring, persona-filtered.
- Inline feedback buttons (Correct/Partial/Incorrect + comment) — one-click feedback capture on the insight.

## KPI Explorer
- KPI selector — pick any of the four core KPIs.
- Trend + movement + materiality breakdown — same numbers as Executive Overview, per-KPI detail view.
- Driver chart reused per KPI — consistent driver view regardless of entry point.
- KPI contract viewer — definition/formula/baseline/threshold for the selected KPI.
- Data freshness panel — last refresh + quality + coverage for the KPI's source.

## Driver Analysis
- Ranked driver list with contribution % and confidence — the full multi-driver breakdown.
- Per-driver evidence lookup (expandable) — pulls RAG evidence specific to that driver, on demand.
- Contradiction warning per driver — flags when a driver's evidence conflicts.
- Alternative hypotheses section — surfaces the 2nd/3rd ranked drivers explicitly.
- Unexplained component display — honest residual instead of forcing 100% attribution.

## Counterfactuals
- Lever selector (Wait Time / Staffing / Pricing / Promotion / Inventory) — pick the variable to simulate.
- Interactive sliders/toggles per lever — adjust the proposed value live.
- Actual vs counterfactual vs difference metrics — clear side-by-side comparison.
- Assumption disclosure — states the exact business assumption behind each estimate.

## Action Simulator
- Driver -> lever mapping — auto-suggests the right lever for the selected driver.
- Staffing slider tied to the counterfactual engine — same math as Counterfactuals, action-framed.
- Owner/confidence/monitoring plan display — full recommendation shape in one view.
- Persona decision-rights check — warns when the current persona can't actually act on this lever.

## Evidence Explorer
- Free-text semantic search box — query the whole evidence corpus directly.
- Adjustable result count — control how many chunks come back.
- Contradiction detector on search results — flags conflicting language across results.
- Full source metadata per result — type, location, date, relevance score, sensitivity.

## Data Sources
- Source metadata table — grain, cadence, freshness, quality, owner, lineage per source.
- Grain/cadence explanation — plain-language note on why reconciliation is needed.
- Live row counts — actual row counts of the in-memory synthetic datasets this session.

## KPI Contract
- Full semantic contract per KPI — definition, formula, unit, source, grain, cadence, baseline method, threshold, drivers, owner, lineage, access restriction.

## Feedback
- Structured verdict submission (8 verdict types) — Correct/Incorrect/Helpful/etc.
- Optional driver correction + free-text comment fields.
- Session feedback history table.
- Explanation of downstream use — how feedback would feed evaluation/ranking/prompt improvement in production.

## Telemetry
- Ollama reachability check — live status indicator for the local LLM server.
- Per-analysis event log — timestamp, persona, location, KPI, method, retrieval count, LLM calls, tokens, latency, cost, status.
- Aggregate metrics — total LLM calls, total tokens, estimated cost, average latency.

## Cross-cutting / platform features
- Persona dropdown (7 personas) — changes narrative focus, recommendations and decision rights app-wide.
- Location/branch dropdown, entitlement-aware — options narrow automatically based on persona.
- Entitlement filtering enforced in the data layer — not just hidden UI, actual dataframe filtering pre-analysis.
- Deterministic KPI engine — baseline calc, movement %, statistical + business materiality scoring.
- Multi-factor driver engine — decomposition + correlation + business rules combined and ranked.
- Contradictory-evidence detection + abstention — engine refuses to name a primary driver when evidence conflicts.
- Sparse-history handling — new product (21 days history) gets descriptive-only treatment, no causal claims.
- RAG pipeline — chunking, embeddings (Ollama or TF-IDF fallback), in-memory vector search, entitlement-filtered retrieval.
- LLM narrative layer — persona-specific narration of pre-computed numbers, with graceful local-template fallback.
- In-memory synthetic data generator — builds all 6 datasets fresh each session, no files touched on disk.
- Light-themed custom Streamlit UI — sidebar nav grouped into Workspace/Data/System, card-style metrics.
