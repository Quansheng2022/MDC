# AGENTS.md

Project: md_converter

Version: 2.0

Status: Phase 1 MVP

---

# Purpose

This repository implements a production-quality Markdown → DOCX compiler.

The project follows a strict compiler architecture.

Markdown
    ↓
Parser
    ↓
AST
    ↓
Pipeline Passes
    ↓
Renderer
    ↓
Post Processor
    ↓
DOCX

Maintain this architecture.

Do not bypass compiler stages.

---

# Source of Truth

The following documents define the architecture.

CANONICAL_SPEC.md (project root)

docs/ARCHITECTURE.md

Architecture Decision Records (ADR)

Code

`CANONICAL_SPEC.md` is the single Canonical Authority for this repository.

If any document (including docs/ARCHITECTURE.md, design docs, theme YAML, code,
tests, or AI-generated plans) conflicts with `CANONICAL_SPEC.md`, the Canonical
Spec takes precedence.

Never introduce architectural changes without updating ADRs.

## Governance Rules (binding)

1. **Canonical Authority**: `CANONICAL_SPEC.md` 是唯一权威。所有 Plan、Test、
   Review 输出必须引用 SPEC-ID（如 `SPEC-ARCH-001`、`SPEC-INV-001`）。
2. **Specification Freeze**: `CANONICAL_SPEC.md` 当前为 FROZEN (1.0)。
   任何 FROZEN 条目的修改必须走
   ADR → Spec Update → SPEC_CHANGELOG → Re-freeze；不得由普通 Patch 顺便完成。
3. **Change Classification**: Review 输出必须按 `REVIEW_TEMPLATE.md` 分类
   （DEFECT / TEST_DEFECT / SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENT），
   并声明 Violated SPEC-ID、Allowed Scope、Forbidden Scope。
4. **Traceable Implementation**: 实施计划必须按 `IMPLEMENTATION_PLAN.md`
   登记 IMP-ID，引用 SPEC-ID/ADR-ID；不得修改未列入 Change Plan 的模块，
   发现额外问题只报告、不修改。
5. **Quality Gates**: StaticQA / RenderedQA / FinalArtifactQA 是强制阶段。
   FAIL 不得静默进入下一阶段；QA 基础设施异常默认 FAIL CLOSED。
6. **Release Evidence**: 没有 `RELEASE_EVIDENCE.md` / `release_evidence.json`
   的 build 不得标记为 Release Candidate。Release Decision 由规则生成。
7. **Golden Baseline**: 更新 Golden baseline 必须走
   investigate → ADR/Spec approval → approve baseline，不得由 Patch 自动完成。

Governance 到此为止，不再增加额外治理层级（不新增 Reviewer、审批层、
Agent 编排层）。

---

# Current MVP Scope

Implemented

- Headings
- Paragraphs
- Lists
- Tables
- Code Blocks
- Block Quotes
- Horizontal Rules
- Inline Formatting
- Images
- Hyperlinks
- Frontmatter
- Cover Page
- TOC
- Theme System
- DiagramPass
- NormalizePass
- Diagnostics
- Golden Tests

Not Yet Implemented

- Cross References
- Footnotes
- Incremental Compilation
- PDF Backend
- HTML Backend
- Multi-threaded Compilation

Avoid implementing unfinished features unless explicitly requested.

---

# Architecture Principles

This repository follows compiler design.

Never shortcut the pipeline.

Always follow

Markdown

↓

Parser

↓

Immutable AST

↓

Pipeline Passes

↓

Renderer

↓

Post Processor

↓

DOCX

---

# Layer Responsibilities

Parser

Responsible for

- Markdown parsing
- Syntax tree traversal
- AST construction

Parser must never

- generate DOCX
- render images
- perform business logic

---

Pipeline

Responsible for

AST transformations.

Examples

NormalizePass

DiagramPass

ReferencePass

Pipeline must never

- manipulate Word objects
- parse Markdown

---

Renderer

Responsible only for rendering AST.

Renderer converts nodes into Word structures.

Renderer must never

- parse Markdown
- call external APIs
- modify AST
- perform document post-processing

---

Post Processor

Responsible for

- Cover page
- TOC
- Table styling
- Font normalization
- Word automation

Renderer should never perform these tasks.

---

Services

Services provide external functionality.

Examples

DiagramService

MermaidService

MathRenderer

Services return data objects.

Services never modify AST.

---

# Dependency Rules

Dependencies must remain one-directional.

Parser

↓

AST

↓

Pipeline

↓

Renderer

↓

PostProcessor

↓

Services

Never introduce circular imports.

---

# AST Rules

AST is immutable.

All nodes should use

@dataclass(frozen=True)

Never mutate AST nodes.

Always return new nodes.

AST stores syntax only.

Never store rendering state.

Never store runtime state.

---

# Parser Rules

Use markdown-it-py.

Use SyntaxTreeNode.

Use BuilderRegistry.

Avoid large if/elif parsing logic.

Register new builders instead.

Parser should produce deterministic AST.

---

# Builder Rules

Each Builder should have one responsibility.

Preferred pattern

HeadingBuilder

ParagraphBuilder

TableBuilder

CodeBuilder

InlineBuilder

Avoid monolithic parser logic.

---

# Pipeline Rules

Each transformation belongs to a Pass.

Example

NormalizePass

DiagramPass

ReferencePass

FootnotePass

Every Pass returns

PassResult

Never return raw AST.

Pipeline execution must be deterministic.

Running the same input twice should produce identical output.

---

# Renderer Rules

Renderer uses NodeVisitor.

Do not implement accept() methods.

Use dynamic dispatch.

Renderer renders only.

Business logic belongs elsewhere.

---

# Render Context

CompilerContext

Stores

- configuration
- diagnostics
- pass registry

RenderContext

Stores

- current paragraph
- numbering
- style state
- rendering flags

Do not mix these responsibilities.

---

# Inline Rendering

Nested formatting must be managed through InlineState.

Avoid mutable global formatting state.

---

# Style System

Renderer must obtain formatting through StyleResolver.

Avoid hardcoding styles.

Themes control appearance.

Renderer controls structure.

---

# Word Font Rules

Always use

set_style_font()

Never use

style.font.name

directly for East Asian text.

Always update

ascii

hAnsi

eastAsia

cs

Failure to do so may cause Word to fall back to MS Mincho.

---

# Diagram Rules

Parser detects diagram blocks.

DiagramPass converts them into images.

Renderer renders images only.

Renderer must never generate SVG.

---

# Plugin Rules

Pipeline supports plugins.

Register through

PassRegistry

or

entry_points

Avoid modifying Pipeline directly.

---

# Diagnostics

All recoverable problems should generate Diagnostics.

Diagnostics include

- code
- severity
- message
- location
- suggestion

Avoid print().

Prefer structured diagnostics.

---

# Error Handling

Fail loudly.

Raise meaningful exceptions.

Avoid silent failures.

Never swallow exceptions.

Include actionable messages.

---

# Performance

Avoid unnecessary AST copies.

Prefer linear algorithms.

Large documents should remain supported.

Avoid quadratic behavior.

---

# Coding Standards

Python

3.10+

Formatting

black

isort

ruff

Typing

Required.

Public APIs require type hints.

Docstrings

Required.

Google style preferred.

Use pathlib instead of os.path.

Use logging instead of print.

---

# Testing

Framework

pytest

Required

Parser Tests

Pipeline Tests

Renderer Tests

Integration Tests

Golden Tests

Rendering changes must update Golden Tests.

Snapshots should remain deterministic.

Before running tests, ensure the project is installed in editable mode (pip install -e .) within the active .venv.

---

# Configuration

Configuration belongs in

config.yaml

Avoid hardcoded paths.

Avoid hardcoded themes.

Avoid hardcoded fonts.

---

# File Organization

Keep modules focused.

One responsibility per class.

Prefer composition over inheritance.

Avoid utility dumping.

---

# Adding New Syntax

The correct workflow is

Markdown

↓

Parser

↓

AST Node

↓

Pipeline Pass

↓

Renderer

↓

Tests

Never shortcut this process.

---

# Adding New Passes

Create a new TransformPass.

Return PassResult.

Register in PassRegistry.

Add tests.

Avoid modifying existing passes unless necessary.

---

# Adding New Themes

Implement Theme interface.

Register theme.

Avoid hardcoding formatting.

---

# Fixing Bugs

Fix root causes.

Avoid renderer hacks.

Avoid parser hacks.

Avoid special cases.

Preserve architecture.

---

# Never Do

Never bypass AST.

Never manipulate DOCX inside Parser.

Never render diagrams inside Renderer.

Never mutate AST.

Never parse Markdown inside Renderer.

Never store rendering state in AST.

Never introduce circular imports.

Never duplicate renderer logic.

Never ignore diagnostics.

Never silently ignore exceptions.

---

# Before Finishing Work

Confirm

✓ Code formatted

✓ Ruff clean

✓ Tests pass

✓ Golden Tests updated

✓ Type hints complete

✓ Public APIs documented

✓ No circular imports

✓ Architecture preserved

✓ Deterministic output preserved

---

# AI Agent Workflow

When receiving a task:

1. Understand the requested change.

2. Identify affected compiler stage.

3. Reuse existing abstractions.

4. Prefer extension over modification.

5. Preserve architecture.

6. Write tests.

7. Explain architectural impact if significant.

When uncertain,

prefer maintainability,

determinism,

and architectural consistency over clever implementations.

---
# Environment and Dependency Management

## Virtual Environment
- **Must** use the virtual environment located at the project root: `.venv`.
- **Must** ensure the environment is activated (`(.venv)` appears in the terminal prompt) before executing any `pip` commands.
- **Must not** install or modify dependencies in external paths such as `C:\TradingAgentsCN\vendors\python`.

## Dependency Declaration
- All project dependencies **must** be explicitly declared in `pyproject.toml` (or `requirements.txt` if `pyproject.toml` is not yet fully adopted).
- For development, use the editable installation: `pip install -e .[dev]`.
- The goal is to achieve a fully self-contained and reproducible environment.

## Testing and Optimization Workflow
- Before starting a major optimization, ensure the test suite can run successfully in the project's `.venv`.
- Environment issues (e.g., incorrect Python paths) should be resolved before code changes.
- After resolving the environment, run the test suite to establish a baseline.
- Only then proceed with code optimization or new features, ensuring all tests pass after each significant change.

---
# Project Philosophy

This repository is intended to evolve into a production-grade document compiler.

Every contribution should improve

- readability
- modularity
- determinism
- extensibility
- maintainability

without sacrificing the compiler architecture.
