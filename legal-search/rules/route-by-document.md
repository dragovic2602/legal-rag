# Rule: Route by Document

When you know (or can infer) which specific law a question is about, route the search to that document using `source_filter`. This dramatically improves result precision.

---

## Step-by-Step Routing

### Step 1: Get the document list
```python
list_documents()
```
Do this at the start of each session, or when you're about to route. The output gives you exact source filenames.

### Step 2: Match the question to a document
Look for:
- Law name mentioned explicitly ("lejeloven", "tinglysningsloven", "arveloven")
- Legal domain keywords that map to known laws (see routing hints below)
- § number references — look up which law contains that section

### Step 3: Search with filter
```python
search_knowledge_base(
    query="<your query>",
    source_filter="ExactFilename.pdf"  # from list_documents() output
)
```

### Step 4: Fallback if filtered search returns nothing
```python
# Remove filter, search all documents
search_knowledge_base("<your query>")
```

---

## Routing Hints

> **Note:** These are approximate mappings based on document names visible in the git status. Run `list_documents()` for exact filenames and to confirm availability.

| Question Domain | Likely Document(s) |
|----------------|-------------------|
| Husleje, depositum, opsigelse af lejemål | `Lov om leje.pdf` |
| Erhvervsleje, erhvervslejemål | `Erhvervslejelov.pdf` |
| Tinglysning, pant, servitutter, skøde | `Tinglysningsloven.pdf` |
| Tinglysningsafgift | `Tinglysningsafgiftsloven.pdf` |
| Andelsbolig, andelsforening, overdragelse af andel | `Andelsboligforeningsloven.pdf` |
| Ejerlejlighed, ejerforening | `Ejerlejlighedsloven.pdf` |
| Arv, testamente, legal arverækkefølge | `Arvelov.pdf` |
| Boafgift, arveafgift | `Boafgiftsloven.pdf` |
| Ægteskab, separation, skilsmisse | `Ægteskabsloven.pdf` |
| Bodeling, ægtefællers formue | `Ægtefællers økonomiske forhold.pdf` |
| Ægtefællers skiftebehandling | `Ægtefællesskifteloven.pdf` |
| Fremtidsfuldmagt | `Lov om fremtidsfuldmagter.pdf` / `Fremtidsfuldmagt.pdf` |
| Gældsbreve, lånevilkår | `Gældsbrevsloven.pdf` |
| Jordforurening, olietanke | `Jordforurening.pdf` / `Jordforureningsloven - olietank.pdf` |
| Planloven, lokalplaner | `Planloven.pdf` |
| Landbrugsejendom, landbrugspligt | `Landbrugsloven.pdf` |
| Miljøbeskyttelse | `Miljøbeskyttelsesloven.pdf` |
| Servitutter | Andersen_servitutter_og_lokalplaner_1984.pdf |
| Forvaltningsret, offentlig myndighed | `Forvaltningsloven.pdf` / `Offentlighedsloven.pdf` |
| Konkurs, insolvens | `Konkursloven.pdf` |
| Forbrugerbeskyttelse, køb | `Forbrugerbeskyttelse.pdf` |
| Rets­pleje, domstole, retssager | `Retsplejeloven.pdf` |
| Aftaler, kontraktret | `Aftaleloven.pdf` |
| Boligregulering | `HISTORISK boligreguleringslov.pdf` / `lov om boligforhold.pdf` |

---

## When NOT to Route to a Specific Document

- Comparative questions: "Hvad er forskellen på lejeloven og erhvervslejeloven?"
- Unclear domain: let broad search determine which law is relevant
- Cross-law questions: "Hvad sker der med lejemålet ved konkurs?" (touches both lejeloven og konkursloven)
- General overview questions: "Hvilke love dækker fast ejendom?"

In these cases, search without `source_filter` and let diversity reranking surface results from multiple laws.

---

## Phase 2 Update

After running `list_documents()` against live data, update the routing hints table above with exact filenames and remove any entries for laws not yet ingested.
