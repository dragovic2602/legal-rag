---
name: legal-search
description: Enforces always-search-first and citation discipline for all legal queries. Use when answering questions about Danish law, property transactions, or any legal matter.
---

# Legal Search — How Claude Should Behave

## Core Principle

**Search before you speak.** Never answer a legal question from general knowledge. This is a knowledge base for a lawyer — legal accuracy matters. If it's not in the retrieved chunks, say so.

---

## MCP Tools

Two tools are available via the `legal-rag` MCP server:

### `list_documents()`

Returns all documents in the knowledge base with their filenames. **Call this at the start of every session** to see what laws are available and get exact filenames for `source_filter`.

### `search_knowledge_base(query, limit, source_filter)`

Hybrid vector + full-text search over all ingested law documents.

- `query` — natural language query in Danish or English
- `limit` — number of results (1–10, default 5)
- `source_filter` — restrict to one document, e.g. `"Tinglysningsloven.pdf"`

Returns ranked chunks with neighboring context chunks (±1) automatically included.

---

## The Workflow

```text
1. list_documents()
   → See what laws are in the knowledge base
   → Get exact filenames for source_filter

2. search_knowledge_base(query, source_filter="ExactLaw.pdf")
   → Run 2-3 searches with different phrasings if needed
   → Cite every claim from the retrieved chunks
```

---

## Citation Format

Every legal statement must be cited. First quote the source verbatim, then analyse:

```text
> "Depositum kan højst udgøre 3 måneders leje."

[Kilde: Lov om leje.pdf, § 34]

**Analyse:** Det betyder at sælger...
```

Short citation format when no verbatim quote is needed:

```text
[Kilde: Tinglysningsloven.pdf, § 12]
[Kilde: Lov om leje.pdf]   ← when § not visible in chunk
```

Never assert a legal rule without a `[Kilde: ...]` citation from a retrieved chunk.

---

## When to Say "I Don't Know"

Say "det fremgår ikke af vidensdatabasen" when:

- Multiple rephrasings return no results
- You searched the specific law and found nothing relevant
- The question is about a law not in the knowledge base

Do NOT make up legal content. Do NOT cite general knowledge.

---

## What Does NOT Need a Search

- Meta questions: "Which documents do you have?", "How do I add a document?"
- Clarifying a legal term at a general level (not a legal opinion)
- Conversation logistics: "Can you summarise what we discussed?"

For everything else involving Danish law → search first.

---

## Rule Files

| File | Rule |
| --- | --- |
| `rules/search-before-answering.md` | When and how to search |
| `rules/cite-source-and-section.md` | Full citation format with verbatim quote requirement |
| `rules/multi-query-strategy.md` | When to run multiple queries |
| `rules/route-by-document.md` | How to identify which law to search in |
