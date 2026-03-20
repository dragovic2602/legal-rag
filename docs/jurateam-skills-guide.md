# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository is a **Workflow Creator** — a meta-project for building Claude Code skills. The primary output is new skill folders that extend Claude's capabilities for specific workflows.

## Project Structure

```
Workflow Creator/
└── Skills-Creator/
    ├── SKILL.md                          # The skill-creator skill (loaded by Claude Code)
    ├── Process of creating new skill.md  # User-defined process: the /new-skill workflow
    ├── init_skill.py                     # Scaffold a new skill directory
    ├── package_skill.py                  # Validate + zip a skill for distribution
    └── quick_validate.py                 # Validate SKILL.md frontmatter and structure
```

## Key Scripts

**Scaffold a new skill:**
```bash
python Skills-Creator/init_skill.py <skill-name> --path <output-directory>
```

**Validate a skill:**
```bash
python Skills-Creator/quick_validate.py <path/to/skill-folder>
```

**Package a skill for distribution:**
```bash
python Skills-Creator/package_skill.py <path/to/skill-folder> [output-directory]
# Runs validation automatically before packaging
```

## The /new-skill Workflow

When a user runs `/new-skill`, follow the process defined in `Skills-Creator/Process of creating new skill.md` exactly. The steps are:

1. **STEP 1 — Gather requirements** via 8 structured questions (purpose, trigger/command, procedure, final product examples, background knowledge, forbidden words/phrases, output format, human approval points)
2. **STEP 2 — Analyse and clarify** — review the user's tech stack, identify missing documents, map all workflow steps, flag any assumptions and resolve them with the user
3. **STEP 3 — Repeat STEP 2** until zero assumptions remain
4. **STEP 4 — Visual approval** — use the `visual-explainer` skill to present the workflow diagram with Approve / Revise options; if Revise, loop back to STEP 2
5. **STEP 5 — Build** — write a `plan.md` for yourself; if the user has actions, produce a to-do table for them; then build the skill using `init_skill.py`
6. **STEP 6 — Test and ship** — test until output is correct, get user approval on output, make small conversational fixes, done

**Critical rule:** Never make assumptions. If anything is unclear at STEP 2, do not proceed to STEP 3 — ask first.

## Skill Anatomy

Every skill is a folder containing:
- `SKILL.md` (required) — YAML frontmatter (`name`, `description`) + imperative markdown instructions
- `scripts/` — executable code run directly or by Claude
- `references/` — docs loaded into context as needed
- `assets/` — templates/files used in output, not loaded into context

`description` in frontmatter determines when Claude auto-triggers the skill. Write it in third person and include explicit WHEN conditions.

## Bug Fixing

When a bug is reported, do not attempt to fix it immediately. First write a test that reproduces the bug, then use subagents to fix it and prove the fix with a passing test.

## API & Connector Reference

When a workflow requires external data, integrations, or API connections, consult the public-apis directory first before agreeing on an approach with the user:

**https://github.com/public-apis/public-apis**

This is a large curated list of free public APIs across categories (finance, weather, government, open data, etc.). During STEP 2 of `/new-skill`, if an integration is needed, check this list, propose relevant options to the user, and agree on the right one before building.

## Installed Skills

The `visual-explainer` skill (`~/.claude/skills/visual-explainer/`) is available and used in STEP 4 to render workflow diagrams as self-contained HTML files opened in the browser. Diagrams are saved to `~/.agent/diagrams/`.
