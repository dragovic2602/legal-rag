# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository has two layers:

1. **Jurateam/** — A meta-project for creating Claude Code skills for a Danish real estate law firm. Primary output is new skill folders.
2. **Case folders** (e.g. `Fadet 5, 4. tv., 1799 København V/`) — Active real estate matters with PDF source documents. These are the input for the `/koeberbrev` workflow. PDFs are organized in `GG/` (legal documents) and `REFU/` (financial documents) subdirectories. See `DEMO - Vesterbrogade 42/` for a completed reference example.

Installed skills live in `~/.claude/Skills/`. The `Jurateam/Skills/` directory is the development source from which skills are deployed there.

---

## Key Commands

**Scaffold a new skill:**
```bash
python Jurateam/Skills/Skills-Creator/init_skill.py <skill-name> --path <output-directory>
```

**Validate a skill:**
```bash
python Jurateam/Skills/Skills-Creator/quick_validate.py <path/to/skill-folder>
```

**Package a skill for distribution** (runs validation automatically):
```bash
python Jurateam/Skills/Skills-Creator/package_skill.py <path/to/skill-folder> [output-directory]
```

**Fill a Word template** (Python kører via WSL — ikke Windows-native):
```bash
# Konvertér Windows-stier: C:\Users\... → /mnt/c/Users/...
# MSYS_NO_PATHCONV=1 er påkrævet — slår Git Bash path conversion fra
# Erstat <USERNAME> med det aktuelle Windows-brugernavn
MSYS_NO_PATHCONV=1 wsl python3 "/mnt/c/Users/<USERNAME>/.claude/skills/koberbrev/scripts/fill_document.py" \
  "<WSL-sti til docx i sagsmappen>" \
  "<WSL-sti til values.json>"
```

---

## Architecture

### Skills System

Every skill is a folder containing:
- `SKILL.md` (required) — YAML frontmatter (`name`, `description`) + imperative markdown instructions
- `scripts/` — executable code Claude runs directly
- `references/` — docs loaded into context as needed
- `assets/` — templates/files used in output, not loaded into context

The `description` field in frontmatter determines when Claude auto-triggers the skill. Write it in third person with explicit WHEN conditions.

### The `/new-skill` Workflow

Defined in `Jurateam/Skills/Skills-Creator/Process of creating new skill.md`. Six steps:
1. Gather requirements via 8 structured questions
2. Analyse and clarify — map workflow steps, flag assumptions, check public-apis if integration needed
3. Repeat step 2 until zero assumptions remain
4. Visual approval via `visual-explainer` skill (saves diagrams to `~/.agent/diagrams/`)
5. Build — write `plan.md`, produce user to-do table, scaffold with `init_skill.py`
6. Test until output is correct, get approval, make small conversational fixes

**Critical rule:** Never make assumptions. If anything is unclear at step 2, ask before proceeding.

### The `/koeberbrev` Workflow

A 9-phase document-filling workflow for Danish real estate buyer's letters. The installed skill is at `~/.claude/Skills/koberbrev/`.

**Core pattern — values.json:** Claude creates a `values.json` in the case folder at the start. Every placeholder value is written to this file immediately when found. It serves as a live progress tracker — empty strings mean work remaining.

**Two-loop structure:**
- **FASE 6** — GENERAL placeholders: factual values extracted directly from source documents (dates, amounts, names). No deliberation — find it, write it, move on.
- **FASE 7** — `_ANALYSE` placeholders: legal judgment required. Each is handled one at a time using a 5-step loop (identify → look up reference notes → read laws + documents → write prose → insert and continue).

**FLAG system:** Significant economic risks or document inconsistencies are marked FLAG — but only written into `{{ KONKLUSION_ANALYSE }}`, never in individual analysis sections.

**Online lookups** are restricted to the whitelist in `references/approved-sites.md` (planinfo.dk, virk.dk, municipal sites, etc.). No free web search.

**Legal texts** are fetched from a Supabase vector database via MCP before writing analysis sections (FASE 5).

**Template filling** uses `docxtpl` (Jinja2) which preserves all Word formatting. Tags in the `.docx` follow `{{ PLACEHOLDER }}` syntax.

**Pronoun handling:** The template comes in two versions (Du/I). Pronoun placeholders (`{{ PRONOMEN }}`, `{{ PRONOMEN_STOR }}`, etc.) are set in FASE 1 based on number of buyers.

---

## Jurateam Context Files

`Jurateam/context/` contains firm-specific templates that should be filled in once and loaded as context:
- `company-profile.md` — firm identity, services, structure
- `clients.md` — client types and relationship rules
- `legal-context.md` — jurisdiction, practice areas, disclaimers
- `tone-of-voice.md` — communication style and forbidden phrases

These inform all legal output but are currently empty placeholders awaiting completion.

---

## Bug Fixing

When a bug is reported, write a test that reproduces the bug first, then use subagents to fix it and verify the test passes.

---

## External References

- Public APIs catalogue: https://github.com/public-apis/public-apis — consult during `/new-skill` STEP 2 when an integration is needed
- Installed `visual-explainer` skill: `~/.claude/skills/visual-explainer/`
