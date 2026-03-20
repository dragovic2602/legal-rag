# Supabase MCP Setup — Lovsamlinger til RAG

Denne guide beskriver hvordan du opsaetter Supabase som vektordatabase for koeberbrev-skillen.

---

## Trin 1 — Opret Supabase-projekt

1. Gaa til https://supabase.com og log ind / opret konto
2. Klik "New project"
3. Giv projektet et navn, fx `jurateam-lov`
4. Noteer din **Project URL** og **anon/service_role API key** fra Project Settings > API

---

## Trin 2 — Aktiver pgvector og opret tabel

Aaben SQL Editor i Supabase og koel foelgende:

```sql
-- Aktiver vektorudvidelse
create extension if not exists vector;

-- Opret tabel til lovtekster
create table lovtekster (
  id bigserial primary key,
  lov_navn text not null,
  paragraf text,
  titel text,
  indhold text not null,
  embedding vector(1536)
);

-- Indeks for hurtig vektorsogning
create index on lovtekster using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
```

---

## Trin 3 — Upload lovtekster

Anbefalede lovtekster til at starte med:

| Lov | Kilde |
|-----|-------|
| Forbrugerbeskyttelsesloven ved erhvervelse af fast ejendom | retsinformation.dk |
| Bek. nr. 13 af 12. januar 2012 (ejerskifteforsikring) | retsinformation.dk |
| Tinglysningsloven | retsinformation.dk |
| ABF standardvilkaar for ejendomshandler | abf-rep.dk |
| Ejerlejlighedsloven | retsinformation.dk |
| Planloven (uddrag: lokalplaner) | retsinformation.dk |
| Jordforureningsloven (uddrag) | retsinformation.dk |

Upload-script (Python) ligger i `scripts/upload_lovtekster.py` — fyld dine API-nogler ind og koel det.

---

## Trin 4 — Konfigurer MCP i Cursor

Aaben eller opret filen `.cursor/mcp.json` i dit home directory:

```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp"
    }
  }
}
```

Genstart Cursor. Foerste gang vil en browser aabne til Supabase-login — godkend adgang.

---

## Trin 5 — Verificer forbindelsen

Bed Claude om at koere: "List tabeller i min Supabase-database via MCP"
Hvis `lovtekster`-tabellen vises, er forbindelsen aktiv.

---

## Soegeeksempel (til brug i skillen)

Naar lovtekster er uploadet, foresporg saadan via MCP:

> "Soeg i lovtekster-tabellen efter paragraffer relevante for ejerskifteforsikring ved ejendomshandel"

Claude vil bruge MCP til at udfoere en vektorsogning og returnere de mest relevante afsnit.
