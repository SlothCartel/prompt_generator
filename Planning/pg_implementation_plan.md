# PG MVP Implementation Plan v2 (Required Local LLM)

## Executive Overview

### System Architecture Summary
- PG is a local-first Python CLI with three isolated engines: Deterministic Generation Engine (authoritative), LLM Augmentation Engine (required and non-authoritative), and Deterministic Review Gate (authoritative).
- Canonical artifacts, canonical hashing, and gate decisions are deterministic-only.
- LLM behavior is augmentation-only and never authoritative.

### Deterministic Core vs LLM Augmentation
- Canonical outputs are always produced by deterministic logic.
- `--no-llm` is canonical, deterministic, and fully offline.
- LLM-enabled runs may produce only sidecar outputs.
- Deterministic review and exit codes do not depend on LLM text.

### Local-First Operating Model
- Offline operation is mandatory for deterministic mode.
- Local LLM integration is mandatory as a subsystem.
- Default provider is Ollama; provider selection is pluggable and config-driven.

## Spec Delta / Overrides

### Override Statement
- This plan intentionally overrides `mvp.md` wording that treats local LLM integration as optional.
- In this plan, local LLM integration is required, while still non-authoritative.

### Non-Negotiable Invariants
- `--no-llm` is canonical, deterministic, fully offline, and bypasses all provider logic and provider calls.
- LLM output is sidecar-only and excluded from canonical hashing and canonical review authority.
- Canonical manifest/hash/review pipelines do not consume LLM sidecar artifacts.
- Deterministic artifacts remain authoritative in all modes.

### Rationale and Risk Note
- Rationale: mandatory provider abstraction avoids hardcoded backend logic and allows extensibility without refactoring deterministic core.
- Risk: boundary violations could let LLM outputs affect canonical behavior.
- Mitigation: explicit interfaces, artifact segregation, and boundary-focused tests.

## Public APIs, Interfaces, and Types (Planned)

### CLI Command Surface
- `pg init [--force]`
- `pg session new <name>`
- `pg session list`
- `pg session use <id>`
- `pg generate --mode {plan|implement|investigate} [--pack <name>...] [--no-llm] [--provider <provider_id>] [--model <model_id>] [--dry-run]`
- `pg review [--strict] [--no-llm] [--provider <provider_id>] [--model <model_id>]`

### CLI Semantics for Provider/Model
- `--mode` selects deterministic template mode only.
- `--provider` selects local LLM provider only.
- `--model` selects LLM model id only.
- `pg generate --no-llm` runs deterministic generation only and does not resolve or call providers.
- `pg review --no-llm` runs deterministic review only and does not resolve or call providers.
- `pg review` without `--no-llm` always runs deterministic classification first, then may run optional LLM critique sidecar generation.
- In `pg review`, `--provider` and `--model` affect only critique sidecar generation and never affect `review_decision.md` or exit code mapping.

### Precedence Rules
- Precedence: CLI flags > session overrides > `.pg/config.yaml` > defaults.
- Session overrides storage is fixed at `.pg/sessions/<session_id>/input/metadata.yaml` under `overrides`.
- Allowed override keys are limited to LLM runtime controls: `provider_id`, `model_id`, `timeout_seconds`, `max_retries`, optional `temperature`, optional `top_p`.
- Forbidden override domains are normalization rules, hashing rules, pack resolution semantics, review gate thresholds, exit code mapping, and prompt heading contracts.
- Unknown override keys are deterministic validation errors.
- Precedence behavior is verifiable and deterministic in unit and integration suites.

## File-by-File Architecture Plan

### Core Project Files
- `pyproject.toml`
- `src/pg/__init__.py`
- `src/pg/cli.py`
- `src/pg/constants.py`
- `src/pg/config/schema.py`
- `src/pg/config/loader.py`
- `src/pg/session/model.py`
- `src/pg/session/store.py`
- `src/pg/context/packs.py`
- `src/pg/context/normalize.py`
- `src/pg/context/manifest.py`
- `src/pg/generate/templates.py`
- `src/pg/generate/renderer.py`
- `src/pg/generate/validate.py`
- `src/pg/review/contract.py`
- `src/pg/review/rules.py`
- `src/pg/review/decision.py`
- `src/pg/llm/providers/base.py`
- `src/pg/llm/providers/ollama.py`
- `src/pg/llm/providers/registry.py`
- `src/pg/llm/service.py`
- `src/pg/io/safe_fs.py`
- `src/pg/logging_setup.py`
- `tests/unit/...`
- `tests/integration/...`
- `tests/fixtures/...`

### Runtime `.pg` Layout Created by `pg init`
- `.pg/config.yaml`
- `.pg/AGENTS.md`
- `.pg/templates/plan.md.j2`
- `.pg/templates/implement.md.j2`
- `.pg/templates/investigate.md.j2`
- `.pg/templates/review.md.j2`
- `.pg/context/global/rules.md`
- `.pg/context/global/output_format.md`
- `.pg/context/global/risk_policy.md`
- `.pg/context/project/README.md`
- `.pg/context/project/packs.yaml`
- `.pg/context/project/session_context_guide.md`
- `.pg/context/project/user_context_slots.md`
- `.pg/sessions/`

### Session Scaffold Created by `pg session new`
- `.pg/sessions/<session_id>/input/request.md`
- `.pg/sessions/<session_id>/input/metadata.yaml`
- `.pg/sessions/<session_id>/input/agent_response.md`
- `.pg/sessions/<session_id>/input/context/user_notes.md`
- `.pg/sessions/<session_id>/input/context/domain_context.md`
- `.pg/sessions/<session_id>/input/context/constraints.md`
- `.pg/sessions/<session_id>/output/prompt_for_agent.md`
- `.pg/sessions/<session_id>/output/context_bundle.md`
- `.pg/sessions/<session_id>/output/context_manifest.json`
- `.pg/sessions/<session_id>/output/review_decision.md`
- `.pg/sessions/<session_id>/output/review_issues.md`
- `.pg/sessions/<session_id>/output/next_prompt.md`
- `.pg/sessions/<session_id>/output/llm/augmentation.md`
- `.pg/sessions/<session_id>/output/llm/review_critique.md`
- `.pg/sessions/<session_id>/output/llm/metadata.json`
- `.pg/sessions/<session_id>/logs/pg.log`
- Sidecar lifecycle policy: the three `output/llm/*` files are always created during session scaffold as deterministic placeholders, then conditionally populated or updated only when LLM mode is invoked.
- `input/metadata.yaml` stores session overrides only under `overrides` with allowed keys from Precedence Rules.

## Artifact Naming Conventions: Canonical vs Sidecar

### Canonical Artifacts
- Canonical output filenames are fixed and authoritative: `output/prompt_for_agent.md`, `output/context_bundle.md`, `output/context_manifest.json`, `output/review_decision.md`, `output/review_issues.md`, and `output/next_prompt.md`.
- Canonical names are stable across runs and never provider-specific.

### Sidecar Artifacts
- LLM sidecars are provider-agnostic and live only under `output/llm/`.
- Minimum sidecar set is fixed: `output/llm/augmentation.md`, `output/llm/review_critique.md`, and `output/llm/metadata.json`.
- Provider/model identity is recorded in `output/llm/metadata.json`, not in filenames.
- Sidecar names never collide with canonical filenames.
- Sidecar lifecycle is fixed: files always exist after `pg session new`; content is placeholder-only until an LLM-enabled operation updates the relevant sidecar.
- Sidecar artifacts are excluded from canonical hash and review authority pipelines.

## Phase 0 - Repository Bootstrap

### Goals
- Establish packaging, CLI wiring, test harness, and baseline tooling.

### Tasks
- `P0-T1` Define bootstrap expectations for greenfield repository initialization and guard behavior.
- `P0-T2` Pin Python 3.12 and define `pyproject.toml` packaging plan.
- `P0-T3` Plan virtual environment workflow and CLI entrypoint.
- `P0-T4` Plan pytest baseline and deterministic test execution contract.
- `P0-T5` Plan formatting/linting policy.
- `P0-T6` Plan initial source and test scaffolding.

### Phase 0 Test Strategy
- CLI import smoke checks.
- `pg --help` exit behavior check.
- Pytest collection and baseline tooling checks.

## Phase 1 - Core CLI and Session Model

### Goals
- Implement core command skeleton and session lifecycle with isolation guarantees.

### Tasks
- `P1-T1` Plan `pg init` creation behavior with `--force` overwrite rules.
- `P1-T2` Plan `pg session new`, `pg session list`, and `pg session use` behavior.
- `P1-T3` Plan session naming format and collision handling.
- `P1-T4` Plan active-session state persistence and lookup.
- `P1-T5` Plan no cross-session reads and no cross-session writes.

### Phase 1 Test Strategy
- Init tree assertions.
- Session naming/collision assertions.
- Session listing order assertions.
- Active-session switching assertions.
- Isolation assertions.

## Phase 2 - Context Artifacts Scaffolding

### Goals
- Create and document all context artifacts with deterministic instructional placeholders.
- Ensure discoverability through pack mapping without code changes.
- Keep deterministic and non-authoritative boundaries explicit in scaffolded files.

### Tasks
- `P2-T1` Define deterministic scaffold content for `.pg/AGENTS.md` with required sections: purpose and usage rules, authoritative vs non-authoritative boundary notes, context-pack interpretation rules, and explicit do-not-execute-code statement.
- `P2-T2` Define auto-generated context files produced by `pg init` and their instructional scaffold content.
- `P2-T3` Define per-session user-provided context placeholders under `input/context/` using one required instructions convention for all placeholders.
- `P2-T4` Define pack mapping and discoverability in `.pg/context/project/packs.yaml`, including how users add files and include them in packs without code changes.
- `P2-T5` Define hashing inclusion policy: placeholders are excluded unless selected by pack; if selected, full normalized file content including scaffold instructions participates in hashing and manifest generation.
- `P2-T6` Define scaffold-edit expectation: editing scaffold instructions in included files changes canonical hashes and is expected behavior.

### Placeholder Instructions Convention (Required Standard)
- Required standard is Option C hybrid with one visible header `## Instructions (Scaffold)` followed immediately by one HTML comment block containing detailed guidance.
- Required fields inside the comment block are `PURPOSE`, `EXPECTED_FORMAT`, `NORMALIZATION`, `DO_NOT_INCLUDE`, and `USER_CONTENT_START`.
- Markdown body for user-authored content begins only after the convention block.
- This standard applies to all scaffold placeholders, including session context placeholders and LLM sidecar placeholders.

### Deliverables
- Init-created context artifacts: `.pg/AGENTS.md`, `.pg/context/global/rules.md`, `.pg/context/global/output_format.md`, `.pg/context/global/risk_policy.md`, `.pg/context/project/README.md`, `.pg/context/project/packs.yaml`, `.pg/context/project/session_context_guide.md`, `.pg/context/project/user_context_slots.md`.
- Session-created placeholder artifacts: `.pg/sessions/<session_id>/input/context/user_notes.md`, `.pg/sessions/<session_id>/input/context/domain_context.md`, `.pg/sessions/<session_id>/input/context/constraints.md`, `.pg/sessions/<session_id>/output/llm/augmentation.md`, `.pg/sessions/<session_id>/output/llm/review_critique.md`, `.pg/sessions/<session_id>/output/llm/metadata.json`.
- Instruction block requirements in every placeholder include purpose, expected format, normalization expectations, and prohibited content.

### Phase 2 Test Strategy
- `pg init` scaffold tree assertions for all required artifact files.
- Placeholder content assertions verify exact hybrid convention structure and required field labels.
- `pg session new` assertions verify session context placeholder creation with required convention block.
- `pg session new` assertions verify sidecar placeholders are always created in `output/llm/`.
- Pack discoverability assertions verify user-added files can be referenced in `packs.yaml` without code changes.
- Hash-policy assertions verify scaffold instruction edits change manifest/hash only when the file is selected by pack.
- Cross-session leakage checks aligned with Phase 1 isolation tests.

### Phase 2 Risks and Edge Cases
- Missing scaffold artifacts can break downstream context generation and review phases.
- Weak or inconsistent inline instructions can cause user misconfiguration and non-deterministic inputs.
- Instruction text edits in included placeholders change hashes; this is expected and must be documented to users.
- Empty versus scaffolded placeholders can cause surprise if inclusion policy is misunderstood.

## Phase 3 - Deterministic Context Engine

### Goals
- Implement deterministic context normalization, ordering, hashing, manifest generation, and size enforcement.

### Tasks
- `P3-T1` Plan pack resolution with CLI-order application.
- `P3-T2` Plan normalization rules: UTF-8, LF, no BOM, relative paths, symlink realpath handling, deterministic sorting, and prepended `AGENTS.md`.
- `P3-T3` Plan deterministic SHA-256 manifest generation.
- `P3-T4` Plan context size warning and hard-fail behavior.
- `P3-T5` Plan explicit hashing note in user docs: if a scaffold placeholder is in a selected pack, its full normalized content including instruction block is hashed; scaffold edits therefore change hashes and are expected.

### Phase 3 Test Strategy
- Normalization stability snapshots.
- Manifest reproducibility checks.
- Pack-order determinism checks.
- Size threshold and hard-fail checks.
- Path and symlink handling checks.
- Included-placeholder hash-delta checks for instruction-block edits.

## Phase 4 - Deterministic Prompt Generator (`--no-llm`)

### Goals
- Implement canonical deterministic prompt generation and strict prompt contract enforcement.

### Tasks
- `P4-T1` Plan deterministic mode template rendering for `plan`, `implement`, and `investigate`.
- `P4-T2` Plan strict heading contract validator.
- `P4-T3` Plan canonical output generation for prompt, bundle, and manifest artifacts.
- `P4-T4` Plan deterministic `--dry-run` behavior.
- `P4-T5` Plan byte-identical reproducibility guarantees.

### Phase 4 Test Strategy
- Heading presence/order checks.
- Missing/reordered heading negatives.
- Snapshot reproducibility checks.
- Dry-run no-write checks.

## Phase 5 - Local LLM Provider Abstraction (Mandatory)

### Goals
- Implement required pluggable local provider layer with strict deterministic boundaries.

### Tasks
- `P5-T1` Define `LocalLLMProvider` contract and provider envelope types.
- `P5-T2` Plan provider registry and config-driven provider selection.
- `P5-T3` Plan default Ollama adapter.
- `P5-T4` Plan sidecar-only augmentation service boundary using fixed sidecar paths under `output/llm/` and fixed lifecycle semantics.
- `P5-T5` Plan hard provider bypass in `--no-llm`.
- `P5-T6` Plan timeout/retry/fallback behavior that preserves deterministic outputs.
- `P5-T7` Plan provider mocks and test doubles.

### Provider Contract

#### Request Envelope
- Reference format is explicit and immutable: canonical artifact references are relative paths from session root.
- Required reference fields are `prompt_ref: output/prompt_for_agent.md`, `context_ref: output/context_bundle.md`, and `manifest_ref: output/context_manifest.json`.
- Optional review-context references for critique mode are also relative paths from session root and constrained to canonical artifact allowlists.
- Envelope carries identifiers and runtime controls: `provider_id`, `model_id`, timeout settings, retry settings, purpose, request/session correlation ids, and timestamp.
- Envelope does not carry embedded full canonical content blobs.
- Envelope does not allow arbitrary absolute paths or out-of-session path references.
- Provider reads canonical artifacts from disk via safe path-boundary helpers.
- Envelope cannot mutate canonical artifacts.

#### Response Envelope
- Fields include generated text payload, provider metadata, resolved model metadata, timing metrics, retry usage, normalized error category, and provider-native error detail.
- Sidecar write mapping is fixed: augmentation text updates `output/llm/augmentation.md`, review critique text updates `output/llm/review_critique.md`, and metadata/errors update `output/llm/metadata.json`.
- Sidecar files always exist from session scaffold; LLM operations update content conditionally.
- Response is sidecar-targeted and excluded from canonical authority.

#### `healthcheck` Requirements
- Reachability validation must test provider endpoint availability.
- Model availability validation must test configured model resolvability/availability.
- Healthcheck result must report both signals separately.

#### Streaming Scope
- Streaming is deferred in v1.
- Future extension point is provider response envelope streaming events without changing deterministic authority boundaries.

#### Non-Authoritative Invariants
- Provider output never mutates canonical deterministic artifacts.
- Provider artifacts are sidecar-only in `output/llm/`.
- Canonical hash and manifest pipelines ignore sidecar files.
- Deterministic review gate never takes authoritative input from sidecars.

### Phase 5 Test Strategy
- Provider registry selection checks.
- Provider adapter mapping checks.
- Timeout/retry/error normalization checks.
- Provider unavailability fallback checks.
- `--no-llm` zero-provider-call assertions.
- Sidecar boundary and hash-isolation assertions tied to fixed sidecar filenames and lifecycle rules.

## Adding a New Local LLM Provider

### Steps
- Add provider module under `src/pg/llm/providers/<provider_id>.py`.
- Implement `LocalLLMProvider` request/response/healthcheck contract.
- Register provider id in provider registry.
- Add provider config keys under `providers.<provider_id>.*`.
- Extend config validation for required provider keys.
- Add provider unit tests for mapping, metadata, and error normalization.
- Add integration tests with mock transport and sidecar behavior checks.

### Compatibility Checklist
- Timeout and retry semantics conform to shared contract.
- Healthcheck distinguishes endpoint reachability from model availability.
- Response metadata fields are populated or explicitly marked unavailable.
- Provider output is sidecar-only under `output/llm/`.
- `--no-llm` bypass remains absolute.
- Provider failures degrade to deterministic behavior without canonical mutation.

## Phase 6 - Review Gate System

### Goals
- Implement deterministic response contract validation and authoritative GREEN/AMBER/RED decisions.

### Tasks
- `P6-T1` Plan validation for required non-empty response sections.
- `P6-T2` Plan deterministic classifier for GREEN, AMBER, and RED triggers.
- `P6-T3` Plan authoritative exit-code mapping.
- `P6-T4` Plan review artifact generation.
- `P6-T5` Plan optional LLM critique sidecar update to `output/llm/review_critique.md` and `output/llm/metadata.json`.
- `P6-T6` Plan strict review boundary: deterministic classification executes before any optional LLM critique and remains the only source of `review_decision.md` and exit codes.

### Phase 6 Test Strategy
- Response contract positives and negatives.
- Classifier matrix checks.
- Exit-code mapping checks.
- Strict-mode behavior checks.
- LLM critique non-authoritative checks.
- Review-order checks confirming deterministic decision is finalized before critique sidecar path executes.
- `pg review --no-llm` checks confirming no provider resolution/calls and no sidecar content updates beyond scaffold placeholders.

## Phase 7 - Configuration and Security Boundaries

### Goals
- Lock precedence behavior, path safety boundaries, and strict deterministic policies.

### Tasks
- `P7-T1` Plan precedence implementation: CLI > session overrides (`input/metadata.yaml:overrides`) > config > defaults.
- `P7-T2` Plan schema validation for baseline and provider-specific settings, plus allowed override-key validation.
- `P7-T3` Plan repo-root read-boundary enforcement.
- `P7-T4` Plan `.pg/` write-boundary enforcement.
- `P7-T5` Plan strict-mode failure policy and diagnostics.
- `P7-T6` Plan explicit prohibition of code execution and agent-command execution.
- `P7-T7` Plan forbidden-override-domain enforcement for deterministic contracts.

### Phase 7 Test Strategy
- Precedence checks across all layers.
- Deterministic override resolution tests using `input/metadata.yaml`.
- Allowed-key and forbidden-domain override validation checks.
- Invalid/missing config checks.
- Path traversal and symlink escape checks.
- Out-of-bound write rejection checks.
- Strict-mode deterministic failure checks.

## Phase 8 - End-to-End Flow and Integration Tests

### Goals
- Validate deterministic baseline and LLM-enabled branch behavior with low flake risk.

### Tasks
- `P8-T1` Plan deterministic full flow: init -> session new -> generate `--no-llm` -> review `--no-llm`.
- `P8-T2` Plan LLM-enabled flow with provider mocks.
- `P8-T3` Plan tagged local-provider smoke coverage.
- `P8-T4` Plan deterministic regression and drift checks.

### LLM-Enabled Structural Invariants (Allowed Assertions)
- Sidecar files always exist after `pg session new`: `output/llm/augmentation.md`, `output/llm/review_critique.md`, and `output/llm/metadata.json`.
- In no-LLM flows, sidecar files remain scaffold-only placeholders and provider call count is zero.
- In LLM-enabled generate flows, `output/llm/augmentation.md` and `output/llm/metadata.json` are updated.
- In LLM-enabled review critique flows, `output/llm/review_critique.md` and `output/llm/metadata.json` are updated.
- `output/llm/metadata.json` contains `provider_id` and `model_id` for LLM-invoked operations.
- Canonical artifacts are byte-identical across repeated `--no-llm` runs.
- Canonical hash/manifest remain unchanged by sidecar presence or sidecar content changes.
- `--no-llm` tests assert provider bypass.

### LLM-Enabled Assertions to Avoid
- Exact freeform LLM text.
- Exact token ordering.
- Exact latency values.
- Provider-native phrasing beyond normalized structure.

### Phase 8 Test Strategy
- Golden canonical snapshots.
- Provider spy assertions.
- Sidecar schema and metadata checks for fixed file names and lifecycle behavior.
- Large-context boundary coverage.
- End-to-end precedence checks showing deterministic override resolution.
- End-to-end review-order checks showing deterministic classification authority precedes optional critique.

## Traceability Matrix (Spec Requirement -> Phase/Task)

| Spec Ref | Requirement | Phase/Task Mapping |
|---|---|---|
| 1 | Workflow contract only; no code execution/edit/test automation | P7-T6, P6-T2, Non-Goals |
| 2.1 | Deterministic by default | P3-T2, P4-T5, P6-T2 |
| 2.2 | Offline-first | P4-T5, P5-T5 |
| 2.3 | Session-isolated | P1-T5, P2 Test Strategy |
| 2.4 | Reproducible | P3-T3, P4-T5, P8-T4 |
| 2.5 | LLM-optional in spec overridden to mandatory non-authoritative subsystem | Spec Delta, P5-T1..P5-T7 |
| 2.6 | Safe by design | P7-T3, P7-T4, P7-T6 |
| 3.1.1 | `pg init` | P1-T1, P2-T1, P2-T2 |
| 3.1.2 | Session management commands | P1-T2..P1-T4, P2-T3 |
| 3.1.3 | Deterministic `pg generate --no-llm` | P4-T1..P4-T5, P5-T5 |
| 3.1.4 | Deterministic `pg review --no-llm` | P6-T1..P6-T3, P6-T6 |
| 3.1.5 | Context pack resolution | P2-T4, P3-T1 |
| 3.1.6 | Deterministic manifest generation | P3-T3, P3-T5 |
| 3.1.7 | Ollama integration via pluggable provider layer | P5-T1..P5-T7 |
| 3.2 | Explicit out-of-scope list | Non-Goals, Deferred Backlog |
| 4.1 | Python/Typer/PyYAML/Jinja2/Rich/hashlib/pathlib | P0-T2 |
| 4.2 | Local runtime and non-authoritative LLM behavior | P5-T3, Provider Contract |
| 5 | `.pg` layout created by `pg init` | Runtime Layout, P1-T1, P2 Deliverables |
| 6.1-6.8 | Normalization rules and ordering | P3-T2 |
| 7 | Session naming and collision handling | P1-T3 |
| 7.1 | Session structure and isolation | Session Scaffold, P1-T5, P2-T3 |
| 8.1 | `pg init` force behavior | P1-T1 |
| 8.2 | `pg session new` and exit handling | P1-T2, P2-T3 |
| 8.3 | `pg session list` sorted | P1-T2 |
| 8.4 | `pg session use` | P1-T4 |
| 8.5 | `pg generate` options and outputs | CLI Surface, P4, P5, P7-T1 |
| 8.6 | `pg review` options and outputs | CLI Surface, P6-T1..P6-T6 |
| 9 | Prompt heading contract | P4-T2 |
| 10 | Agent response contract | P6-T1 |
| 11 | Review authority and exit codes | P6-T2..P6-T6 |
| 12 | Manifest schema | P3-T3 |
| 13 | Context size limits | P3-T4, P7-T2 |
| 14 | Config baseline keys | P7-T2, P7-T7 |
| 15 | Security boundaries | P7-T3..P7-T6 |
| 16.1 | Safe bootstrap | P1-T1, P2-T2 |
| 16.2 | Session isolation | P1-T5 |
| 16.3 | Stable deterministic manifest | P3-T3, P3-T5 |
| 16.4 | Offline generate `--no-llm` | P4-T5, P5-T5 |
| 16.5 | Review `--no-llm` correctness | P6-T2, P6-T6 |
| 16.6 | Exit codes reflect gate decision | P6-T3, P6-T6 |
| 16.7 | Works without active provider runtime | P5-T5, P5-T6 |
| 16.8 | Context size enforcement | P3-T4 |
| 16.9 | Unit tests pass | P0-T4, P8 |
| 17 | Unit and integration test plan | P1..P8 |
| 18.1-18.9 | Implementation order coverage with context scaffolding phase | P0..P8 |
| 19 | Reinforced non-goals | Non-Goals |
| 20 | Future extensions | Deferred Backlog |
| Final Statement | MVP incomplete without offline deterministic `--no-llm` | Spec Delta Invariants, P4-T5, P5-T5, P8-T1 |

## Risks and Edge Cases

| Risk / Edge Case | Failure Mode | Mitigation | Detection |
|---|---|---|---|
| Missing context scaffolds | Later phases fail due missing required artifacts | Enforce Phase 2 deliverable checks and init/session scaffold assertions | Tree and deliverable tests |
| Placeholder convention drift | Inconsistent instruction formatting causes ambiguity | Enforce single hybrid convention and field labels | Placeholder convention assertions |
| Instruction-edit hash impact surprise | Scaffold edits change hash unexpectedly when included | Document expected behavior in P2-T6/P3-T5 and user guidance | Hash-delta tests for included placeholders |
| Sidecar lifecycle ambiguity | Contributors assume wrong file existence semantics | Fix lifecycle policy as always-scaffolded placeholders plus conditional updates | Lifecycle assertions in session and e2e tests |
| Sidecar naming collision | LLM artifacts overwrite canonical outputs | Fixed `output/llm/` sidecar namespace and canonical filename reservation | Path collision tests |
| Session override misuse | Overrides alter deterministic contracts | Allowed-key whitelist and forbidden-domain enforcement | Override validation tests |
| Hash instability | Same inputs produce different hashes | Single normalization pipeline and deterministic ordering | Reproducibility suite |
| Session collisions | Session overwrite | Deterministic collision suffix logic | Collision tests |
| Provider timeout | LLM path stalls | Timeout/retry and deterministic fallback | Provider timeout tests |
| LLM hallucinated structure | Invalid generated sections | Canonical artifacts remain deterministic-only | Boundary isolation tests |
| Deterministic drift | Canonical output changes unexpectedly | Snapshot regression checks | Drift tests |
| Model switching incompatibility | Backend shape mismatch | Provider contract and adapter conformance tests | Multi-provider mock tests |
| OS path differences | Path normalization instability | Relative path normalization policy | Cross-platform tests |
| Large context handling | Exceeded limits and unstable warnings | Byte accounting and hard enforcement | Boundary-size tests |
| Symlink traversal | Out-of-root reads | Realpath confinement checks | Security traversal tests |
| `--no-llm` contamination | Provider called in deterministic mode | Hard bypass guard and provider spies | Zero-provider-call tests |

## Explicit Non-Goals (v1)

- No automatic execution of repository code.
- No execution of agent-provided shell commands.
- No source mutation outside `.pg/`.
- No internet-based RAG.
- No IDE integration.
- No repo-wide auto-scanning.
- No model fine-tuning.
- No git workflow orchestration.
- No CI orchestration as runtime behavior.
- No background daemons.

## Deferred Backlog

- Streaming provider output support.
- Additional provider adapters beyond Ollama.
- Structured JSON output mode.
- Context diffing between sessions.
- Deterministic replay UX improvements.
- Model benchmarking mode.
- CI integration beyond local deterministic test contract.
- IDE/editor extension integration.

## Assumptions and Defaults

- Local LLM integration is mandatory but non-authoritative.
- Default provider is `ollama` when LLM mode is enabled.
- `--no-llm` is canonical and fully bypasses provider logic.
- Provider failures degrade to deterministic outputs with warnings.
- Existing config keys remain supported; provider-aware keys are additive.
- Session placeholder files are created by `pg session new` and are pack-includable without code changes through `packs.yaml`.
- Session overrides are stored in `input/metadata.yaml` and constrained to allowed LLM runtime keys only.
- Sidecar files are always scaffolded and only populated by LLM-invoked operations.
