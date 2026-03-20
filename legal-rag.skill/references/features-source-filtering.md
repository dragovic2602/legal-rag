# Feature: Source Filtering

Source filtering lets you restrict a search to a single specific law document instead of searching across all ingested content.

---

## How It Works

The `source_filter` parameter in `search_knowledge_base()` is applied **after** the SQL search, in Python:

```python
if source_filter:
    reranked = [
        (r, s) for r, s in reranked
        if source_filter.lower() in r.get("source", "").lower()
    ]
```

- **Case-insensitive** partial match against `documents.source`
- The `source` field is the relative file path from the `documents/` folder: e.g. `Tinglysningsloven.pdf`
- Partial matches work: `"leje"` matches `"Lov om leje.pdf"`, `"tinglysning"` matches `"Tinglysningsloven.pdf"`

---

## Getting the Exact Filename

**Always call `list_documents()` first** to see exact source filenames. Do not guess filenames.

```
list_documents()
→ Returns: "42 documents in knowledge base:\n- Tinglysningsloven  →  Tinglysningsloven.pdf\n..."
```

Use the value after `→` as your `source_filter`.

---

## When to Use Source Filtering

**Use `source_filter` when:**
- The question is clearly about one specific law ("hvad siger lejeloven om...")
- The user refers to a specific act by name
- You got weak results from a global search and suspect one law is the right source
- You want to avoid irrelevant results from other laws contaminating the answer

**Do NOT use `source_filter` when:**
- The question is comparative ("hvad er forskellen mellem lejeloven og erhvervslejeloven...")
- You're unsure which law applies
- The question is about general legal principles that span multiple acts
- A filtered search returned nothing — retry without filter before giving up

---

## Fallback Pattern

```
1. Call list_documents() → identify relevant law → note source filename
2. search_knowledge_base(query, source_filter="ExactFilename.pdf")
3. If no results → search_knowledge_base(query)  # remove filter, search all
4. If still no results → try rephrased query
5. If still nothing → report: "not found in knowledge base"
```

---

## Example

```python
# User asks: "Hvad er reglerne for opsigelse i lejeloven?"

# Step 1: Get documents
list_documents()
# → "Lov om leje  →  Lov om leje.pdf"

# Step 2: Filtered search
search_knowledge_base(
    query="opsigelse lejer udlejer",
    limit=8,
    source_filter="Lov om leje.pdf"
)

# Step 3 (if empty): Fallback
search_knowledge_base("opsigelse lejer udlejer", limit=8)
```
