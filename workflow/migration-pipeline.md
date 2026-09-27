# Migration Pipeline — Orchestration Workflow

This document is the step-by-step script followed by the **Migration Orchestrator** mode to execute
a full Java → Python/TypeScript migration. Read `workflow/pipeline-config.json` at session start.

---

## Pre-flight Checklist

Before starting, confirm:
- [ ] MCP server is built: `mcp-server/build/index.js` exists
- [ ] Config is loaded: `workflow/pipeline-config.json` is readable
- [ ] Source directory exists and contains `.java` files
- [ ] Python ≥ 3.10 or Node.js ≥ 18 is available (depending on target language)
- [ ] `pytest` (Python) or `jest` (TypeScript) is installed

---

## Stage 0 — Discovery

```
TOOL: list_source_files(directory=config.source.root_dir, extension=".java")
```

Build a **migration manifest**: a table of all Java files to migrate, with status `PENDING`.

```
| File                   | Status  | Issues |
|------------------------|---------|--------|
| UserService.java       | PENDING |        |
| OrderProcessor.java    | PENDING |        |
| UserServiceTest.java   | PENDING |        |
```

Mark test files (matching `*Test.java`, `*Tests.java`) separately — they go to the Test Generator,
not the Migration Agent.

---

## Stage 1 — Structural Analysis (per file)

For each non-test Java file:

```
TOOL: parse_java_ast(file_path=<java_file>)
```

Record: class name, method count, field count, dependencies (imports). This forms the
**complexity score** used to sort migration order: lowest complexity first.

---

## Stage 2 — Migration (per file, in complexity order)

For each file in sorted manifest:

1. **Invoke Migration Agent** (load `agents/migration-agent.md` as system prompt)
   - Provide: Java AST + full source
   - Target: `config.target.language`
   - Output path: `config.target.output_dir/<snake_case_name>.<ext>`

2. Update manifest: `MIGRATED` or `FAILED`

3. If `FAILED`: log error, continue to next file (do not halt pipeline)

---

## Stage 3 — Test Generation (per migrated file)

For each `MIGRATED` file:

1. Find corresponding Java test file (e.g. `UserService.java` → `UserServiceTest.java`)
2. **Invoke Test Generator Agent** (load `agents/test-generator-agent.md` as system prompt)
   - Provide: migrated file path, Java test path (if found)
   - Output path: `config.target.test_output_dir/test_<name>.py` (or `.test.ts`)
3. Update manifest: `TESTED` or `TEST_FAILED`

---

## Stage 4 — Validation (per tested file)

For each `TESTED` file:

1. **Invoke Validator Agent** (load `agents/validator-agent.md` as system prompt)
   - Provide: migrated file, test file, original Java file
2. Validator runs:
   - Phase 1: `static_analysis`
   - Phase 2: `run_tests`
   - Phase 3: structural comparison via `parse_java_ast` + `diff_files`
   - Phase 4: `compare_behavior` (if behavioral outputs are captured)
3. Update manifest:
   - All phases pass → `VALIDATED ✅`
   - Some phases pass → `PARTIAL ⚠️`
   - Phase 1 or 2 fails → `FAILED ❌`, re-invoke Migration Agent with error context (max 2 retries)
   - Regression detected → `REGRESSION ❌`, halt and escalate to user

---

## Stage 5 — Report Generation

Generate `migration-report.md` with:

```markdown
# Migration Report
Generated: <timestamp>
Config: workflow/pipeline-config.json

## Summary
- Total files:     N
- Validated:       N  ✅
- Partial:         N  ⚠️
- Failed:          N  ❌
- Regressions:     N  ❌

## Per-file Results
<manifest table with final statuses>

## Issues
<list of all failures with error details>
```

---

## Retry / Escalation Policy

| Condition                         | Action                                          |
|-----------------------------------|-------------------------------------------------|
| Migration produces invalid code   | Re-invoke Migration Agent with AST + error (×2) |
| Tests fail > 20%                  | Re-invoke Migration Agent with failing tests     |
| Static analysis score < 7.0       | Re-invoke Migration Agent with pylint output     |
| Regression detected               | HALT — escalate to user, do not auto-retry       |
| All retries exhausted             | Mark `FAILED`, continue to next file             |

---

## Invocation

Switch to **Migration Orchestrator** mode in Bob, then:

```
Run the migration pipeline using workflow/pipeline-config.json
```

Bob will execute all stages autonomously, updating the manifest and reporting status after each file.
