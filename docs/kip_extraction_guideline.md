# KIP Extraction Guideline

## For use in Section 3.2 (Baseline Definition) and Appendix

---

## 1. Definition

A **Key Information Point (KIP)** is a single, atomic, verifiable unit of information extracted from a source artifact that would be relevant for inclusion in a wiki-style knowledge entry.

Each KIP must satisfy three criteria:

1. **Atomic:** It expresses exactly one fact or claim. If two parts can be independently true or false, they are separate KIPs.
2. **Verifiable:** It can be confirmed or refuted by pointing to a specific location in the source artifact (commit hash, file path, PR description, or work item field).
3. **Documentation-relevant:** A team member unfamiliar with the workstream would need this information to understand what was done and why.

This definition is informed by the atomic fact decomposition approach used in FActScore (Min et al., 2023), adapted for the domain of software engineering artifacts rather than biographical text.

---

## 2. KIP Categories

Each KIP is assigned exactly one category. Categories are tailored to the artifact types in the Control Set (development compilations and support/professional services reports).

### Unified category taxonomy (both artifact types)

| Code | Category | Definition | Example |
|------|----------|------------|---------|
| DEC | **Design Decision** | A deliberate architectural or strategic choice that shaped the workstream direction | "Adopted Kustomize for Kubernetes deployment configuration management" |
| IMP | **Implementation Action** | A concrete technical action taken — code added, files created, configuration changed | "Added a DisplayConfigCommand CLI command for inspecting runtime configuration" |
| FIX | **Bug Fix / Correction** | A problem identified and resolved during the workstream | "Changed SyncOrderFeedback to log errors instead of crashing the process" |
| RAT | **Rationale** | An explanation of *why* something was done, especially when not self-evident from the action alone | "Removed E2E tests because they were replaced by integration tests" |
| CFG | **Configuration / Infrastructure** | Changes to deployment, CI/CD, environment setup, or operational parameters | "Added backoffLimit and activeDeadlineSeconds to Kubernetes CronJob definitions" |
| DEP | **Dependency Change** | Addition, removal, or version change of external libraries or services | "Bumped Billbee API Client to version 2.4.3" |
| TEC | **Technical Detail** | Specific technical facts relevant to understanding the work or resolution | "The automatic screenshot function requires a USB drive with drive letter G:" |

> **Note:** One unified taxonomy applies to both artifact types; it was validated against all six Control Set artifacts (CS-01 through CS-06). Earlier drafts defined additional Type-1-specific codes (ISS, RES, BLK) that did not occur in the final extraction and were removed.


---

## 3. Granularity Rules

### The Splitting Test

Ask: "Could an architecture's output correctly state one part of this claim while missing or getting the other part wrong?" If yes, split into separate KIPs.

**Example — Split:**
- ~~"Removed E2E tests and added 19 integration tests using Testcontainers and Moq"~~
- KIP 1 (DEC): "E2E tests were removed from the project"
- KIP 2 (DEC): "Integration tests were introduced as the replacement testing strategy"
- KIP 3 (IMP): "19 integration tests were added"
- KIP 4 (IMP): "Integration tests use Testcontainers (SFTPGo) for SFTP simulation"
- KIP 5 (IMP): "Integration tests use Moq for dependency mocking"

**Example — Keep as one:**
- "The credentials-secret.yaml file was renamed to credentials-secret.yaml.example and the original was added to .gitignore"

  This is a single coordinated action where one part without the other would be misleading. It stays as one KIP.

### The Relevance Test

Not every commit or change warrants a KIP. Exclude:

- **Pure noise commits** that only echo a previous fix without new information (e.g., multiple "Bugfix Integration Testing" commits that represent iterative debugging, not distinct knowledge)
- **Trivial housekeeping** that carries no architectural or operational significance (e.g., a test build commit with no meaningful change)
- **Duplicate information** already captured by another KIP at a higher level of abstraction

Include intermediate steps only when they reveal something the final state does not — for instance, a reverted approach that shows what was tried and abandoned.

### Counting Guidance

Based on the artifact density assessment:

| Artifact | Estimated KIP Range | Rationale |
|----------|-------------------|-----------|
| CS-04 | 15–20 | High density; multi-phase narrative spanning setup, Kustomize adoption, staging, credential hardening |
| CS-05 | 8–10 | Low density; linear fix→enhance arc, empty work item descriptions |
| CS-06 | 10–12 | Medium density; clear strategic pivot, but information is concentrated in a few key commits |

If your extraction falls significantly outside these ranges, revisit granularity (too many = over-splitting; too few = missing implicit knowledge).

---

## 4. Sourcing Rules

Every KIP must include a **source reference** pointing to the specific evidence in the artifact.

| Source Type | Reference Format |
|-------------|-----------------|
| Commit message | `commit:<hash>` (short hash) |
| File change | `commit:<hash>, file:<path>` |
| PR description | `PR#<number>` |
| Work item field | `WI:AB#<id>, field:<field_name>` |
| Inferred from multiple sources | `inferred:<hash1>,<hash2>` with a note explaining the inference |

### Handling Implicit Knowledge

Some KIPs will not be stated explicitly in any single commit message but can be reliably inferred from the pattern of changes. These are marked with `inferred` sourcing and a brief justification.

**Example:** "The project shifted from a custom StorageClass to the cluster's built-in StorageClass" — this is not stated in any single commit but is the clear narrative arc of commits `b8bb38a` → `ae4873b` in CS-04.

Implicit KIPs are critical to include because they represent exactly the kind of synthesized knowledge that a wiki entry should capture and that distinguishes an intelligent system from a simple commit log formatter.

---

## 5. Output Format — KIP Registry

Each artifact gets a KIP registry table. The registry serves as the gold-standard baseline for evaluation scoring.

```
| KIP-ID    | Category | Statement                                          | Source           | Implicit? |
|-----------|----------|-----------------------------------------------------|------------------|-----------|
| CS-06-001 | DEC      | E2E tests were removed from the project             | commit:27bbf4f   | No        |
| CS-06-002 | DEC      | Integration tests were introduced as replacement    | commit:5088faa   | No        |
| CS-06-003 | IMP      | An integration test project was created              | commit:5088faa   | No        |
| CS-06-004 | IMP      | Test fixtures for SFTP and external API mocking were added | commit:5088faa | No  |
| CS-06-005 | RAT      | Manual E2E steps were documented in README as fallback | commit:27bbf4f | No        |
| CS-06-006 | IMP      | Integration test warnings were cleaned up in a follow-up pass | inferred:ce26c70,79a4931 | Yes |
```

> **Note:** CS-06 has no matched PRs due to the cross-tagging inconsistency documented in the Control Set decisions (PR#354 is tagged to AB#3151/CS-04 instead of AB#3651/CS-06). The example above therefore sources KIPs only from commit messages and file changes within CS-06, consistent with the cross-artifact boundary rule in Section 7. The richer details available in PR#354 (e.g., "19 tests", "Testcontainers + Moq") are valid KIPs only for CS-04.

---

## 6. Extraction Procedure

### Step 1: Read the full artifact end-to-end
Do not extract KIPs on a first pass. Build a mental model of the workstream narrative first.

### Step 2: Identify the narrative arc
What is the overall story? For each artifact, write a one-sentence summary:
- CS-04: "Onboarding onto an existing project, stabilizing the codebase, adopting Kustomize for deployment, and setting up staging infrastructure."
- CS-05: "Making the order sync process resilient to bad data and adding email notifications for errors."
- CS-06: "Replacing brittle E2E tests with robust integration tests."

### Step 3: Extract KIPs systematically
Work through the artifact chronologically. For each commit or PR, ask:
1. Does this introduce new information not captured by existing KIPs?
2. What category does it belong to?
3. Is it atomic, or should it be split?
4. Is it documentation-relevant (would a newcomer need to know this)?

### Step 4: Check for implicit knowledge
After the chronological pass, review the full KIP list and ask: "What story do these commits tell that no single commit says?" Add inferred KIPs.

### Step 5: Validate against estimates
Compare your count to the density estimates in Section 3. Significant deviation signals either over-splitting or under-extraction.

---

## 7. Cross-Artifact Boundary Rule

Each artifact is treated as an **independent unit** for KIP extraction and evaluation. Information that exists in Artifact X but not in Artifact Y is not a valid KIP for Artifact Y, even if the information is logically related.

This rule exists because:
- The prototypes process each artifact independently (no cross-artifact context)
- Scoring must reflect what can be extracted from the artifact alone
- The cross-tagging inconsistency (PR#354 tagged to CS-04 instead of CS-06) is a real-world data quality issue, not an extraction error

The boundary rule and its implications are discussed further in Section 5 (Evaluation) and Section 6.3 (Future Work: cross-artifact knowledge linking).

---

## 8. Thesis Integration

### Section 3.2 — Baseline Definition
Include: KIP definition (Section 1), category taxonomy summary (Section 2), and the extraction procedure overview (Section 6). Reference the full guideline and worked examples in the appendix.

**Suggested paragraph:**
> "Key Information Points were extracted manually by the author following a structured guideline (see Appendix X). Each KIP represents an atomic, verifiable, documentation-relevant fact identified in the source artifact. KIPs were categorized into six types — design decision, implementation action, bug fix, rationale, configuration change, and dependency change — and each was traced to its source evidence. The resulting KIP registry serves as the gold-standard baseline against which both architectures' outputs are evaluated for recall and completeness."

### Appendix
Include: The full guideline (this document), the complete KIP registry tables for all Control Set artifacts, and 2–3 worked examples showing the splitting test and implicit knowledge extraction applied to real data.
