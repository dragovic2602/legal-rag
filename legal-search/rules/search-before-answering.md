# Rule: Search Before Answering

## Trigger — What Counts as a Legal Question

**Always search first** when the user asks about:
- The content of a Danish law or legal act (what does § X say...)
- Rights and obligations of parties (lejer, udlejer, arving, ægtefælle, køber, sælger...)
- Legal procedures (how to file, how to contest, time limits, deadlines...)
- Whether something is legal/permitted/required
- Specific legal terms or concepts in a Danish context
- Case outcomes or precedents
- Contractual requirements or formalities

**Examples that require search:**
- "Hvad siger lejeloven om depositum?"
- "Kan udlejer opsige lejekontrakten uden grund?"
- "Hvad er fristen for tinglysning af et pant?"
- "Er det lovligt at kræve mere end 3 måneders depositum?"

## What Does NOT Require a Search

- System/meta questions: "Which laws do you have?", "How do I add a document?"
- Ingestion commands: "How do I re-index the documents?"
- Requests for general explanation of what a term means (not a legal opinion)
- Follow-up clarifications on chunks you already retrieved
- Conversation logistics: "Summarise the last answer", "What did we discuss?"

## Search Strategy

### Step 1: Call `list_documents()` if needed
If you haven't already this session, call it first to see what's available.

### Step 2: Search
```
search_knowledge_base(query, source_filter=<law if known>)
```

### Step 3: If Results Are Weak or Empty
- Try a rephrased query (see `rules/multi-query-strategy.md`)
- Try removing `source_filter` if you used one
- Try Danish synonyms for key terms
- Try broader/narrower formulation

### Step 4: If Still Nothing
Report: "Jeg kan ikke finde information om dette i vidensdatabasen. Emnet er muligvis ikke dækket af de indlæste dokumenter."

**Never fill the gap with general legal knowledge or training data.**

## CRAG Pattern (Corrective RAG)

If retrieved chunks seem irrelevant to the actual question:
1. Do not use them — acknowledge they don't match
2. Rephrase and search again
3. If still no match → say not found

Retrieved chunks that are topically adjacent but not directly answering the question are still useful for context — say so explicitly ("the knowledge base covers X but not Y specifically").
