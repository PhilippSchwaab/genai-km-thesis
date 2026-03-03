# GenAI-KM Thesis

**System Designs for GenAI-Based Knowledge Capture in SME Business Processes**

Master's thesis comparing two LLM-driven architectures — a structured pipeline (Architecture A) and an agentic workflow (Architecture B) — for automatically converting unstructured business artifacts (meeting transcripts, chat logs, commit histories) into structured wiki entries.

**Author:** Philipp Julian Schwaab | **Advisor:** Dorian Achim Prill | **Company:** Meshmakers GmbH

## Setup

```bash
uv sync
cp .env.example .env   # add your Mistral API key
```

## Project Structure

```
src/common/       Shared utilities (LLM client, PII redaction, config)
src/pipeline/     Architecture A — Structured Pipeline
src/agentic/      Architecture B — Agentic Workflow
prompts/          Versioned prompt library
data/             raw → anonymized → KIPs (gold standard)
eval/             Evaluation harness, metrics, results
docs/             Architecture docs, requirements, DSR changelog
```

## PII Anonymization

Place raw business artifacts in `data/raw/`, then run:

```bash
uv run python -m src.common.anonymize_files
```

Anonymized files are written to `data/anonymized/`. Already-processed files are skipped.

## KIP Validation

Validate all KIP files in `data/kips/` against the schema:

```bash
uv run python -m src.common.validate_kips
```

Or validate a single file:

```bash
uv run python -m src.common.validate_kips data/kips/sample_meeting.json
```

## Prompt Library

Versioned YAML prompts in `prompts/`. Load artifacts and render in one go:

```python
from src.common.prompts import load_prompt, load_artifacts

bundle = load_artifacts("sample_meeting.txt", "chat_sprint42.txt")  # from data/anonymized/
prompt = load_prompt("pipeline_generate_wiki")
messages = prompt.render(artifact_type=bundle.artifact_type, artifact_id=bundle.artifact_id, artifact_text=bundle.artifact_text)
response = litellm.completion(model=prompt.model, messages=messages)
```

Prompts: `pipeline_generate_wiki`, `agentic_generate_wiki`, `eval_kip_scorer`, `eval_hallucination_checker`.

## Tests

```bash
uv run pytest -v          # no API key required
```

## Stack

Python 3.13 · Mistral AI (via LiteLLM) · Microsoft Presidio · uv
