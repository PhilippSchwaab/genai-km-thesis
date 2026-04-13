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

## CLI

All commands are available via the `km` entry point:

```bash
km --help                # show all commands
km anonymize             # redact PII: data/raw/ → data/anonymized/
km generate --arch pipeline sample_meeting.txt   # generate wiki entry
km evaluate --run-dir runs/2026-04-13/           # run eval suite
km validate              # validate all KIPs against schema
km validate data/kips/sample_meeting.json        # validate a single file
km prompts               # list available prompt templates
```

> If `km` is not on your PATH, use `uv run km` instead.

## Tests

```bash
uv run pytest -v          # no API key required
```

## Stack

Python 3.13 · Mistral AI (via LiteLLM) · Microsoft Presidio · uv
