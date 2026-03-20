-- ============================================================
-- JURATEAM — Supabase lovtekster schema
-- Kør dette i SQL Editor i Supabase Dashboard
-- ============================================================

-- 1. Aktiver pgvector (til fremtidig vektorsøgning)
create extension if not exists vector;

-- 2. Aktiver fuld-tekst søgning (bruges til keyword-søgning nu)
-- (ingen extension nødvendig — PostgreSQL built-in)

-- 3. Opret tabel
create table if not exists lovtekster (
  id          bigserial primary key,
  lov_navn    text      not null,   -- fx "Forbrugerbeskyttelsesloven"
  paragraf    text,                 -- fx "§ 4, stk. 1"
  titel       text,                 -- fx "Tilstandsrapportens gyldighed"
  indhold     text      not null,   -- selve lovteksten
  noegleord   text[],               -- ["ejerskifteforsikring", "tilstandsrapport"]
  embedding   vector(1536),         -- til fremtidig vector search
  opdateret   timestamptz default now()
);

-- 4. Fuld-tekst søgeindeks (til keyword-søgning via REST API)
create index if not exists lovtekster_fts_idx
  on lovtekster
  using gin (to_tsvector('danish', indhold));

-- 5. Nøgleord-array indeks
create index if not exists lovtekster_noegleord_idx
  on lovtekster using gin (noegleord);

-- 6. (Fremtidig) Vector similarity indeks
-- create index if not exists lovtekster_embedding_idx
--   on lovtekster using ivfflat (embedding vector_cosine_ops)
--   with (lists = 100);

-- 7. RPC-funktion til nøgleordssøgning (bruges af Claude via MCP)
create or replace function soeg_lovtekster(soegerord text[])
returns table (
  lov_navn    text,
  paragraf    text,
  titel       text,
  indhold     text,
  noegleord   text[]
)
language sql
stable
as $$
  select lov_navn, paragraf, titel, indhold, noegleord
  from lovtekster
  where noegleord && soegerord   -- array overlap: mindst ét nøgleord matcher
  order by lov_navn, paragraf
  limit 20;
$$;

-- 8. Row Level Security (tillad læsning via anon key)
alter table lovtekster enable row level security;

create policy "Alle kan læse lovtekster"
  on lovtekster for select
  using (true);
