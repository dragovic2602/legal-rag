# Rule: Multi-Query Strategy

When the first search returns weak, irrelevant, or no results, use multiple query variants before concluding the topic isn't covered.

---

## When to Run Multiple Queries

**Triggers:**
- Search returns 0 results
- Results look topically adjacent but don't answer the question
- The question uses very specific terminology (§ numbers, named procedures)
- The question uses informal/conversational phrasing
- First query was in Danish — try English variants (and vice versa)

**Do not** run multiple queries if the first search already returned 4–5 clearly relevant chunks.

---

## How Many Variants

**2–3 variants maximum.** More than that is rarely useful and wastes time.

---

## How to Vary Queries

### 1. Rephrase: Informal → Formal
```
"kan udlejer smide lejeren ud" → "ophævelse af lejekontrakt"
"hvad sker der med huset ved skilsmisse" → "bodeling fast ejendom"
```

### 2. Synonyms
```
"depositum" → "sikkerhedsstillelse"
"opsigelse" → "ophævelse"  (note: different legal meanings — try both)
"ejer" → "udlejer" / "boligejer"
"pantsætning" → "pant" / "tinglysning af pant"
```

### 3. Broader → Narrower
```
Broad: "lejekontrakt regler"
Narrow: "lejekontrakt krav skriftlighed"
```

### 4. Danish → English (or reverse)
The full-text index uses English `tsvector`. For Danish documents, some terms may be indexed differently. Try:
```
"opsigelse" AND "termination of lease"
"tinglysning" AND "land registration"
```

### 5. § Number Variants
```
"§ 34 stk 2" → "paragraf 34" → the likely section title text
```

---

## How to Combine Results

- Take the **union** of all retrieved chunks
- Remove **duplicates** by chunk content (same text from same source = same chunk)
- Rank by relevance to the question (not by which query retrieved them)
- Cite the **source**, not which query found it

---

## Example

```python
# Question: "Kan man tinglyse et pant i en andelslejlighed?"

# Round 1 (poor results)
search_knowledge_base("pant andelslejlighed tinglysning")

# Round 2 (formal rephrasing)
search_knowledge_base("pantsætning andel andelsbolig sikkerhed")

# Round 3 (source-filtered)
search_knowledge_base("pant andel", source_filter="Andelsboligforeningsloven.pdf")

# Combine, deduplicate, answer with citations from all retrieved chunks
```

---

## RAG-Fusion Note

This is a lightweight version of RAG-Fusion. A full implementation would embed all queries, search in parallel, and fuse rankings via RRF. Our manual approach achieves similar coverage for a legal assistant use case without extra API calls.
