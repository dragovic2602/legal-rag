# Rule: Cite Source and Section

Every legal statement derived from the knowledge base must be cited. No exceptions.

---

## Citation Format

### When the chunk contains a § number

```text
[Kilde: Tinglysningsloven.pdf, § 12]
[Kilde: Lov om leje.pdf, § 36, stk. 2]
```

### When the chunk does not show a § number

```text
[Kilde: Tinglysningsloven.pdf]
```

Optionally note: "(præcis paragraf ikke synlig i tekststykket)"

### When citing multiple sources in one answer

Cite each claim separately inline:

```text
Udlejer kan kræve depositum på op til 3 måneders husleje [Kilde: Lov om leje.pdf, § 34].
Depositum skal tilbagebetales senest 1 måned efter fraflytning [Kilde: Lov om leje.pdf, § 98].
```

---

## What to Include in the Citation

| Field | Required | Example |
| --- | --- | --- |
| Source filename | Always | `Lov om leje.pdf` |
| § number | If visible in chunk | `§ 36` |
| Stk. (subsection) | If visible | `stk. 2` |
| Nr. (item) | If visible | `nr. 3` |
| Document title | Optional (use filename instead) | — |

Use the **source filename** (from the `[Kilde: ...]` line in search results), not the document title, so the user can identify the exact file.

---

## Verbatim Quote Requirement

Before your legal analysis of any claim, include a **direct quote** from the retrieved chunk in a blockquote:

```text
> "Udlejer kan kræve depositum svarende til 3 måneders leje."

[Kilde: Lov om leje.pdf, § 34]

**Analyse:** Sælger kan således…
```

This is mandatory when:

- Stating what a law says or requires
- Citing a specific § or rule
- Making a claim with legal consequences for the client

If the chunk only partially covers the question, quote the most relevant sentence and note what is missing:

```text
> "Fortrydelsesretten kan gøres gældende inden 6 hverdage…"

[Kilde: Forbrugerbeskyttelse.pdf, § 11]

⚠️ Chunken dækker fristen men ikke betalingsvilkårene — søg videre.
```

Never paraphrase a legal rule without first quoting the source text directly.

---

## What You Must Never Do

- Cite a source you did not retrieve in this session
- Mix retrieved content with training knowledge without clearly distinguishing
- Say "ifølge dansk lovgivning" without a specific source citation
- Invent or estimate § numbers — if you can't see one, don't cite one

---

## When Chunks Show Heading Hierarchy

Docling chunks include heading context. If the chunk shows a heading like `## § 34 Depositum`, use that § number in the citation. If the heading shows a section title but no § number, use the section title in the citation:

```text
[Kilde: Lov om leje.pdf, afsnit "Fraflytning"]
```

---

## Chunks That Partially Answer the Question

If a chunk contains relevant background but doesn't directly answer the question, cite it with a qualifier:

```text
[Kilde: Andelsboligforeningsloven.pdf — omhandler beslutningsprocessen,
ikke direkte pris på andele]
```
