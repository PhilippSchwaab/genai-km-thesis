# GenAI-KM Thesis

**System Designs for GenAI-Based Knowledge Capture in SME Business Processes**

Master's thesis comparing two LLM-driven architectures — a structured pipeline (Architecture A) and an agentic workflow (Architecture B) — for automatically converting unstructured business artifacts into structured wiki entries.

**Author:** Philipp Julian Schwaab | **Advisor:** Dorian Achim Prill | **Company:** Meshmakers GmbH

## Setup

```bash
uv sync
cp .env.example .env
```

### Local (Ollama)

No API key needed. Install [Ollama](https://ollama.com), pull a model, and set the base URL:

```bash
ollama pull gemma4:26b
# .env
OLLAMA_API_BASE=http://localhost:11434
```

### Cloud (Mistral, OpenAI, etc.)

Add your API key to `.env` (e.g. `MISTRAL_API_KEY=...`). See [LiteLLM providers](https://docs.litellm.ai/docs/providers) for supported models.

## Project Structure

```
src/pipeline/     Architecture A — Structured Pipeline
src/agentic/      Architecture B — Agentic Workflow (Strands Agents SDK)
src/common/       Shared utilities (LLM client, PII redaction, prompt loader)
prompts/          Versioned prompt YAMLs (generation + evaluation)
data/             raw → anonymized → KIPs (gold standard)
eval/harness/     KIP scorer (LLM-as-judge) and MCDA math (aspiration SAW)
eval/results/     Per-run raw outputs (wiki_entry.md, metadata.json, kip_eval.json)
eval/metrics/     Cross-run derived aggregates (run1_mcda_summary.md + run1_mcda.json)
eval/run_mcda.py  MCDA orchestrator: per-architecture aggregation + gates + canonical Run-N report
eval/review_stats.py  Library: review-UI loaders, ReviewData, Cohen's d
eval/mcda_config.yaml 5 criteria + 4 sensitivity profiles per thesis §3.3.2
docs/             Architecture docs, DSR changelog, future plans
```

## CLI

```bash
km --help

# Generate wiki entries
km generate --arch pipeline CS-06_Testing_Strategy_compiled.md
km generate --arch agentic  CS-06_Testing_Strategy_compiled.md

# Override prompt template or sampling
km generate --arch pipeline --prompt my_prompt_id --temperature 0.8 --top-p 0.9 CS-06*.md

# Score runs against KIP ground truth (writes kip_eval.json per run dir)
km evaluate pipeline_CS-06_..._20260417T060240Z agentic_CS-06_..._20260417T061058Z \
  --judge-model ollama_chat/gemma4:26b

# MCDA composite ranking across architectures (writes eval/metrics/run1_mcda_summary.md + run1_mcda.json)
km mcda
km mcda --label "Run 2"          # re-run after Run 2 results land

# Override the frontend repo path (default: $KM_FRONTEND_PATH or ~/PycharmProjects/genai-km-frontend)
km mcda --frontend /path/to/genai-km-frontend

# Other
km anonymize             # redact PII: data/raw/ → data/anonymized/
km validate              # validate all KIPs against schema
km prompts               # list prompt templates with model + version
```

> If `km` is not on your PATH, use `uv run km` instead.

## Tests

```bash
uv run pytest -v          # 97 tests, no API key required
```

## Stack

Python 3.13 · LiteLLM (Ollama / Mistral / OpenAI) · Strands Agents SDK · Microsoft Presidio · uv
