---
name: mcp-builder-information-site-noapi
description: Step-by-step metodologi til at bygge en dedikeret MCP-server til et informationssite uden offentlig API. Dækker den fulde kortlaegningsproces (Playwright network interception, klik gennem alle undersider, PDF-haandtering, dynamiske URL-parametre) inden MCP designes. Brug naar du skal bygge en ny informations-MCP svarende til OIS MCP.
---

# MCP Builder — Informationssite uden API

Denne skill beskriver den eksakte fremgangsmaade brugt til at bygge OIS MCP (port 8086) og skal bruges enhver gang vi skal bygge en ny MCP til et site der:
- Returnerer en tom HTML-skal til browser-MCP (React SPA / JavaScript-rendered)
- Ikke har en dokumenteret offentlig API
- Har undersider, PDF-dokumenter eller dynamiske URL-parametre

**Kritisk regel:** MCP'en designes ALDRIG foer kortlaegningen er 100% faerdig. Antagelser i MCP-kode er fejl.

---

## Fase 1 — Forstaa sitet manuelt (foer kode)

Naviger selv rundt paa sitet og noter:

1. **Hvad er sitetets primære indgangsparametre?** (BFE-nummer, adresse, CVR, matrikelnr...)
2. **Hvilke undersider/sektioner findes?** Klik alt igennem — trae-strukturer, faner, accordions
3. **Er der PDF-dokumenter?** Notér om de hentes via klik, direkte URL eller dynamisk genereret
4. **Er der elementer der kun vises naar man klikker?** (lazy-loaded data, MUI TreeItem, modal dialogs)
5. **Koerer sitet i React/SPA?** Tjek om browser-MCP returnerer tom HTML-skal

---

## Fase 2 — Playwright Network Interception (KRITISK TRIN)

Dette trin finder de skjulte JSON API-kald sitet bruger internt. Disse API'er er hvad MCP'en skal kalde direkte.

### Opsaet kortlaegningsscript

Skriv et Python-script lokalt og upload til VPS via SFTP (undgaa heredoc med f-strings — parsingfejl):

```python
# map_site.py — upload til VPS, kør der
import asyncio
from playwright.async_api import async_playwright

SITE_URL = "https://www.example.dk/page/PARAM"
OUTPUT = []

async def intercept(route, request):
    OUTPUT.append(f"REQ: {request.method} {request.url}")
    await route.continue_()

async def map_page(page, url, label):
    print(f"\n=== {label} ===")
    await page.route("**/*", intercept)
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(4000)

    # Udskriv alle interceptede requests
    for line in OUTPUT[-30:]:  # seneste 30
        print(line)
    OUTPUT.clear()

    # Udskriv page text (bevis paa at data er loadet)
    text = await page.evaluate("document.body.innerText")
    print(f"PAGE TEXT (500 chars): {text[:500]}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await ctx.new_page()

        # Kortlaeg HVER sektion separat
        await map_page(page, f"{SITE_URL}/section1", "SECTION 1")
        await map_page(page, f"{SITE_URL}/section2", "SECTION 2")
        # ... alle undersider

        await browser.close()

asyncio.run(main())
```

Kør paa VPS:
```bash
ssh root@VPS_IP "python3 /root/mcpserver/map_site.py"
```

### Hvad du leder efter i output

- `GET https://api.example.dk/...` — JSON API-kald
- `POST https://...` — form-submissions med data
- `GET https://.../document.pdf` — direkte PDF-links
- Base64-indhold i responses — tegn paa at PDF er indlejret i JSON

---

## Fase 3 — Klik igennem ALLE UI-elementer

Lazy-loaded data (data der kun hentes naer man klikker) vises IKKE i fase 2. Du skal eksplicit simulere klik.

### Tilfoej til kortlaegningsscriptet:

```python
async def click_and_intercept(page, selector_or_text, label):
    """Klik paa element og opfang nye network requests"""
    print(f"\n=== KLIK: {label} ===")

    try:
        # Forsoeg tekst-match (MUI TreeItem, accordions)
        el = page.get_by_text(selector_or_text, exact=False).first
        await el.click()
        await page.wait_for_timeout(2000)

        for line in OUTPUT[-20:]:
            print(line)
        OUTPUT.clear()

        text = await page.evaluate("document.body.innerText")
        print(f"POST-KLIK TEXT: {text[:300]}")
    except Exception as e:
        print(f"FEJL ved klik '{selector_or_text}': {e}")

# Eksempel: klik paa alle trae-elementer
await click_and_intercept(page, "Tidligere vurderingsmeddelelser", "SVUR liste")
await click_and_intercept(page, "2022", "SVUR 2022")
await click_and_intercept(page, "BBR-meddelelse", "BBR dokument")
```

### OIS-eksempel: hvad vi opdagede ved at klikke

- **`Tidligere vurderingsmeddelelser`** → loadede liste af aar (MUI TreeItem)
- **Klik paa specifikt aar** → network request afsloerede: `GetVurderingsmeddelelse?kommunenummer=X&ejendomsnummer=Y&vurderingsaar=Z&vurderingsdato=W`
- **`vurderingsdato`** var IKKE altid `YEAR-10-01` — f.eks. 2008: `vur_aendr_dato = 2011-12-12T00:00:00Z` (helt andet aar!)
- **Plandata undersider** havde UUID-baserede URLs der ikke kunne gættes

---

## Fase 4 — Kortlaeg fuld response-struktur

For HVERT API-endpoint du fandt: undersog JSON-svaret i detaljer.

```python
async def probe_api(url, params=None):
    """Kald API direkte og udskriv fuld response-struktur"""
    import httpx
    headers = {"User-Agent": "Mozilla/5.0...", "Accept": "application/json"}
    async with httpx.AsyncClient() as c:
        r = await c.get(url, params=params, headers=headers)
        data = r.json()
        print(f"STATUS: {r.status_code}")
        print(f"TOP-LEVEL KEYS: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        # Udskriv nested struktur
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])
```

### Hvad du dokumenterer for hvert endpoint

```
ENDPOINT: GET /api/example/GetData
PARAMS: id=, type=
RESPONSE KEYS: [key1, key2, key3[]]
NESTED: key3[].subfield → [beskrivelse af hvad det er]
KRITISK: key3[].datum er IKKE altid YYYY-MM-01 — hentes fra API, antages aldrig
PDF?: response["pdfData"] er base64-streng startende med "JVBERi0" (%PDF-)
```

---

## Fase 5 — Tjekliste foer MCP designes

Svar JA til ALLE punkter foer du skriver en linje MCP-kode:

- [ ] Alle undersider er besøgt og network requests opfanget
- [ ] Alle UI-klik (lazy-load, trae-elementer, accordions) er simuleret
- [ ] Alle parametre er verificeret fra live API-svar (ingen antagelser om format)
- [ ] PDF-haandtering er afklaret: base64 i JSON? Direkte download? Begge?
- [ ] Dynamiske UUIDs eller datoer: er det klart HVORDAN de hentes? (aldrig gættes)
- [ ] Overlappende data-sektioner er kortlagt (hvad er i hvilken response)
- [ ] Edge cases dokumenteret (hvad sker der hvis data mangler / tom liste returneres)

---

## Fase 6 — Design MCP tools

Foerst naar fase 5 er komplet: design tools.

### Principper

1. **Et bredt "hent alt"-tool kommer foerst** — ligesom `ois_property_info` der returnerer det meste i ét kald. Det afklarer hvad der er tilgængeligt.
2. **Specialiserede tools til PDF/dokument-hentning** — separat tool pr. dokument-type
3. **Ingen parametre der gættes** — alle dynamiske parametre hentes fra det brede tool
4. **Tool-docstrings indeholder workflow-guide** — hvornaar bruges hvilken tool, i hvilken raekkefolge

### FastMCP skabelon

```python
import asyncio, base64, io
import httpx, pypdf
from fastmcp import FastMCP

PORT = 8086  # eller andet ledig port
BASE = "https://www.example.dk"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept": "application/json, */*"}

mcp = FastMCP(
    "example-mcp",
    instructions="""
    [Workflow guide her — indsaettes automatisk i Claude's kontekst ved forbindelse]
    """
)

async def api_get(path, params=None):
    async with httpx.AsyncClient(timeout=20, headers=HEADERS) as c:
        r = await c.get(f"{BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()

async def pdf_download(path, params=None):
    async with httpx.AsyncClient(timeout=30, headers=HEADERS, follow_redirects=True) as c:
        r = await c.get(f"{BASE}{path}", params=params)
        r.raise_for_status()
        return r.content

def extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    return "\n\n".join(p.extract_text() or "" for p in reader.pages).strip()

def decode_base64_pdf(b64_string: str) -> str:
    pdf_bytes = base64.b64decode(b64_string)
    return extract_pdf_text(pdf_bytes)

@mcp.tool()
async def site_info(identifier: str) -> str:
    """
    Henter alt tilgaengeligt i ét kald.
    Brug dette FOERST — output afgoer hvilke parametre der bruges i efterfoelgende kald.
    """
    data = await api_get("/api/GetData", {"id": identifier})
    # ... formatér og returnér
    return "..."

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)
```

---

## Fase 7 — Deploy og verificering

### Systemd service

```bash
# Upload server til VPS
sftp root@VPS_IP <<EOF
put /local/path/server.py /root/mcpserver/server_name.py
EOF

# Opret service
ssh root@VPS_IP "cat > /etc/systemd/system/server-name.service" <<EOF
[Unit]
Description=Server Name MCP
After=network.target

[Service]
ExecStart=/root/mcpserver/venv/bin/python /root/mcpserver/server_name.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

ssh root@VPS_IP "systemctl daemon-reload && systemctl enable server-name && systemctl start server-name"
```

### Nginx proxy

```nginx
location /mcp-server-name-niroai/ {
    proxy_pass http://127.0.0.1:PORT/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 300s;
}
```

### `.mcp.json` tilfoejelse (lokal)

```json
"server-name": {
    "type": "http",
    "url": "https://niroai.cloud/mcp-server-name-niroai/mcp"
}
```

### Verificering — 4 tests der ALLE skal bestaa

```bash
# 1. Service kører
ssh root@VPS_IP "systemctl status server-name"

# 2. Port svarer (HTTP 406 = MCP protocol klar, ikke en fejl)
curl -s -o /dev/null -w "%{http_code}" http://VPS_IP:PORT/mcp

# 3. Basis-tool virker
# → Test via Claude: kald det brede "hent alt"-tool med et kendt ID

# 4. Dokument-tool virker
# → Test via Claude: kald PDF/dokument-tool og verificér tekst-output
```

---

## OIS MCP — Konkret reference (verificeret)

Dette er hvad vi faktisk fandt og byggede. Brug som skabelon-eksempel.

### Kortlagte endpoints

| Endpoint | Params | Returnerer |
|----------|--------|-----------|
| `GET /api/property/GetGeneralInfoFromBFE` | `bfe=` | Adresse, kommunekode, ejendomstype |
| `GET /api/property/GetPropertyFromBFE` | `bfe=` | Fuld BBR + SVUR-struktur (se nedenfor) |
| `GET /api/ejer/get` | `bfe=` | Ejernavn |
| `GET /api/svur/GetVurderingsmeddelelse` | `kommunenummer=, ejendomsnummer=, vurderingsaar=, vurderingsdato=` | Base64 PDF |
| `GET /api/plandata/GetPlandata` | `coords=POINT (x y)` | Lokalplaner, kommuneplan, zonestatus |
| `GET /bbrmeddelelse/get` | `bfe=` | PDF direkte download (ikke base64) |

### Kritiske fund (ville vaere antagelsesfejl hvis vi ikke havde undersøgt)

- `vurderingsdato` i `GetVurderingsmeddelelse` er IKKE altid `YEAR-10-01`
  - 2008: dato var `2011-12-12` (tre aar efter!)
  - Kilde: `svurCoreSFE.vurdMeddelList[].Vurderingsdato` i `GetPropertyFromBFE`
- Plandata koordinater hentes fra `grund[].Adgangsadresse.Position` (format: `"POINT (x y)"`)
- BBR-meddelelse er direkte PDF-download (ikke base64 i JSON)
- Vurderingsmeddelelse er base64 i JSON-response

### Opdaget ved UI-klik (ville vaere misset uden Playwright)

- `Tidligere vurderingsmeddelelser` MUI TreeItem → lazy-loadede aar-liste
- Klik paa specifikt aar → afsloerede de 4 parametre inkl. den korrekte `vurderingsdato`
- Plandata-undersider havde UUID-baserede URLs der ikke kunne konstrueres uden API-kald
