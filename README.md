# Java → Python/TypeScript Migration Orchestration System

> **Bob orchestrates specialized agents → MCP provides engineering tools →
> migration is executed → tests are generated → old/new behavior is automatically validated.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BOB (Migration Orchestrator Mode)                 │
│                    .bob/custom_modes.yaml                            │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              ORCHESTRATION PIPELINE                          │    │
│  │         workflow/migration-pipeline.md                       │    │
│  │                                                              │    │
│  │  Stage 0: Discovery        Stage 1: Analysis                │    │
│  │  list_source_files()  ───► parse_java_ast()                 │    │
│  │         │                                                    │    │
│  │         ▼                                                    │    │
│  │  Stage 2: Migration        Stage 3: Test Generation         │    │
│  │  Migration Agent      ───► Test Generator Agent             │    │
│  │  agents/migration-agent.md agents/test-generator-agent.md  │    │
│  │         │                        │                          │    │
│  │         ▼                        ▼                          │    │
│  │  Stage 4: Validation                                        │    │
│  │  Validator Agent                                            │    │
│  │  agents/validator-agent.md                                  │    │
│  │         │                                                    │    │
│  │         ▼                                                    │    │
│  │  Stage 5: Report → migration-report.md                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              │ MCP Tools                             │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   MCP SERVER (stdio)                         │    │
│  │              mcp-server/src/index.ts                         │    │
│  │                                                              │    │
│  │  read_source_file    write_output_file   list_source_files  │    │
│  │  run_tests           compare_behavior    parse_java_ast      │    │
│  │  diff_files          static_analysis                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
   demo/java-source/              demo/migrated-output/
   UserService.java               user_service.py
   OrderProcessor.java            order_processor.py
   UserServiceTest.java           tests/test_user_service.py
```

---

## Project Structure

```
.
├── .bob/
│   └── custom_modes.yaml          # Migration Orchestrator mode definition
│
├── mcp-server/
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       └── index.ts               # MCP server — 8 engineering tools
│
├── agents/
│   ├── migration-agent.md         # Prompt: Java → Python/TS translation
│   ├── test-generator-agent.md    # Prompt: test suite generation
│   └── validator-agent.md         # Prompt: behavioral validation
│
├── workflow/
│   ├── pipeline-config.json       # Pipeline configuration
│   └── migration-pipeline.md      # Step-by-step orchestration script
│
├── demo/
│   ├── java-source/               # Source Java monolith
│   │   ├── UserService.java
│   │   ├── OrderProcessor.java
│   │   └── UserServiceTest.java
│   └── expected-output/           # Reference migrated Python output
│       ├── user_service.py
│       ├── order_processor.py
│       └── test_user_service.py
│
├── requirements.txt               # Python test/lint dependencies
└── README.md
```

---

## MCP Server Tools

| Tool                | Description                                              |
|---------------------|----------------------------------------------------------|
| `read_source_file`  | Read any source file (Java, Python, TS)                  |
| `write_output_file` | Write migrated code; creates directories automatically   |
| `list_source_files` | Walk a directory, filter by extension                    |
| `run_tests`         | Execute `pytest` or `jest` and return full output        |
| `compare_behavior`  | Line-by-line diff of two program outputs                 |
| `parse_java_ast`    | Extract class/method/field structure from a Java file    |
| `diff_files`        | Unified diff between any two files                       |
| `static_analysis`   | Run `pylint` (Python) or `tsc --noEmit` (TypeScript)     |

---

## Quick Start

### 1. Build the MCP Server

```bash
cd mcp-server
npm install
npm run build
```

### 2. Register the MCP Server in Bob

Add to your workspace `.bob/mcp.json`:

```json
{
  "mcpServers": {
    "migration-tools": {
      "command": "node",
      "args": ["mcp-server/build/index.js"]
    }
  }
}
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Switch to Migration Orchestrator Mode

In Bob, open the mode picker and select **Migration Orchestrator**.
The mode becomes available immediately after the workspace loads.

### 5. Run the Pipeline

With the MCP server connected and the mode active, say:

```
Run the migration pipeline using workflow/pipeline-config.json
```

Bob will autonomously:
1. Discover all `.java` files in `demo/java-source/`
2. Parse each file's AST for structural analysis
3. Invoke the Migration Agent for each class
4. Invoke the Test Generator Agent for each migrated file
5. Invoke the Validator Agent (static analysis + test run + behavior diff)
6. Produce `migration-report.md`

---

## Agents

### Migration Agent (`agents/migration-agent.md`)
Translates a Java class to idiomatic Python or TypeScript. Follows a strict mapping table,
calls `parse_java_ast` + `read_source_file` before writing, and validates output with
`static_analysis` before finishing.

### Test Generator Agent (`agents/test-generator-agent.md`)
Ports existing JUnit tests to pytest/Jest and fills coverage gaps. Covers happy paths, edge
cases, and error paths. Runs tests after writing to confirm the file executes.

### Validator Agent (`agents/validator-agent.md`)
Four-phase validation pipeline:
1. **Static analysis** — pylint / tsc --noEmit
2. **Test execution** — pytest / jest
3. **Structural equivalence** — method-by-method comparison via AST
4. **Behavioral diff** — line-by-line stdout comparison

Issues a structured `VALIDATION REPORT` for every file. Escalates regressions immediately.

---

## Validation Strategy

```
          ┌─────────────┐
          │ Static Check│ ──FAIL──► re-invoke Migration Agent (×2)
          └──────┬──────┘
                 │PASS
          ┌──────▼──────┐
          │ Run Tests   │ ──FAIL (>20%)──► re-invoke Migration Agent
          └──────┬──────┘
                 │PASS
          ┌──────▼──────┐
          │ Structural  │ ──MISSING METHODS──► re-invoke Migration Agent
          │ Equivalence │
          └──────┬──────┘
                 │PASS
          ┌──────▼──────┐
          │  Behavior   │ ──REGRESSION──► HALT, escalate to user
          │    Diff     │
          └──────┬──────┘
                 │PASS
          ┌──────▼──────┐
          │  VALIDATED  │ ✅
          └─────────────┘
```

---

## Configuration

Edit `workflow/pipeline-config.json` to change:

| Key                          | Purpose                                           |
|------------------------------|---------------------------------------------------|
| `source.root_dir`            | Directory with `.java` files to migrate           |
| `target.language`            | `"python"` or `"typescript"`                      |
| `target.output_dir`          | Where migrated files are written                  |
| `validation.min_test_pass_rate` | Minimum fraction of tests that must pass (0–1) |
| `validation.fail_on_regression`  | Halt pipeline on any behavioral regression     |
| `reporting.output_file`      | Path for the generated migration report           |

---

## Demo

The `demo/` directory contains a realistic Java monolith:

- **`UserService.java`** — user creation, retrieval, activation, deletion with full validation
- **`OrderProcessor.java`** — order processing with bulk discount and tax calculation
- **`UserServiceTest.java`** — 11 JUnit 5 tests with Mockito

The `demo/expected_output/` directory contains the reference Python migration for comparison
and as a baseline for the validator.

---

*Made with IBM Bob*
