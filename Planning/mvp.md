# PG (Prompt Generator) — MVP Specification (v2)

> Local-first, deterministic CLI for structured prompt generation and review gating.

---

# 1. Purpose

PG is a **local-first CLI workflow engine** that standardizes:

```
Natural language request
→ Structured prompt
→ Copilot Agent execution
→ Deterministic review gate (GREEN / AMBER / RED)
```

PG:

* DOES generate structured prompts.
* DOES enforce deterministic review rules.
* DOES NOT execute code.
* DOES NOT modify repository files.
* DOES NOT run tests.
* DOES NOT auto-edit source files.

It is a workflow contract tool — not an automation engine.

---

# 2. Design Principles

1. Deterministic by default
2. Offline-first
3. Session-isolated
4. Reproducible
5. LLM-optional
6. Safe by design

---

# 3. Scope

## 3.1 In Scope (MVP Must Ship)

1. `pg init`
2. Session management:

   * `pg session new`
   * `pg session list`
   * `pg session use`
3. Deterministic prompt generation:

   * `pg generate --no-llm`
4. Deterministic review gate:

   * `pg review --no-llm`
5. Context pack resolution
6. Deterministic manifest generation
7. Optional Ollama integration (non-authoritative)

---

## 3.2 Explicitly Out of Scope (v1)

* Running tests
* Executing commands
* Editing source files
* IDE integration
* Internet-based RAG
* Repo-wide automatic scanning
* Fine-tuning models
* Git integration
* CI automation

---

# 4. Technology Stack

## 4.1 Core

* Python 3.12
* Typer
* PyYAML
* Jinja2
* Rich
* hashlib
* pathlib

## 4.2 Optional LLM Runtime

* Ollama (local HTTP API)
* Default endpoint: `http://localhost:11434`

LLM features are non-authoritative and may not affect deterministic gate decisions.

---

# 5. Repository Layout

Running `pg init` creates:

```
.pg/
  config.yaml
  AGENTS.md
  templates/
    plan.md.j2
    implement.md.j2
    investigate.md.j2
    review.md.j2
  context/
    global/
      rules.md
      output_format.md
      risk_policy.md
    project/
      README.md
  packs.yaml
  sessions/
```

---

# 6. Deterministic Normalization Rules

All context files are normalized before hashing and concatenation:

1. UTF-8 encoding enforced
2. Line endings normalized to LF (`\n`)
3. No BOM allowed
4. Paths stored relative to repo root
5. Symlinks resolved to real paths
6. Files sorted lexicographically per pack
7. Packs applied in CLI order
8. `AGENTS.md` always prepended

Hashing uses SHA-256 of normalized content.

---

# 7. Session Model

Each session lives in:

```
.pg/sessions/<timestamp>_<slug>/
```

Timestamp format:

```
YYYY-MM-DD_HHMMSS
```

Collision handling:

* If identical timestamp occurs, append `_01`, `_02`, etc.

---

## 7.1 Session Structure

```
input/
  request.md
  metadata.yaml
  agent_response.md

output/
  prompt_for_agent.md
  context_bundle.md
  context_manifest.json
  review_decision.md
  review_issues.md
  next_prompt.md

logs/
  pg.log
```

Sessions are isolated. No cross-session reads.

---

# 8. Commands

## 8.1 `pg init`

Creates `.pg/` directory structure.

Options:

* `--force` (overwrites existing files)

Failure:

* Aborts if `.pg/` exists without `--force`.

---

## 8.2 `pg session new <name>`

Creates new session and marks it active.

Exit codes:

* 0 success
* 3 CLI error

---

## 8.3 `pg session list`

Lists sessions sorted by timestamp.

---

## 8.4 `pg session use <id>`

Sets active session.

---

## 8.5 `pg generate`

Modes:

```
--mode plan
--mode implement
--mode investigate
```

Required:

* Active session
* `input/request.md` present

Produces:

* `prompt_for_agent.md`
* `context_bundle.md`
* `context_manifest.json`

Options:

* `--pack <pack_name>` (repeatable)
* `--no-llm`
* `--model <model_name>`
* `--dry-run`

---

## 8.6 `pg review`

Required:

* `input/agent_response.md`
* Previous `prompt_for_agent.md`

Produces:

* `review_decision.md`
* `review_issues.md`
* `next_prompt.md`

Options:

* `--strict`
* `--no-llm`

---

# 9. Prompt Output Contract (Strict)

All generated prompts MUST contain exactly these headings in order:

```
1. Title
2. Risk Level
3. Execution Mode
4. Mission / Objective
5. Current State
6. Target State (Acceptance Criteria)
7. Constraints (Do Not Change / Non-Goals)
8. Proposed Steps
9. Tests (Agent must run)
10. Manual Verification Steps
11. Output Requirements
```

Validator checks exact presence of headings.

---

# 10. Agent Response Contract

Agent response MUST contain:

```
## Summary
## Files Changed
## Tests Executed
## Acceptance Criteria Coverage
## Manual Verification
```

Each section must be non-empty.

---

# 11. Review Gate (Deterministic)

## Exit Codes

| Code | Meaning   |
| ---- | --------- |
| 0    | GREEN     |
| 1    | AMBER     |
| 2    | RED       |
| 3    | CLI error |

---

## GREEN Requirements

* All required sections present
* Files list contains valid paths
* Tests include commands AND output blocks
* Acceptance criteria mapped explicitly
* Manual verification steps present

---

## AMBER Triggers

* Missing manual verification
* Tests listed but no output shown
* Acceptance criteria not fully mapped
* Files list incomplete

---

## RED Triggers

* Violates "Do Not Change" constraints
* Broad changes outside scope
* Claims tests pass without evidence
* Missing critical sections
* High-risk session + refactor language detected

Rule-based decision is authoritative.
LLM critique may elaborate but cannot override.

---

# 12. Context Manifest Structure

`context_manifest.json` includes:

```json
{
  "pg_version": "1.0.0",
  "template_sha256": "...",
  "config_sha256": "...",
  "model_name": "...",
  "model_digest": "...",
  "files": [
    {
      "path": "...",
      "sha256": "...",
      "bytes": 1234
    }
  ],
  "total_bytes": 123456,
  "pack_order": ["default", "django_standard"]
}
```

---

# 13. Context Size Limits

Config keys:

```yaml
max_context_bytes: 500000
warning_threshold_percent: 75
```

Behavior:

* Warning at threshold
* Hard fail if exceeded

---

# 14. Configuration (`.pg/config.yaml`)

```yaml
project_name: "My Project"

ollama_host: "http://localhost:11434"
default_model: "llama3.1:8b-instruct"
temperature: 0.2
max_tokens: 4096
timeout_seconds: 60
retry_count: 1

default_pack: "default"
strict_review: true
session_naming: "timestamp_slug"

max_context_bytes: 500000
warning_threshold_percent: 75
```

---

# 15. Security Boundaries

PG MUST:

* Never execute repository code
* Never modify files outside `.pg/`
* Never read outside repository root
* Never auto-run agent-provided commands
* Never execute shell commands from agent output

---

# 16. Acceptance Criteria (MVP)

MVP is complete when:

1. `pg init` safely bootstraps structure
2. Sessions isolate input/output/logs
3. Deterministic manifest stable across runs
4. `pg generate --no-llm` works fully offline
5. `pg review --no-llm` produces correct gate decisions
6. Exit codes reflect gate decision
7. Tool functions without Ollama
8. Context size enforcement works
9. Unit tests pass

---

# 17. Test Plan

## Unit Tests

* Session creation & activation
* Context normalization stability
* Manifest hashing reproducibility
* Template heading enforcement
* Validator rule classification
* Exit code mapping

## Integration Test

Flow:

```
pg init
pg session new test
pg generate --mode plan --no-llm
pg review --no-llm
```

Using canned fixtures.

---

# 18. Implementation Order

1. CLI skeleton
2. Config loader
3. `init`
4. Session manager
5. Context normalization + manifest
6. Template rendering (`--no-llm`)
7. Deterministic review gate
8. Exit code wiring
9. Ollama adapter (optional)

---

# 19. Non-Goals (Reinforced)

* No automatic code execution
* No CI orchestration
* No source code mutation
* No internet dependencies
* No background daemons

---

# 20. Future Extensions (Post-MVP)

* CI mode
* VS Code extension
* Git integration
* Structured JSON output mode
* Context diffing between sessions
* Deterministic replay mode
* Model benchmarking mode

---

# Final Statement

This MVP defines a **deterministic workflow contract engine**.

LLM features are auxiliary.
Determinism, safety, and reproducducibility are primary.

If it cannot operate offline in `--no-llm` mode, it is not complete.
