# Agent Contribution Guidelines for AutoFlow

This document outlines the standards, workflow, and principles for AI agents contributing to the `pingcap/autoflow` repository. Adherence is mandatory for all agent-generated code.

## 1. Guiding Principles

### 1.1. Minimal Change Principle (MCP)

All modifications must be the **smallest possible change** that fulfills the requirements in `PRD.txt`. Agents must strive for elegance and simplicity.
*   **Prioritize Modification:** Modify existing functions rather than creating new ones unless explicitly required (e.g., the new config file).
*   **Validation:** The `nx-mcp` tool MUST be used to validate the impact scope and minimalism of all changes before submission. Contributions introducing excessive complexity will be rejected.

### 1.2. Backward Compatibility

Preserving existing functionality is paramount.
*   **Feature Flags:** All new or enhanced behavior MUST be gated behind feature flags defined in `core/autoflow/configs/knowledge_graph.py`.
*   **Default Behavior:** The default configuration (`enable_enhanced_kg=False`) MUST replicate the legacy behavior exactly.
*   **API Stability:** Do not alter public API signatures. New parameters must be optional.

### 1.3. Context Awareness

Agents must utilize available tools to understand the codebase before making changes.
*   Use `ref` and `context7` for precise navigation and local context.
*   Use `deepgraph.co` for architectural dependency understanding.

## 2. Coding Standards

### 2.1. Style Guide

Adhere to the existing style of the repository (generally PEP 8).
*   **Formatting:** Use `black`.
*   **Linting:** Use `flake8`.
*   **Typing:** Use `mypy`. All function signatures must be type-hinted.
*   **Imports:** Use `isort`.

### 2.2. Code Quality

*   **Error Handling:** Implement robust error handling. Use `try...except` blocks for error isolation, especially in parallel processing (`index.py`). Failure of one chunk must not halt the batch.
*   **Logging:** Use the existing logging framework. Log significant events (e.g., entity merges, cache hits/misses, errors) at appropriate levels.
*   **Dependencies:** Do not introduce new external libraries unless specified in the PRD (e.g., `cachetools` for LRU cache, if required and not already present).

## 3. Implementation Workflow (Agent Specific)

1.  **Specification Review:** (Coder Agents) Review the `ImplementationSpec`. Use `ref` to locate target files/lines.
2.  **Context Analysis:** (Coder Agents) Analyze the surrounding code using `context7` and `ref`.
3.  **Implementation:** (Coder Agents) Apply the changes using `codegpt`, adhering to MCP and coding standards. Ensure correct feature flag usage.
4.  **Validation:** (Tester Agent) Execute unit tests and `kg_benchmark.py`. Verify metrics against PRD targets.
5.  **Review:** (Reviewer Agent) Audit the changes using `coderabbit` (quality/performance) and `nx-mcp` (minimalism).

## 4. Repository Management

### 4.1. Branching

The Orchestrator manages the branching strategy. Development occurs on `feature/kg-enhancement`.

### 4.2. Commit Messages

Use Conventional Commits format: `<type>(<scope>): <description>`

*   **Type:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
*   **Scope:** The module affected (e.g., `kg-config`, `tidb-store`, `extractor`, `kg-index`).

**Example:** `feat(tidb-store): Implement LRU cache and normalization utilities`

## 5. Testing and Evaluation

*   **Benchmarking:** The primary validation mechanism is `examples/kg_benchmark.py`.
*   **Unit Tests:** If new utilities are added (e.g., normalization functions), accompanying unit tests must be created. Tests must cover both enabled and disabled states of the feature flag.
*   **Integration Tests:** Ensure existing integration tests pass.

## 6. Review Checklist (For Reviewer Agent)

- [ ] Does the code fulfill the phase requirements?
- [ ] Is the change minimal (validated via `nx-mcp`)?
- [ ] Is the new behavior correctly gated by feature flags?
- [ ] Are public APIs unchanged?
- [ ] Does the code adhere to the style guide?
- [ ] Are performance benchmarks met (validated via `coderabbit` profiling and `BenchmarkResult`)?
