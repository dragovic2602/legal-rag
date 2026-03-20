---
name: word-template-converter
description: Omdanner et Word-dokument med inkonsistente placeholders (XXXXX, [X], {X}, (du/I) osv.) til en standardiseret skabelon med {{ PLACEHOLDER_NAVN }} format klar til brug med fill_document.py. Udloeses naar brugeren beder om at konvertere en skabelon.
---

# Word Template Converter

Du modtager et Word-dokument (.docx) med inkonsistente placeholders og omdanner dem til `{{ PLACEHOLDER_NAVN }}` format. Du rører **aldrig** noget andet end selve placeholders.

---

## Teknisk baggrund — docx er XML

En `.docx`-fil er et ZIP-arkiv. Tekstindholdet ligger i `word/document.xml`. Strukturen:

```xml
<w:p>                          ← afsnit (paragraph)
  <w:r>                        ← run (tekststykke med fælles formatering)
    <w:rPr>...</w:rPr>         ← formatering (fed, kursiv, skrifttype osv.)
    <w:t>KLIENTNAVN</w:t>      ← selve teksten
  </w:r>
</w:p>
```

**Kritisk: Split runs.** Word splitter tekst i separate runs uden varsel, selv uden formateringsændring. `KLIENTNAVN` kan fremstå som:

```xml
<w:r><w:t>KLIENT</w:t></w:r><w:r><w:t>NAVN</w:t></w:r>
```

Dette forhindrer simpel tekstsøgning. Du skal identificere split runs og sammenlægge dem ved erstatning.

---

## Trin 1 — Udpak docx

```bash
mkdir -p /tmp/template_conv
cp "<absolut_sti_til_dokument.docx>" /tmp/template_conv/document.docx
cd /tmp/template_conv && unzip -o document.docx -d extracted/ > /dev/null
echo "Udpakket OK"
```

---

## Trin 2 — Læs XML

Læs `extracted/word/document.xml` med Read-værktøjet. Fokus på al tekst inde i `<w:t>` elementer — det er den eneste del du må ændre.

---

## Trin 3 — Identificér placeholders (to-pass analyse)

### Pass 1 — Mønstergenkendelse

Gennemgå XML og find ALT der ser ud som en placeholder:

| Mønster | Eksempel | Handling |
|---------|----------|---------|
| X-sekvenser | `XXXXX`, `XXXX`, `XXX` | Brug kontekst → navngiv |
| Brackets | `[KLIENTNAVN]`, `[X]`, `[indsæt dato]` | Fjern brackets, brug tekst som navn |
| Curly (enkelt) | `{ADRESSE}`, `{X}` | Konvertér → `{{ ADRESSE }}` |
| ALL-CAPS ord | `KLIENTNAVN`, `ADRESSE`, `MAEGLER` | Brug direkte som navn |
| Alternativ form | `(du/I)`, `(din/jeres)`, `(dig/jer)` | Se pronomen-tabel nedenfor |
| Datoformat | `dd. månedsnavn åååå`, `DD-MM-ÅÅÅÅ` | → `{{ DATO }}` |
| Beløbsformat | `0.000.000 kr.`, `X.XXX.XXX kr.` | Brug kontekst → `{{ KOEBESUM }}` |
| Tal-placeholder | `00`, `0` som tydelig placeholder | Brug kontekst → fx `{{ DEPONERING_HVERDAGE }}` |

### Pass 2 — Kontekstbaseret navngivning for `XXXXX`

For X-sekvenser uden eksplicit navn: læs hele sætningen rundt om og brug kontekst:

- `"Kære XXXXX,"` → `{{ HILSEN_NAVN }}`
- `"Adresse: XXXXX"` → `{{ ADRESSE }}`
- `"kortlagt som XXXXX"` → `{{ JORDFORURENING_STATUS }}`
- `"kr. XXXXX"` + pengeafsnit → `{{ KOEBESUM }}` (eller relevant beløb)
- `"inden XXXXX hverdage"` → `{{ DEPONERING_HVERDAGE }}`
- `"udstedes den XXXXX"` → `{{ DATO }}`

### Pronomen-konvertering

| Original | Placeholder |
|----------|-------------|
| `(du/I)` | `{{ PRONOMEN }}` |
| `(Du/I)` | `{{ PRONOMEN_STOR }}` |
| `(dig/jer)` | `{{ PRONOMEN_OBJ }}` |
| `(din/jeres)` | `{{ PRONOMEN_GEN }}` |
| `(berettiget/berettigede)` | `{{ PRONOMEN_BERETTIGET }}` |
| `(forpligtet/forpligtede)` | `{{ PRONOMEN_FORPLIGTET }}` |

### Kendte placeholder-navne (brug disse frem for egne navne)

Fra koberbrev-workflowet — brug disse navne når kontekst matcher:

```
KLIENTNAVN, KLIENT_ADRESSE, KLIENT_EMAIL, ADRESSE, HILSEN_NAVN,
PRONOMEN, PRONOMEN_STOR, PRONOMEN_OBJ, PRONOMEN_GEN,
PRONOMEN_BERETTIGET, PRONOMEN_FORPLIGTET,
DATO, JOURNALNR, ADVOKATFORBEHOLD_DATO, ADVOKATFORBEHOLD_KL,
KOEBESUM, DEPONERING_KR, DEPONERING_HVERDAGE,
BANKGARANTI_KR, BANKGARANTI_HVERDAGE,
TINGBOG_DATO, ADKOMSTHAVER, SERVITUTTER_ANTAL, HAEFTELSER_ANTAL,
FORENINGSTYPE, TILBEHOER, MAEGLER_NAVN,
TILSTANDSRAPPORT_DATO, TILSTANDSRAPPORT_UDLOEB,
ELRAPPORT_DATO, ELRAPPORT_UDLOEB,
EJERSKIFTEFORSIKRING_SELSKAB, EJERSKIFTEFORSIKRING_DATO, EJERSKIFTEFORSIKRING_KR,
ENERGIMAERKE_DATO, ENERGIMAERKE_UDLOEB, ENERGIMAERKE,
EJENDOMSDATARAPPORT_DATO, JORDFORURENING_STATUS,
SERVITUT_ANALYSE, HAEFTELSER_ANALYSE, EJERFORENING_ANALYSE,
BBR_ANALYSE, LOKALPLAN_ANALYSE, TILSTAND_ANALYSE,
ELINSTALLATION_ANALYSE, VARMEFORBRUG_ANALYSE, JORDFORURENING_ANALYSE,
KONKLUSION_ANALYSE
```

Nye dokumenttyper kan have egne placeholders — navngiv dem beskrivende med STORE_BOGSTAVER.

---

## Trin 4 — Præsentér mapping til godkendelse

Vis denne tabel **FØR du ændrer noget som helst**:

```
| Original tekst      | Kontekst (forkortet sætning)             | Foreslået placeholder        | Split run? |
|---------------------|------------------------------------------|------------------------------|------------|
| XXXXX               | "Kære XXXXX,"                            | {{ HILSEN_NAVN }}            | Nej        |
| [ADRESSE]           | "Ejendommen beliggende [ADRESSE]"        | {{ ADRESSE }}                | Nej        |
| (du/I)              | "anbefaler vi (du/I) at tage stilling"   | {{ PRONOMEN }}               | Nej        |
| dd. månedsnavn åååå | "København, dd. månedsnavn åååå"         | {{ DATO }}                   | Nej        |
| KLIENT + NAVN       | "brev til KLIENTNAVN vedrørende"         | {{ KLIENTNAVN }}             | JA         |
```

Angiv altid om der er split run — det er vigtigt for advokaten at forstå hvad der sker.

Skriv: *"Er denne mapping korrekt? Du kan ændre navne inden vi fortsætter. Skal vi gå i gang?"*

**Vent på godkendelse inden du rører XML.**

---

## Trin 5 — Erstat i XML

Brug Edit-værktøjet på `extracted/word/document.xml`.

### Simpelt tilfælde — ét `<w:t>` element

Find den nøjagtige streng og erstat:

```xml
<!-- FØR -->
<w:t>XXXXX</w:t>

<!-- EFTER -->
<w:t>{{ HILSEN_NAVN }}</w:t>
```

Vigtigt: `{{ PLACEHOLDER }}` skrives **altid** med:
- Dobbelt curly braces
- Ét mellemrum inden for hvert bracket
- STORE BOGSTAVER med underscore

### Split run-tilfælde — placeholder spredt over flere runs

Find hele det splittede segment og erstat med ét run. Behold `<w:rPr>` (formatering) fra det **første** run:

```xml
<!-- FØR (to runs der tilsammen danner "KLIENTNAVN") -->
<w:r><w:rPr><w:b/></w:rPr><w:t>KLIENT</w:t></w:r><w:r><w:rPr><w:b/></w:rPr><w:t>NAVN</w:t></w:r>

<!-- EFTER (ét run med placeholder) -->
<w:r><w:rPr><w:b/></w:rPr><w:t>{{ KLIENTNAVN }}</w:t></w:r>
```

Hvis runs ikke har formatering (`<w:rPr>`):

```xml
<!-- FØR -->
<w:r><w:t>KLIENT</w:t></w:r><w:r><w:t>NAVN</w:t></w:r>

<!-- EFTER -->
<w:r><w:t>{{ KLIENTNAVN }}</w:t></w:r>
```

### Hvad du ALDRIG må røre

- `<w:pPr>` — afsnitsformatering
- `<w:sectPr>` — sidelayout
- `<w:styles>`, `<w:settings>`, andre XML-filer i arkivet
- Al løbende tekst der ikke er en placeholder
- Overskrifter, brødtekst, noter — intet

---

## Trin 6 — Pak docx igen

```bash
cd /tmp/template_conv/extracted
zip -r ../document_converted.docx . > /dev/null
# Kopiér til samme mappe som originalen
cp ../document_converted.docx "<original_mappe>/template_converted.docx"
echo "Gemt som template_converted.docx"
```

Gem **altid** som ny fil med suffix `_converted` — overskriv aldrig originalen.

---

## Trin 7 — Verificér

Læs `extracted/word/document.xml` igen. Tjek:

1. Alle `{{ placeholder }}` er korrekt formateret (dobbelt curly, mellemrum, STORE BOGSTAVER)
2. Intet andet indhold er ændret
3. Ingen tomme `<w:t/>` elementer efterladt fra split-run-sammenlægninger
4. Ingen `<w:t>` med kun whitespace

Præsentér:
- Samlet antal erstatninger
- Liste over eventuelle usikre navne der bør gennemses
- Sti til den færdige fil

---

## Regler — læs disse igen inden du starter

1. **Rør kun placeholders** — aldrig løbende tekst, overskrifter eller andet indhold, uanset hvad
2. **Bevar al formatering** — `<w:rPr>` og `<w:pPr>` ændres ikke, undtagen ved split-run-sammenlægning hvor det første runs formatering bevares
3. **Gem altid som ny fil** — suffix `_converted`, aldrig overskriv original
4. **Brug koberbrev-navne** når kontekst matcher — gør integration med `fill_document.py` problemfri
5. **Usikker kontekst** — hvis en `XXXXX` ikke kan navngives med sikkerhed, præsentér tre navnmuligheder til brugeren og vent på valg
6. **Godkend mapping FØR ændringer** — vis altid tabellen og vent på svar

---

## Fejlhåndtering

**Kan ikke unzippe:** Filen er ikke et gyldigt .docx. Bed brugeren gem filen igen fra Word som .docx.

**Placeholder ses i rendered tekst men ikke i XML:** Det er et split run. Søg på de første 3-4 bogstaver i `<w:t>` for at finde starten af sekvensen.

**Samme placeholder bruges med forskellig formatering på tværs af dokumentet:** Erstat hver forekomst individuelt — bevar den lokale formatering for hvert sted.

**XML er meget langt:** Word-dokumenter kan have meget XML. Læs i sektioner — søg på `XXXXX` eller det specifikke mønster med Grep for at finde de relevante linjer.
