---
name: mcp-guide
description: Komplet oversigt over alle tilgængelige MCP-servere og deres tools. Dækker hvornår man bruger hvilken server, dynamiske kombinationer på tværs af MCPs, og optimale workflows. Brug ved alle opgaver der involverer ejendomsdata, juridiske spørgsmål eller webopslag.
type: reference
---

# MCP Guide — Niroai Agent

## Tilgængelige MCP-servere

| Navn | URL | Port | Hvad |
|------|-----|------|------|
| **ois** | `https://niroai.cloud/mcp-ois-niroai` | 8086 | OIS.dk — samlet ejendomsdata, BBR-PDF, vurdering, plandata |
| **bbr** | `https://niroai.cloud/mcp-bbr-niroai` | 8081 | BBR via Datafordeler GraphQL — struktureret bygningsdata |
| **matriklen** | `https://niroai.cloud/mcp-matriklen-niroai` | 8082 | Matriklen WFS — matrikelnr, ejerlav, areal, notering |
| **vurdering** | `https://niroai.cloud/mcp-vurdering-niroai` | 8084 | Datafordeler VUR — officielle ejendomsvurderinger |
| **browser** | `https://niroai.cloud/mcp-browser-niroai` | 8085 | Web-browser — åbne API'er, sider med JavaScript |
| **legal-rag** | stdio | 8080 | Juridisk vidensbase — love, domme, cirkulærer |

---

## Tools per server

### OIS (`mcp-ois-niroai`)
Kræver BFE-nummer. Dækker den bredeste mængde ejendomsdata i ét kald.

| Tool | Args | Returnerer |
|------|------|-----------|
| `ois_property_info(bfe)` | bfe: str | Adresse, ejer, vurdering, salg, ejendomsskat, BBR-oversigt, vurderingsmeddelelse-liste, plandata-adresser |
| `ois_vurderingsmeddelelse(bfe, year)` | bfe: str, year: int | PDF-tekst fra specifik vurderingsmeddelelse |
| `ois_bbr_meddelelse(bfe)` | bfe: str | PDF-tekst fra BBR-meddelelse (bygningsmaterialer, installationer, m²) |
| `ois_plandata(bfe, address_hint="")` | bfe: str | Plandata pr. adresse: lokalplaner, kommuneplanrammer, zonestatus |

### BBR (`mcp-bbr-niroai`)
Kalder Datafordeler BBR GraphQL API. Returnerer struktureret JSON-data (ikke PDF).
Kræver DATAFORDELER_API_KEY.

| Tool | Args | Returnerer |
|------|------|-----------|
| `get_bbr_by_address(adresse)` | adresse: str | Byggeår, areal, etager, varme, opvarmning, BBR-status |
| `get_bbr_by_bfe(bfe_nummer)` | bfe_nummer: str | Samme — via BFE direkte |

### Matriklen (`mcp-matriklen-niroai`)
Kalder Datafordeler Matriklen WFS. Returnerer matrikeldata inkl. særlige noteringer.
Kræver DATAFORDELER_API_KEY.

| Tool | Args | Returnerer |
|------|------|-----------|
| `get_matrikel_by_address(adresse)` | adresse: str | Matrikelnr, ejerlav, areal, notering, fredskov, strandbeskyttelse |
| `get_matrikel_by_id(ejerlavskode, matrikelnr)` | ejerlavskode: str, matrikelnr: str | Samme — via direkte ID |

### Vurdering (`mcp-vurdering-niroai`)
Kalder Datafordeler VUR GraphQL API. Officielle Skatteforvaltningens vurderinger.
Kræver DATAFORDELER_API_KEY.

| Tool | Args | Returnerer |
|------|------|-----------|
| `get_vurdering_by_address(adresse)` | adresse: str | Ejendomsværdi, grundværdi, vurderingsår (seneste 3) |
| `get_vurdering_by_bfe(bfe_nummer)` | bfe_nummer: str | Samme — via BFE direkte |

### Browser (`mcp-browser-niroai`)
Til åbne web-API'er og sider der kræver JavaScript-rendering.

| Tool | Args | Returnerer |
|------|------|-----------|
| `browse_url(url, wait_for="", wait_ms=0)` | url: str | Markdown-tekst fra siden |
| `extract_links(url, wait_for="", wait_ms=0)` | url: str | Links fra siden |
| `click_and_read(url, steps, wait_ms=2000)` | url, steps: list[dict] | Tekst efter interaktioner |
| `search_and_read(url, selector, query, ...)` | url, søgefelt, søgetekst | Tekst efter søgning |

### Legal RAG (`legal-rag`)
Juridisk vidensbase med love og retskilder.

| Tool | Args | Returnerer |
|------|------|-----------|
| `search_knowledge_base(query, source_filter="")` | query: str | Relevante juridiske chunks med kilde |
| `list_documents()` | — | Liste over alle dokumenter i vidensbasen |

---

## Adresse → BFE (nødvendig til OIS)

OIS-tools kræver BFE-nummer. Tre måder at få det:

**Metode 1 — BBR MCP (anbefalet, ét kald):**
```
get_bbr_by_address("Gammel Vartov Vej 1, Hellerup")
→ Find BFEnummer i svaret
→ ois_property_info(bfe)
```

**Metode 2 — Dataforsyningen via browser (to kald, ingen API-nøgle):**
```
browse_url("https://api.dataforsyningen.dk/adgangsadresser?q={adresse}&per_side=1")
→ udtræk matrikelnr + ejerlav.kode
browse_url("https://api.dataforsyningen.dk/jordstykker/{ejerlavskode}/{matrikelnr}")
→ udtræk bfenummer
→ ois_property_info(bfe)
```

**Metode 3 — Matriklen MCP (hvis du har brug for matrikeldata alligevel):**
```
get_matrikel_by_address("Gammel Vartov Vej 1, Hellerup")
→ udtræk ejerlav_kode + matrikelnr
→ browse_url Dataforsyningen jordstykker → BFE
→ ois_property_info(bfe)
```

---

## Beslutningsguide — hvornår bruges hvad?

```
Spørgsmål om ejendom:
├─ Har du BFE?
│   ├─ Ja → ois_property_info(bfe)              [starter altid her]
│   └─ Nej → get_bbr_by_address(adresse) for BFE, derefter ois_property_info
│
├─ Vurderingsmeddelelse (PDF)?
│   → ois_property_info(bfe) for at se tilgængelige år
│   → ois_vurderingsmeddelelse(bfe, year)
│
├─ BBR-detaljer (materialer, installationer)?
│   ├─ Strukturerede data → get_bbr_by_bfe(bfe)   [BBR MCP]
│   └─ Fuld PDF-tekst → ois_bbr_meddelelse(bfe)   [OIS MCP]
│
├─ Matrikelforhold (notering, fredskov, strandbeskyttelse)?
│   → get_matrikel_by_address(adresse)
│
├─ Lokalplan / zonestatus / kommuneplan?
│   → ois_plandata(bfe)
│
├─ Ejendomsskat / grundskyld?
│   → ois_property_info(bfe)  [ejendomsskatEE-feltet]
│
└─ Juridisk spørgsmål (lejeloven, ABF, tinglysning...)?
    → list_documents() for at se hvad der er i vidensbasen
    → search_knowledge_base(query)
```

---

## Overlap og valg mellem MCPs

Visse data kan hentes fra flere sources. Her er forskellen:

| Data | OIS MCP | Datafordeler MCPs (BBR/VUR/Mat) |
|------|---------|--------------------------------|
| **BBR** | PDF-tekst via `ois_bbr_meddelelse` | Struktureret JSON via `get_bbr_by_bfe` |
| **Vurdering** | Fuld historik + korrekte datoer via `ois_property_info` | Seneste 3 år via `get_vurdering_by_bfe` |
| **Adresse→BFE** | Ikke indbygget | Indbygget i `get_bbr_by_address` |

**Tommelfingerregel:**
- OIS MCP er det **bredeste** valg — dækker det meste i ét kald
- BBR/Matriklen/Vurdering MCP bruges når du har brug for **strukturerede data** (ikke PDF) eller specifikke registeroplysninger fra Datafordeler
- Legal RAG bruges **udelukkende** til juridiske retskilder

---

## Typiske workflows

### "Hvad kan du fortælle mig om [adresse]?"
```
1. get_bbr_by_address(adresse)  → BFE + grundlæggende BBR
2. ois_property_info(bfe)       → fuld overblik
```

### "Hent vurderingsmeddelelsen fra 2012"
```
1. get_bbr_by_address(adresse)      → BFE
2. ois_property_info(bfe)           → bekræft at 2012 er tilgængeligt + korrekt dato
3. ois_vurderingsmeddelelse(bfe, 2012)  → PDF-tekst
```

### "Er der strandbeskyttelse / fredskov / særlig notering?"
```
1. get_matrikel_by_address(adresse)  → notering + restriktioner
```

### "Hvad er lokalplanen for ejendommen?"
```
1. get_bbr_by_address(adresse)  → BFE
2. ois_plandata(bfe)            → lokalplaner + kommuneplanrammer
```

### "Hvad siger lejeloven om depositum?"
```
1. list_documents()                         → se om lejeloven er i vidensbasen
2. search_knowledge_base("depositum lejeloven")
```

---

## Opdateringslog

| Dato | Ændring |
|------|---------|
| 2026-03-20 | OIS MCP tilføjet (port 8086) |
| 2026-03-20 | Skill oprettet med alle 6 MCPs |
