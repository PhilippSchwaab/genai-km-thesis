# DSR Change Log

This document tracks all modifications made between evaluation runs
as the Design Science Research audit trail (thesis §3.1, §4.2.3, §5.3).

## Run 1 → Run 2 Changes

Six changes scoped for DSR Cycle 2. Plan: `docs/run2_plan.md`.
Each row is filled in as the change is implemented and its prompt YAML(s) bumped to `version: 2`.

| ID    | Architecture | Component                                | Before                                                                 | After                                                                  | Rationale (Run 1 evidence + 30 Apr consultation)                                                                                                              | Status  |
|-------|--------------|------------------------------------------|------------------------------------------------------------------------|------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| CL-01 | Both         | Prompt template + CLI                    | Single fixed schema                                                    | `--audience {marketing,development,architect}` with per-audience scaffolding | Realizes Adaptability principle (thesis §2.3, Yun et al.); Tech Lead A flagged stakeholder-specific outputs as unmet need (§3.2.2)                              | Pending |
| CL-02 | Both         | Prompt template (exemplars)              | No few-shots                                                           | Two audience-appropriate exemplars per audience spliced as user/assistant turns | Tech Lead A documentation paradox (§3.2.2): Run 1 outputs include audience-inappropriate detail (commit hashes, file paths, line counts) that fits a developer reader but not a marketing or architect reader; exemplars demonstrate the desired audience-fit. Pre-Run-1 high-temperature trial on CS-06 also showed structural variance (`docs/eval_cs06_first_runs.md` Obs. 1) which exemplars further reduce | Pending |
| CL-03 | Both         | Prompt template (block order)            | Instruction first, then artifact                                       | Source artifact first, instruction last                                | Aligns with Anthropic long-context guidance; positions cache breakpoint between static and dynamic content for CL-05                                            | Done    |
| CL-04 | Agentic      | Tool prompts + REVIEW step               | Verbose intermediate output                                            | "Bullet list only, ≤150 words, `NONE` if empty" (≈10× below Run 1 intermediate-reasoning volume) | Run 1 agentic produced ~2,106 tokens of internal reasoning per run (`docs/eval_cs06_first_runs.md` Obs. 2); cut intermediate verbosity without touching DRAFT  | Done    |
| CL-06 | Agentic      | Runner + new Reviewer prompt + tool_choice | Single Strands `Agent` with two degenerate self-referential tools (`check_completeness`, `check_hallucinations`) that re-inject the source as a prompt; tool use was optional | Writer-orchestrator `Agent` + Reviewer sub-agent (new `prompts/agentic_reviewer.yaml`) wrapped as a single `review_draft(draft)` tool via Strands' "Agents as Tools" pattern; orchestrator forced via `tool_choice` to invoke Reviewer at least once | §2.2.3 promised "specialised agents that act together" but Run 1 implementation was a single agent with self-referential tools; closes that gap with no methodology shift. Also realises Tech Lead A's three-stage architecture (writer / fact-checker / human, §3.2.2 finding 2). Forced tool use defends against the Gemma-style CoT collapse documented in `docs/eval_cs06_first_runs.md` Obs. 2 | Pending |
| CL-05 | Agentic      | Runner / LiteLLM client                  | No prompt cache; `_estimate_cost` passes raw `prompt_tokens` at standard input rate | Prompt-cache breakpoints on system prompt + source artifact (Writer and Reviewer prefixes) via LiteLLM's `cache_control` marker; `_estimate_cost` updated to consume `cached_tokens` and `cache_creation_input_tokens` from the Strands usage block (or fall back to `litellm.completion_cost()` on the raw response) and compute Cost using the per-token cache-read / cache-write / standard-input rates separately | Run 1 agentic uses ~8.2× the prompt tokens of pipeline because each tool turn re-sends the source; caching amortizes the prefix across turns. After CL-06 the Reviewer also re-reads the source, so the same breakpoints apply to its request. **Cost-reporting dependency:** without the `_estimate_cost` update, the Cost criterion would overstate Architecture B's cost by ignoring the ~10× cheaper cache-read rate; persist `cached_tokens` and `cache_creation_input_tokens` in `metadata.json` for Ch 5.3 hit-rate analysis | Pending |

### Excluded refinements (recorded for audit trail)

- **Inline source attribution** (commit hashes / quote anchors). Discussed under thesis §3.3.3 as a candidate Run 2 refinement contingent on reviewer feedback. Reviewed and **not adopted** for Run 2; rationale to be captured in §4.2.3 prose so the §3.3.3 conditional clause is explicitly resolved.

### Status tracking

- **Pending** — not started.
- **In progress** — branch open, not yet merged.
- **Done** — merged, prompt version bumped, before/after run captured.

When all six rows reach **Done**, execute the Run 2 batch (12 comparable runs + 6 audience-showcase runs as defined in `docs/run2_plan.md`).