# Legal-RAG — Installation Guide for Claude

You are setting up the legal-rag system on a lawyer's computer. Follow every step in order. Do not skip steps. At the end, print a summary of what succeeded and what needs attention.

---

## IMPORTANT: What This Install Does NOT Set Up

- The ingestion pipeline (documents are already embedded in Supabase)
- The file watcher / watchdog service
- OneDrive sync

The lawyer uses a shared Supabase knowledge base managed by the developer. Do not run `indexing.pipeline`, `watch_service.py`, or `sync_service.py`.

---

## Step 1 — Detect Project Root

Read the absolute path of this file (`install/SETUP.md`) and derive the project root (one directory up). Every path below uses `PROJECT_ROOT` as a placeholder for that path.

Use a Bash command to confirm:

```bash
pwd
```

Store the result. All subsequent paths are relative to this root.

---

## Step 2 — Check Git Bash

The continuous learning hooks and several scripts require `bash`. On Windows, this comes from Git for Windows (Git Bash).

```bash
bash --version
```

If bash is not found:
- Note it in the final summary
- Tell the lawyer to download Git for Windows from https://git-scm.com/download/win and install with default options
- Without bash, the learning observer hooks will not fire

If bash is available, continue.

---

## Step 3 — Check Python 3.9+


```bash
python --version
```

If Python is not found or the version is below 3.9:

- Tell the lawyer to download Python 3.11+ from https://www.python.org/downloads/
- Make sure "Add Python to PATH" is checked during install
- Stop here and ask them to restart Claude Code after installing Python

If Python 3.9+ is available, continue.

---

## Step 4 — Install `uv` and Create the Virtual Environment

Check if `uv` is available:

```bash
uv --version
```

If missing, install it:

```bash
pip install uv
```

Create the virtual environment (from project root):

```bash
uv venv .venv
```

Install all Python dependencies from the lock file:

```bash
uv sync --link-mode=copy
```

> **Windows note:** Always use `--link-mode=copy`. Without it, uv will fail with a hardlink error when the project folder is on a different drive than the uv cache (e.g., Downloads vs AppData). This is expected on Windows — `--link-mode=copy` is the correct fix.

This installs everything listed in `pyproject.toml` and `uv.lock` — including Docling, PydanticAI, asyncpg, MCP, and all other dependencies.

> Note: Docling and Whisper download their AI models on first use (not during install). First-time startup takes ~30 seconds.

If `uv sync --link-mode=copy` still fails, try:

```bash
.venv/Scripts/python -m pip install -e .
```

---

## Step 5 — Check Node.js and npm

The Supabase MCP server requires Node.js:

```bash
node --version
npm --version
```

If Node.js is missing:

- Note it in the final summary as a warning
- Tell the lawyer to install Node.js from https://nodejs.org (LTS version)
- Do not block — continue with the remaining steps

---

## Step 6 — Create the `.env` File

Check if `.env` already has content:

```bash
cat .env
```

If it exists and has values (not empty), skip this step.

If it is empty or missing, use `AskUserQuestion` to collect the following from the lawyer (or the developer who is running this install):

- **OPENAI_API_KEY** — starts with `sk-` — required for all AI features
- **DATABASE_URL** — the Supabase PostgreSQL connection string provided by the developer (format: `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`)
- **LLM_CHOICE** — the OpenAI model to use (default: `gpt-4o-mini`)

Write the following to `.env`:

```
OPENAI_API_KEY=[value from above]
DATABASE_URL=[value from above]
LLM_CHOICE=[value from above, or gpt-4o-mini]
AGENT_NAME=Legal RAG
```

---

## Step 7 — Fix `.mcp.json` Paths

The `.mcp.json` file contains hardcoded paths from the developer's machine that must be updated to match this computer.

Read `.mcp.json`. Locate the `legal-rag` server block and update exactly these three values:

| Field | New Value |
| --- | --- |
| `mcpServers.legal-rag.command` | `PROJECT_ROOT\.venv\Scripts\python.exe` |
| `mcpServers.legal-rag.args[0]` | `PROJECT_ROOT\rag\mcp_server.py` |
| `mcpServers.legal-rag.env.PYTHONPATH` | `PROJECT_ROOT\rag` |

Use the actual absolute path you determined in Step 1 — not the placeholder text `PROJECT_ROOT`.

Leave the `supabase` server block completely untouched (it contains the correct access token and project reference).

Write the updated file back to `.mcp.json`.

---

## Step 8 — Copy Everything to `~/.claude/` (Global Setup)

This step makes all skills, context, and knowledge available in every project the lawyer works in — not just this folder. It is the most important step.

### 8a — Project Skills → Global

Copy the following folders from `PROJECT_ROOT/.claude/skills/` into `~/.claude/skills/`. If a folder already exists at the destination, overwrite it entirely.

```bash
cp -r .claude/skills/koberbrev ~/.claude/skills/
cp -r .claude/skills/legal-search ~/.claude/skills/
cp -r .claude/skills/skills-creator ~/.claude/skills/
```

These skills give Claude:
- `koberbrev` — full 7-phase workflow for generating Danish buyer's letters
- `legal-search` — enforces always-search-first discipline on legal questions
- `skills-creator` — framework for building new Claude skills

### 8b — Global Skills → Global

Copy the following folders from `PROJECT_ROOT/claude/global/skills/` into `~/.claude/skills/`:

```bash
cp -r claude/global/skills/continuous-learning-v2 ~/.claude/skills/
cp -r claude/global/skills/document-skills ~/.claude/skills/
cp -r claude/global/skills/mcp-server-pattern ~/.claude/skills/
cp -r claude/global/skills/new-skill ~/.claude/skills/
cp -r claude/global/skills/team-builder ~/.claude/skills/
cp -r claude/global/skills/visual-explainer ~/.claude/skills/
```

### 8c — Context Files → Global

Copy all context files from `PROJECT_ROOT/.claude/context/` into `~/.claude/context/`. These contain firm-specific knowledge (company profile, clients, legal context, tone of voice) and have been pre-filled by the developer.

```bash
mkdir -p ~/.claude/context
cp .claude/context/company-profile.md ~/.claude/context/
cp .claude/context/legal-context.md ~/.claude/context/
cp .claude/context/clients.md ~/.claude/context/
cp .claude/context/tone-of-voice.md ~/.claude/context/
```

---

## Step 9 — Merge `~/.claude/settings.json`

The project's `.claude/settings.json` contains permissions that allow Claude to run the koberbrev Word-filling script via WSL. These must be added to the global settings.

Read `PROJECT_ROOT/.claude/settings.json`. It contains:

```json
{
  "permissions": {
    "allow": [
      "Bash(wsl python3 *fill_document.py*)",
      "Bash(wsl python3 *)",
      "Bash(wsl pip install *)"
    ]
  }
}
```

Read `~/.claude/settings.json` if it exists.

- If it does not exist: copy the project settings file directly to `~/.claude/settings.json`
- If it exists: merge the three `allow` entries into the existing `permissions.allow` array without removing any existing entries. Write the merged result back to `~/.claude/settings.json`

---

## Step 10 — Set Up Continuous Learning Observer

The continuous-learning system observes every tool call Claude makes and learns patterns from your sessions over time. It requires hooks in the global settings and a small directory structure.

### 10a — Create the homunculus directory structure

```bash
mkdir -p ~/.claude/homunculus/instincts/personal
mkdir -p ~/.claude/homunculus/instincts/inherited
mkdir -p ~/.claude/homunculus/evolved/agents
mkdir -p ~/.claude/homunculus/evolved/skills
mkdir -p ~/.claude/homunculus/evolved/commands
mkdir -p ~/.claude/homunculus/projects
```

### 10b — Patch `observe.sh` to support VSCode

The default `observe.sh` only runs when Claude is opened from the terminal. Since this system is used via the VSCode extension (Claude Code runs inside VSCode), it must be patched.

Read `~/.claude/skills/continuous-learning-v2/hooks/observe.sh`. Find this block:

```bash
case "${CLAUDE_CODE_ENTRYPOINT:-cli}" in
  cli) ;;
  *) exit 0 ;;
esac
```

Replace it with:

```bash
# claude-vscode added: VSCode extension is also an interactive human session.
case "${CLAUDE_CODE_ENTRYPOINT:-cli}" in
  cli|claude-vscode) ;;
  *) exit 0 ;;
esac
```

### 10c — Add observation hooks to global settings

Read `~/.claude/settings.json`. Add the following `hooks` block alongside the existing `permissions` block (do not remove anything already there):

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "bash \"$HOME/.claude/skills/continuous-learning-v2/hooks/observe.sh\" pre",
          "timeout": 5
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "bash \"$HOME/.claude/skills/continuous-learning-v2/hooks/observe.sh\" post",
          "timeout": 5
        }
      ]
    }
  ]
}
```

Write the merged result back to `~/.claude/settings.json`.

### 10d — Windows: Set up automatic pattern extraction via Task Scheduler

The background observer (which turns raw observations into instincts) cannot run automatically on Windows due to a limitation in the Claude CLI. Instead, set up a Windows Scheduled Task to do it automatically.

Run the following in PowerShell (as the current user, not administrator):

```powershell
$action = New-ScheduledTaskAction `
  -Execute "python3" `
  -Argument "$env:USERPROFILE\.claude\skills\continuous-learning-v2\scripts\instinct-cli.py evolve" `
  -WorkingDirectory "$env:USERPROFILE\.claude"

$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date)

Register-ScheduledTask `
  -TaskName "ClaudeObserver" `
  -Action $action `
  -Trigger $trigger `
  -RunLevel Limited `
  -Force
```

This runs `instinct-cli.py evolve` every 30 minutes. It will silently skip when there are fewer than 20 observations — no harm done. The instincts it creates go into `~/.claude/homunculus/projects/<project-id>/instincts/`.

If PowerShell fails (e.g. execution policy blocked), note it in the summary as a warning. Observations are still captured; pattern extraction just won't be automatic.

> **Note:** If `flock` is not available in Git Bash (common on Windows), the lazy-start guard in `observe.sh` will silently skip — this is expected and does not affect observation capture.

---

## Step 11 — Add MCP Servers to Global Config (`~/.claude/mcp.json`)

Adding the MCP servers globally means the legal knowledge base is available in every Claude Code session — not only when the lawyer has this project open.

Read `PROJECT_ROOT/.mcp.json` (already corrected in Step 6).

Read `~/.claude/mcp.json` if it exists.

- If it does not exist: create `~/.claude/mcp.json` as a copy of `.mcp.json`
- If it exists: merge the `legal-rag` and `supabase` entries into the existing `mcpServers` object. Do not remove existing servers. Write the merged result back.

---

## Step 11 — Check WSL and Install `docxtpl`

The `koberbrev` skill fills Word document templates using a Python script that must run inside WSL (Windows Subsystem for Linux). Check if WSL is available:

```bash
wsl echo ok
```

If WSL is not available:

- Note it in the final summary
- Print: "WSL is not installed. The koberbrev Word-filling step will not work until WSL is enabled. To install: open PowerShell as administrator and run `wsl --install`, then restart."
- Continue — do not block remaining steps

If WSL is available, install the required Python package:

```bash
wsl pip install docxtpl
```

---

## Step 12 — Verify and Print Summary

Run the following checks:

**Check 1 — Virtual environment exists:**

```bash
ls .venv/Scripts/python.exe
```

**Check 2 — MCP package installed:**

```bash
PYTHONPATH=rag .venv/Scripts/python -c "import mcp; print('MCP OK')"
```

**Check 3 — RAG modules importable:**

```bash
PYTHONPATH=rag .venv/Scripts/python -c "from storage.db_utils import DatabasePool; print('DB module OK')"
```

**Check 4 — .env has content:**

```bash
cat .env
```

Then print a clean summary to the lawyer:

```
==========================================
  Legal-RAG — Installation Complete
==========================================

  ✓/✗  Python venv created (.venv/)
  ✓/✗  Dependencies installed (uv sync)
  ✓/✗  .env file created
  ✓/✗  .mcp.json paths updated
  ✓/✗  Skills copied to ~/.claude/skills/
  ✓/✗  Context copied to ~/.claude/context/
  ✓/✗  observe.sh patched for VSCode
  ✓/✗  Observation hooks added to ~/.claude/settings.json
  ✓/✗  ClaudeObserver scheduled task created (30 min)
  ✓/✗  Global MCP config updated (~/.claude/mcp.json)
  ✓/✗  WSL + docxtpl installed
  ⚠    Node.js missing  [if applicable]
  ⚠    WSL not available — koberbrev Word-filling will not work  [if applicable]
  ⚠    Task Scheduler blocked — observer will not run automatically  [if applicable]

Next steps:
  1. Restart Claude Code (or VSCode) so MCP servers and hooks load
  2. Open any project folder — the legal knowledge base and all
     skills are available automatically in every session
  3. Ask Claude: "list documents" to confirm the knowledge base
     is connected
  4. After your first session, ask Claude: "check learning status"
     to verify observations are being captured
==========================================
```

Replace each ✓/✗ with the actual result. List any warnings at the bottom.
