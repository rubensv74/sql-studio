# AI Development Framework

Version: 1.0

---

# Mission

This repository is developed collaboratively by humans and AI agents.

The objective is to build production-quality software.

Prototype code is not acceptable.

---

# Source of Truth

Git is the only source of truth.

Never regenerate the repository.

Always work from the current repository state.

---

# Architecture

Respect the approved architecture.

Do not redesign the project unless explicitly requested.

Refactoring is allowed only when it clearly improves maintainability and does not change behaviour.

---

# Development Rules

- Implement only the requested sprint.
- Modify only the files required.
- Never rewrite unrelated modules.
- Prefer extending existing code over replacing it.
- Keep backward compatibility whenever possible.

---

# Coding Standards

- Python 3.12+
- Type hints whenever practical.
- Small, cohesive classes.
- Single Responsibility Principle.
- Prefer composition over inheritance.
- No duplicated logic.
- Clear naming.
- No dead code.
- No commented-out code.

---

# Error Handling

All public APIs must:

- validate inputs
- provide meaningful exceptions
- avoid silent failures
- fail gracefully

CLI commands must:

- return exit code 0 on success
- return non-zero on failure
- print errors to stderr

---

# Testing

Every sprint must include tests whenever functionality changes.

Tests should cover:

- happy path
- edge cases
- invalid input
- regression scenarios

---

# Dependencies

Avoid external dependencies unless they provide significant value.

Prefer the Python standard library.

---

# Performance

Avoid unnecessary allocations.

Avoid reading the same file multiple times.

Prefer streaming over loading large datasets into memory.

Measure before optimizing.

---

# AI Agent Behaviour

The AI agent must:

- understand the repository before coding
- analyse existing code
- reuse existing components
- avoid architectural drift

Before finishing:

- run available tests
- validate imports
- validate CLI
- report modified files
- report deleted files
- report created files

---

# Commit Convention

Use Conventional Commits.

Examples:

feat(repository): add repository engine

fix(scanner): improve SQL classification

refactor(core): simplify scanner

test(repository): increase coverage

docs(architecture): update AI workflow

---

# Sprint Definition of Done

A sprint is complete only if:

- implementation finished
- tests passing
- no obvious regressions
- code reviewed
- repository builds successfully
- Git working tree is clean

---

# Forbidden

Do not:

- invent functionality
- create placeholder implementations
- add TODO-only code
- duplicate modules
- modify unrelated files
- change architecture without approval

---

# Working Cycle

1. Analyse repository
2. Understand sprint
3. Implement
4. Self-review
5. Execute validations
6. Present modified files
7. Commit
8. Start next sprint
