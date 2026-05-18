# DSR Change Log

This document tracks all modifications made between evaluation runs
as the Design Science Research audit trail (thesis §3.1, §4.2.3, §5.3).

## Run 1 → Run 2 Changes

Six changes scoped for DSR Cycle 2. Plan: `docs/run2_plan.md`.
Each row is filled in as the change is implemented and its prompt YAML(s) bumped to `version: 2`.

| ID    | Architecture | Component                                | Before                                                                 | After                                                                  | Rationale (Run 1 evidence + 30 Apr consultation)                                                                                                              | Status  |
|-------|--------------|------------------------------------------|------------------------------------------------------------------------|------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| CL-01 | Both         | Prompt template + CLI                    | Single fixed schema                                                    | `--audience {marketing,development,architect}` with per-audience scaffolding declared under `meta.audiences` in the prompt YAML; runner forwards the parameter and persists it in `metadata.json` | Realizes Adaptability principle (thesis §2.3, Yun et al.); Tech Lead A flagged stakeholder-specific outputs as unmet need (§3.2.2)                              | Done    |
| CL-02 | Both         | Prompt template (exemplars)              | No few-shots                                                           | Two audience-appropriate exemplars per audience under `meta.audiences.<name>.exemplars`, spliced as user/assistant turns through the same user-template wrapper as the live request (format-consistent few-shot per Min et al. EMNLP 2022). Pipeline path: native LiteLLM multi-message. Agentic path: exemplar history forwarded via Strands `Agent(messages=...)`. | Tech Lead A documentation paradox (§3.2.2): Run 1 outputs include audience-inappropriate detail (commit hashes, file paths, line counts) that fits a developer reader but not a marketing or architect reader; exemplars demonstrate the desired audience-fit. Pre-Run-1 high-temperature trial on CS-06 also showed structural variance (`docs/eval_cs06_first_runs.md` Obs. 1) which exemplars further reduce | Done    |
| CL-03 | Both         | Prompt template (block order)            | Instruction first, then artifact                                       | Source artifact first, instruction last                                | Aligns with Anthropic long-context guidance; positions cache breakpoint between static and dynamic content for CL-05                                            | Done    |
| CL-04 | Agentic      | Tool prompts + REVIEW step               | Verbose intermediate output                                            | "Bullet list only, ≤150 words, `NONE` if empty" (≈10× below Run 1 intermediate-reasoning volume) | Run 1 agentic produced ~2,106 tokens of internal reasoning per run (`docs/eval_cs06_first_runs.md` Obs. 2); cut intermediate verbosity without touching DRAFT  | Done    |
| CL-06 | Agentic      | Runner + new Reviewer prompt              | Single Strands `Agent` with two degenerate self-referential tools (`check_completeness`, `check_hallucinations`) that re-inject the source as a prompt; tool use was optional | Two cooperating Strands `Agent` instances (Writer + Reviewer, new `prompts/agentic_reviewer.yaml`) cycled by the runner: the Writer drafts the entry, the Reviewer re-reads the source against the draft and returns either the literal `NONE` (acceptable) or a bullet list of issues; on issues the Writer revises and the cycle repeats, capped at `_MAX_REVIEWER_ITERATIONS = 3`. Run 1's two self-referential tools are removed. `metadata.json` gains `reviewer_iterations`, `reviewer_passed`, `max_iterations`, `reviewer_prompt_id`, `reviewer_prompt_version` for §5.3 audit. | §2.2.3 promised "specialised agents that act together" but Run 1's implementation was a single agent with self-referential tools; closes that gap by making the Reviewer a real second agent with its own prompt, sampling, and conversation. Also realises Tech Lead A's three-stage architecture (writer / fact-checker / human, §3.2.2 finding 2). The runner's hard cap on iterations defends against the Gemma-style CoT collapse documented in `docs/eval_cs06_first_runs.md` Obs. 2 by giving up rather than looping unbounded. CL-05 cache breakpoints apply to both agents — the source artifact is the stable prefix shared across all Writer revisions and all Reviewer turns. | Done    |
| CL-05 | Agentic      | Runner / LiteLLM client                  | No prompt cache; `_estimate_cost` passes raw `prompt_tokens` at standard input rate | Cache breakpoints on the system prompt and the source-artifact prefix of the live user message via Strands' `cachePoint` content-block (Strands' LiteLLMModel translates to Anthropic's `cache_control: ephemeral` on the preceding text block). `_estimate_cost` rewritten to forward `cache_creation_input_tokens` and `cache_read_input_tokens` to `litellm.cost_per_token`, applying the per-rate cache-read / cache-write / standard-input pricing separately. Cache token fields persisted in `metadata.json` (`cache_read_input_tokens`, `cache_creation_input_tokens`) for §5.3 hit-rate analysis. | Run 1 agentic uses ~8.2× the prompt tokens of pipeline because each tool turn re-sends the source; caching amortizes the prefix across turns. After CL-06 the Reviewer also re-reads the source, so the same breakpoints apply to its request. **Cost-reporting dependency:** without the `_estimate_cost` update, the Cost criterion would overstate Architecture B's cost by ignoring the ~10× cheaper cache-read rate. | Done    |

### Excluded refinements (recorded for audit trail)

- **Inline source attribution** (commit hashes / quote anchors). Discussed under thesis §3.3.3 as a candidate Run 2 refinement contingent on reviewer feedback. Reviewed and **not adopted** for Run 2; rationale to be captured in §4.2.3 prose so the §3.3.3 conditional clause is explicitly resolved.

### Status tracking

- **Pending** — not started.
- **In progress** — branch open, not yet merged.
- **Done** — merged, prompt version bumped, before/after run captured.

When all six rows reach **Done**, execute the Run 2 batch (12 comparable runs + 6 audience-showcase runs as defined in `docs/run2_plan.md`).

## Refactors (non-DSR)

Code-shape changes that touch neither prompts nor models nor evaluation
methodology. Explicitly **not** numbered as CL-XX entries because they
do not move any thesis-reported figure — the prompts, sampling, models,
KIP scorer, MCDA, and per-run output bundle are unchanged. Recorded
here only for audit-trail completeness and to flag the surface area
the Phase-0 preparation introduces (see `docs/production_fork_plan.md`).

| Date       | Scope                                                   | Summary |
|------------|---------------------------------------------------------|---------|
| 2026-05-18 | `src/common/contracts.py` + `src/{pipeline,agentic}/runner.py` | Introduce a canonical `SourceArtifact` / `GenerationResult` contract that both architectures route their core through (`generate(source) -> result`). The file-based `run_pipeline` / `run_agentic` orchestrators are thin wrappers that load anonymized artifacts, call `generate`, and persist outputs. Adds `result.json` (canonical contract) to each run directory; `metadata.json` is preserved key-for-key so MCDA, KIP scorer, and review_stats keep working without change. `run_id` is a UUIDv7 per RFC 9562 §5.7 (inline shim — stdlib `uuid.uuid7()` is Python 3.14+; this repo is pinned to 3.13 because of LiteLLM's uvloop incompatibility, BerriAI/litellm#26343). Source identifier follows OpenLineage's namespace+name convention as a single URI (`file:///data/anonymized/<filename>` for single, `bundle:///<comma-joined>` for multi). All 171 tests pass unchanged. Motivation in `docs/production_fork_plan.md` §"Phase 0". |
