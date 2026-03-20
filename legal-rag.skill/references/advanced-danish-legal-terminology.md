# Advanced Danish Legal Terminology

> **STATUS: Phase 2 placeholder — not yet populated.**
>
> This file requires running `list_documents()` and `search_knowledge_base()` against live production data, plus legal domain review. Populate after the MCP server is confirmed working with a full document set.

---

## Purpose

A vocabulary map of Danish legal terms and their synonyms, abbreviations, and related concepts. Helps sub-agents generate better multi-query variants when the initial search returns weak results.

---

## Structure (to be populated in Phase 2)

### Synonym Clusters

```
Term → Synonyms / Related terms
----------------------------------
[POPULATE FROM LIVE SEARCHES]

Example pattern:
depositum → sikkerhedsstillelse, forudbetaling, kaution, garanti
opsigelse → ophævelse, fraflytning (NOTE: different legal meanings — check context)
udlejer → ejer, boligejer, boligudlejer, landlord
lejer → beboer, lejeboer, tenant
```

### Law Name Mappings

```
Common name → Filename in knowledge base
------------------------------------------
[POPULATE FROM list_documents() OUTPUT]

Example pattern:
lejeloven → Lov om leje.pdf
tinglysningsloven → Tinglysningsloven.pdf
andelsboligloven → Andelsboligforeningsloven.pdf
```

### Danish § Citation Format

Standard format: `§ 12` or `§ 12, stk. 2` or `§ 12, stk. 2, nr. 3`

In search queries, try both:
- `§ 12 stk 2` (without comma and period)
- `paragraf 12` (written out)
- The section heading text that likely surrounds that § number

### Common Question Patterns → Relevant Laws

```
[POPULATE BASED ON ACTUAL DOCUMENT CONTENT]

Pattern → Likely source law(s)
--------------------------------
tinglysning / pant / servitut → Tinglysningsloven
leje / husleje / opsigelse / lejer → Lov om leje
andelsbolig / andel / overdragelse → Andelsboligforeningsloven
ejerlejlighed / ejerforening → Ejerlejlighedsloven
erhvervsleje / erhvervslejekontrakt → Erhvervslejelov
arv / testamente / skiftebehandling → Arvelov, Boafgiftsloven
ægteskab / bodeling / separation → Ægteskabsloven, Ægtefællers økonomiske forhold
jordsforurening / olietank → Jordforurening, Jordforureningsloven - olietank
planlægning / lokalplan → Planloven
```

---

## How to Populate This File (Phase 2 Instructions)

1. Run `list_documents()` → copy all `→ filename.pdf` values into the Law Name Mappings section
2. For each major law, run 3–5 representative searches to identify common term clusters
3. Note where Danish informal terms differ from formal legal terms
4. Add any domain-specific terminology the lawyer uses frequently
5. Update `GENERATION.md` with the date and git SHA of the update
