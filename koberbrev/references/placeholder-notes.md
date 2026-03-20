# Placeholder-noter — Koberbrev

Dette dokument lister alle `{{ PLACEHOLDER }}`-tags i koberbrev-skabelonen.

---

## Vigtig regel: Factuel vs. juridisk

**Enhver placeholder der slutter på `_ANALYSE` kræver selvstændig juridisk vurdering.**
Håndteres af dedikerede analyseagenter i FASE 5 — ét afsnit per agent, alle 9 parallelt.

Alle andre placeholders er faktuelle og udfyldes direkte fra kildedokumenterne.

---

## A — Sagshoved

| Placeholder | Beskrivelse | Kilde |
|-------------|-------------|-------|
| `{{ DATO }}` | Brevets dato | Advokat udfylder |
| `{{ JOURNALNR }}` | Sagsnummer | Sagssystem |
| `{{ KLIENTNAVN }}` | Fulde navn(e), fx "Kamilla og Peter Hjortkjær" | Købsaftale |
| `{{ KLIENT_ADRESSE }}` | Klienternes adresse | Købsaftale |
| `{{ KLIENT_EMAIL }}` | Klienternes e-mail(s) | Sagssystem |

*Kira Niro, kn@hankelaw.dk, HankeLaw Advokatanpartsselskab = FAST — aldrig placeholder.*

---

## B — Brevhoved og åbning

| Placeholder | Beskrivelse | Kilde |
|-------------|-------------|-------|
| `{{ ADRESSE }}` | Ejendommens fulde adresse inkl. etage og side | Købsaftale |
| `{{ HILSEN_NAVN }}` | Fornavn(e) til "Kære X", fx "Kamilla og Peter" | Sagssystem |

---

## C — Pronomenplaceholders

Sættes i fase 1 baseret på antal købere. Bruges til at erstatte alle du/I-former i brevet.

| Placeholder | Ental | Flertal |
|-------------|-------|---------|
| `{{ PRONOMEN }}` | du | I |
| `{{ PRONOMEN_STOR }}` | Du | I |
| `{{ PRONOMEN_OBJ }}` | dig | jer |
| `{{ PRONOMEN_GEN }}` | din | jeres |
| `{{ PRONOMEN_REFL }}` | dig | jer (refleksiv) |
| `{{ PRONOMEN_BERETTIGET }}` | berettiget | berettigede |
| `{{ PRONOMEN_FORPLIGTET }}` | forpligtet | forpligtede |

---

## D — Generelle faktaoplysninger

| Placeholder | Beskrivelse | Kilde |
|-------------|-------------|-------|
| `{{ ADVOKATFORBEHOLD_DATO }}` | Frist-dato for advokatforbeholdet | Købsaftale |
| `{{ ADVOKATFORBEHOLD_KL }}` | Klokkeslæt, fx "16" | Købsaftale |
| `{{ KOEBESUM }}` | Kontantpris i kr. (bruges 2 gange) | Købsaftale pkt. 3/13 |
| `{{ DEPONERING_KR }}` | Deponeringbeløb i kr. | Købsaftale pkt. 13 |
| `{{ DEPONERING_HVERDAGE }}` | Antal hverdage for deponering | Købsaftale pkt. 13 |
| `{{ BANKGARANTI_KR }}` | Bankgarantibeløb i kr. | Købsaftale pkt. 13 |
| `{{ BANKGARANTI_HVERDAGE }}` | Antal hverdage for bankgaranti | Købsaftale pkt. 13 |
| `{{ TINGBOG_DATO }}` | Dato for tingbogsattest | Tingbog |
| `{{ ADKOMSTHAVER }}` | Nuværende ejer(e) | Tingbog |
| `{{ SERVITUTTER_ANTAL }}` | Antal tinglyste servitutter | Tingbog |
| `{{ HAEFTELSER_ANTAL }}` | Antal tinglyste hæftelser | Tingbog |
| `{{ FORENINGSTYPE }}` | "Ejerforening" eller "Grundejerforening" | BBR / dokumenter |
| `{{ TILSTANDSRAPPORT_DATO }}` | Udstedelsesdato for tilstandsrapport | Tilstandsrapport |
| `{{ TILSTANDSRAPPORT_UDLOEB }}` | Udløbsdato for tilstandsrapport | Tilstandsrapport |
| `{{ ELRAPPORT_DATO }}` | Udstedelsesdato for elinstallationsrapport | Elinstallationsrapport |
| `{{ ELRAPPORT_UDLOEB }}` | Udløbsdato for elinstallationsrapport | Elinstallationsrapport |
| `{{ EJERSKIFTEFORSIKRING_SELSKAB }}` | Forsikringsselskabets navn | Bilag |
| `{{ EJERSKIFTEFORSIKRING_DATO }}` | Dato for forsikringstilbud | Bilag |
| `{{ EJERSKIFTEFORSIKRING_KR }}` | Sælgers betalingsandel i kr. | Bilag |
| `{{ ENERGIMAERKE_DATO }}` | Udstedelsesdato for energimærke | Energimærke |
| `{{ ENERGIMAERKE_UDLOEB }}` | Udløbsdato for energimærke | Energimærke |
| `{{ ENERGIMAERKE }}` | Bogstav A–G | Energimærke |
| `{{ EJENDOMSDATARAPPORT_DATO }}` | Rapportdato | Ejendomsdatarapport |
| `{{ JORDFORURENING_STATUS }}` | "ikke kortlagt" / "kortlagt på V1" / "kortlagt på V2" | Ejendomsdatarapport |
| `{{ TILBEHOER }}` | Liste over medfølgende hårde hvidevarer og løsøre | Salgsopstilling |

---

## E — Juridisk analyse (slutter alle på `_ANALYSE`)

Disse tags kræver selvstændig juridisk vurdering. Brug FASE 6-loopet (trin 1–5 i SKILL.md) — ét tag ad gangen.

| Placeholder | Afsnit i brevet | Dokumenter |
|-------------|-----------------|-----------|
| `{{ SERVITUT_ANALYSE }}` | Adkomsthaver, hæftelser og servitutter | Tingbog, servitutdokumenter |
| `{{ HAEFTELSER_ANALYSE }}` | Adkomsthaver, hæftelser og servitutter | Tingbog, købsaftale |
| `{{ EJERFORENING_ANALYSE }}` | Grundejerforening / Ejerforening | Årsrapport, vedtægt, generalforsamlingsreferat, vedligeholdelsesplan, forsikringspolice, administratorbesvarelse, virk.dk |
| `{{ BBR_ANALYSE }}` | BBR og Ejendommen | BBR-meddelelse, købsaftale |
| `{{ LOKALPLAN_ANALYSE }}` | Lokalplan | Lokalplan fra planinfo.dk, ejendomsdatarapport |
| `{{ TILSTAND_ANALYSE }}` | Tilstands- og elinstallationsrapporter | Tilstandsrapport |
| `{{ ELINSTALLATION_ANALYSE }}` | Tilstands- og elinstallationsrapporter | Elinstallationsrapport |
| `{{ VARMEFORBRUG_ANALYSE }}` | Energimærke | Energimærkningsrapport |
| `{{ JORDFORURENING_ANALYSE }}` | Jordforurening | Ejendomsdatarapport, jordforureningsattest |
| `{{ KONKLUSION_ANALYSE }}` | Konklusion og udkast til mail til mægler | Alle dokumenter — Claude skriver hele sektionen inkl. betingelser, ønsker og mægler-mail |

---

## F — Konklusion / mægler-mail

`{{ KONKLUSION_ANALYSE }}` dækker hele konklusionssektionen som Claude skriver som fri tekst.
Inkluderer: indledende vurdering, betingelsesliste, ønsker til sælger, og mægler-mail med `{{ MAEGLER_NAVN }}` som salutation.

| Placeholder | Beskrivelse | Kilde |
|-------------|-------------|-------|
| `{{ MAEGLER_NAVN }}` | Mæglerens navn til "Kære X" i mailen | Sagssystem |

*`{{ MAEGLER_NAVN }}` opgives som faktum til Claude, der indlejrer det i `{{ KONKLUSION_ANALYSE }}`.*

---

## Detaljerede overvejelser pr. `_ANALYSE`-tag

Se de individuelle afsnit nedenfor. Gennemgå ALLE punkter for hvert tag inden du skriver.

---

### `{{ SERVITUT_ANALYSE }}`

**Lovsamlinger:** Tinglysningsloven §§ 1, 10, 16; Grundejerforeningsloven (uskrevet ret)
**Typiske komplikationer:** Servitut der forbyder udstykning, byggelinjepålæg der blokerer tilbygning, grundejerforeningspligt med høje kontingenter, uklart hvem der er påtaleberettiget
**Ejendomstype-variation:** Ejerlejlighed — facadeservitutter håndteres af ejerforening; Parcelhus — byggebegrænsninger rammer ejeren direkte
**Standardberegninger:** Er der løbende betalingsforpligtelse? Hvad koster grundejerforeningskontingent pr. år?
**Kritiske detaljer:** Er servitutten pantstiftende? Er den tidsbegrænset? Hvem er påtaleberettiget (privat / kommune / forening)?

**Behandl hver servitut separat.**

> **Må ikke:** Indlede med en gentagelse af antallet af servitutter — det fremgår allerede af sætningen umiddelbart inden i brevet ("der er lyst X servitutter").
> **Må ikke:** Bruge "unormal byrde" — skriv "usædvanlig byrde" eller "byrde ud over det sædvanlige".

1. Hvad pålægger servitutten ejeren at gøre eller undlade? Positiv eller negativ servitut?
2. Pålægger servitutten køber at være medlem af en grundejerforening? Kontingent og årstal?
3. Begrænser servitutten koebers mulighed for at bygge til, ombygge eller udnytte ejendommen?
4. Giver servitutten tredjemand ret til færdsel, parkering, ledningsføring eller andet?
5. Indebærer servitutten løbende betalingsforpligtelser? FLAG hvis væsentlig.

---

### `{{ HAEFTELSER_ANALYSE }}`

**Lovsamlinger:** Tinglysningsloven §§ 1, 10, 40–47; Kreditaftaleloven
**Typiske komplikationer:** Ejerpantebrev med gammel, høj grænse der overstiger købesum; privat pantebrev med ukendt kreditor der kan blokere frigivelse; tinglyst udlæg der ikke fremgår tydeligt
**Ejendomstype-variation:** Ejerlejlighed — fællesudgiftspanteret (ejerforeningens panteret i lejligheden) fremgår ikke altid af tingbogen
**Standardberegninger:** Sum af alle hæftelser vs. købesum — er der underskud?
**Kritiske detaljer:** Er ejerpantebreve transporteret til tredjemand? Dato for tinglysning vs. overtagelsesdato

> **Må ikke:** Indlede med en gentagelse af antallet af hæftelser — det fremgår allerede af sætningen umiddelbart inden.
> **Må ikke:** Slutte med en underskudshandel-konklusion — den sætning er fast boilerplate i brevet efter dette tag.

1. Beskriv hæftelsernes art: realkreditlån, ejerpantebrev, privat pantebrev?
2. Er der pantehæftelser ud over det forventede (fx ud over købesummen)?
3. FLAG hvis købesummen ikke kan dække samtlige hæftelser (underskudshandel).

---

### `{{ EJERFORENING_ANALYSE }}`

**Lovsamlinger:** Ejerlejlighedsloven; ABF standardvilkår for ejendomshandler; Årsregnskabsloven (for foreningens regnskab)
**Typiske komplikationer:** Utilstrækkelige henlæggelser til fremtidigt vedligehold, besluttet større renovering med ekstraordinære bidrag, verserende retssager mod foreningen, forsikring der ikke dækker fællesarealer tilstrækkeligt
**Ejendomstype-variation:** Kun relevant ved ejerlejlighed. Ved parcelhus: erstat med grundejerforeningsanalyse hvis relevant. Spring over ved andelsbolig.
**Standardberegninger:** Stemmer ejerudgifter i ejerlejlighedsskema med salgsopstillingens tal? Er henlæggelserne tilstrækkelige ift. vedligeholdelsesplanens estimater?
**Kritiske detaljer:** Ejerforeningens CVR-nummer verificeres på virk.dk. Generalforsamlingsbeslutninger med ekstraordinære bidrag inden for de næste 2 år FLAG-markeres.

> **Sprogkrav:** Skriv "Jeg anbefaler, at I/du ligeledes gennemgår vedtægterne" — komma efter "anbefaler" er obligatorisk. Brug direkte tiltaleform (ikke upersonlig konstruktion "det anbefales").

1. **Regnskab og økonomi** — Er egenkapitalen positiv? Tilstrækkelige henlæggelser? Kortfristet gæld? Afvigelse fra salgsopstillingens ejerudgifter?
2. **Vedligeholdelsesplan** — Planlagte større arbejder? Finansieret eller kræver ekstraordinære bidrag? FLAG hvis køber bidrager kort efter overtagelse.
3. **Generalforsamling** — Beslutninger med økonomisk konsekvens? Igangværende sager?
4. **Forsikring** — Dækker foreningens forsikring fællesarealerne tilstrækkeligt?
5. **Vedtægt** — Usædvanlige bestemmelser (fremlejeforbud, erhvervsbegrænsninger, brugsret)?

---

### `{{ BBR_ANALYSE }}`

**Lovsamlinger:** Byggeloven; Planloven; Bekendtgørelse om bygnings- og boligregistrering (BBR-bekendtgørelsen)
**Typiske komplikationer:** Uregistreret tilbygning eller ombygning der kræver lovliggørelse, forkert registreret opvarmningsform, bevaringsværdi 4 eller derunder der indskrænker ombygningmuligheder
**Ejendomstype-variation:** Ejerlejlighed — BBR dækker primært den samlede ejendom; lejlighedsspecifikke forhold fremgår af ejerlejlighedsskema. Parcelhus — alle bygninger på grunden skal kontrolleres.
**Standardberegninger:** Ingen direkte, men sammenlign registreret areal med det der er nævnt i salgsopstillingen.
**Kritiske detaljer:** Kommunens varmeplan: er der planlagt tilslutningspligt inden for 5–10 år? Estimér omkostning for køber. Bevaringsværdi tjekkes via BBR og lokalplan.

> **Sprogkrav:** Brug direkte tiltaleform — skriv fx "Jeg anbefaler, at I er opmærksomme på..." i stedet for upersonligt "det anbefales at...".

1. **Registrerede forhold** — Stemmer BBR overens med ejendommens faktiske fremtræden? Uregistrerede tilbygninger?
2. **Opvarmningsform** — Korrekt registreret? Planlagte ændringer i kommunens varmeplan? Estimeret økonomisk konsekvens. FLAG hvis tilslutningspligt forventes inden for 5–10 år.
3. **Bevaringsværdi** — Har ejendommen bevaringsværdi 4 eller derunder? FLAG — skærpede krav til ydre fremtræden.

---

### `{{ LOKALPLAN_ANALYSE }}`

**Lovsamlinger:** Planloven §§ 13–18; Miljøvurderingsloven (ved større projekter i nærhed)
**Typiske komplikationer:** Ejendommen er udpeget som bevaringsværdig med krav til facadematerialer, fremtidigt boligbyggeri i nærhed der reducerer udsigt/lys, zoneskift planlagt der ændrer ejendommens anvendelsesmuligheder
**Ejendomstype-variation:** Gælder alle ejendomstyper. Ejerlejlighed: facadekrav koordineres af ejerforeningen, men køber bærer risikoen.
**Standardberegninger:** Ingen direkte beregning, men vurdér om planlagte byggerier inden for 500 m har væsentlig påvirkning på ejendommens værdi.
**Kritiske detaljer:** Søg altid på planinfo.dk med ejendommens adresse. Notér lokalplanens nummer og navn. Er der udstedt dispensationer?

1. **Formål og anvendelse** — Er nuværende anvendelse i overensstemmelse med lokalplanen?
2. **Fremtidigt byggeri** — Planlagte byggerier eller zoneskift i nærhed? FLAG hvis væsentlig påvirkning.
3. **Byggebegrænsninger** — Begrænsninger for til-/ombygning, tagudhøjde, facade, materialevalg?
4. **Bevaringsværdi** — Er ejendommen udpeget som bevaringsværdig i lokalplanen?

---

### `{{ TILSTAND_ANALYSE }}`

**Lovsamlinger:** Forbrugerbeskyttelsesloven ved erhvervelse af fast ejendom (inkl. bek. nr. 13 af 12. januar 2012); Lov om forbrugerbeskyttelse ved erhvervelse af fast ejendom § 4
**Typiske komplikationer:** Mange K2-noter på samme bygningsdel (mønster der indikerer skjult problem), K3-note med uafklaret årsag, UN-noter der bør undersøges inden overtagelse, rapport der udløber inden overtagelsesdato
**Ejendomstype-variation:** Gælder alle ejendomstyper. Ejerlejlighed: K3-noter på fællesarealer håndteres af foreningen — men køber bærer risikoen for manglende udbedring.
**Standardberegninger:** Er rapporten gyldig på overtagelsesdagen? Udløbsdato vs. overtagelsesdato. FLAG hvis ikke.
**Kritiske detaljer:** Retten til at annullere handlen hvis teknisk rådgiver anbefaler det. Sælger mister mangelsansvarsfrihed hvis rapport udløber inden overtagelse.

1. K3-noter (kritiske)? Beskriv konsekvenser for køber.
2. K2-noter (særlig opmærksomhed)? Mønstre (fx mange K2 på tag, fugt)?
3. UN-noter der bør følges op?
4. Anbefal teknisk rådgiver hvis antallet eller alvoren af noter berettiger det — anfør at køber har ret til at annullere handlen.
5. Er rapporten gyldig på overtagelsesdagen? FLAG hvis ikke.

---

### `{{ ELINSTALLATION_ANALYSE }}`

**Lovsamlinger:** Stærkstrømsbekendtgørelsen; Forbrugerbeskyttelsesloven ved erhvervelse af fast ejendom (bek. nr. 13 af 12. januar 2012)
**Typiske komplikationer:** IN2-forhold (funktionsfejl der kræver udbedring), ulovlige installationer der kræver el-autoriseret håndværker, rapport der udløber inden overtagelse
**Ejendomstype-variation:** Ejerlejlighed: installationer inden for lejligheden købers ansvar; fælles forsyningsledninger er foreningens ansvar.
**Standardberegninger:** Estimeret udgift til udbedring af IN2-forhold. Er rapporten gyldig på overtagelsesdagen? FLAG hvis ikke.
**Kritiske detaljer:** IN1 = anmærkning (ikke akut). IN2 = funktionsfejl (skal udbedres). Sælger mister mangelsansvarsfrihed hvis rapport udløber inden overtagelse.

1. Ulovlige eller funktionsfejlende installationer?
2. Estimeret udgift til udbedring?
3. Er rapporten gyldig på overtagelsesdagen? FLAG hvis ikke.

---

### `{{ VARMEFORBRUG_ANALYSE }}`

**Lovsamlinger:** Energimærkningsloven; Byggeloven (krav til energiramme ved renovering)
**Typiske komplikationer:** Energimærke udløber inden overtagelsesdato, anbefalede forbedringer med høj estimeret omkostning, discrepans mellem energimærke og faktisk opvarmningsform registreret i BBR
**Ejendomstype-variation:** Ejerlejlighed: energimærke dækker typisk hele ejendommen; den individuelle lejlighed kan afvige. Parcelhus: mærket dækker hele bygningen.
**Standardberegninger:** Er energimærket gyldigt på overtagelsesdagen? Udløbsdato vs. overtagelsesdato. FLAG hvis ikke.
**Kritiske detaljer:** Energimærke A–G. Mærket er gyldigt i 10 år (nyere bygninger) eller 7 år (ældre). Nyt mærke kræves ved salg hvis det er udløbet.

> **Må ikke:** Indlede med en gentagelse af energimærke-bogstavet — det fremgår allerede af sætningen umiddelbart inden ("ejendommen har energimærke X").

1. Hvad siger energimærket om ejendommens varmeforbrug og forbedringspotentiale?
2. Er der konkrete anbefalinger til forbedringer med estimerede besparelser?
3. Er mærket relevant ift. ejendommens alder og type?

---

### `{{ JORDFORURENING_ANALYSE }}`

**Lovsamlinger:** Jordforureningsloven; Miljøbeskyttelsesloven; Olietankbekendtgørelsen
**Typiske komplikationer:** V2-kortlægning (dokumenteret forurening) der kræver kommunal tilladelse ved anvendelsesændring eller gravearbejde, olietank der ikke er korrekt sløjfet med dokumentation, forurening fra nabogrund
**Ejendomstype-variation:** Parcelhus: nedgravet olietank er hyppig. Ejerlejlighed: individuel olietank sjælden; tjek ejendomsdatarapport for hele grunden.
**Standardberegninger:** Ingen direkte, men vurdér om V1/V2-status øger ejerskifteforsikringspræmien væsentligt.
**Kritiske detaljer:** V1 = mistanke om forurening. V2 = dokumenteret forurening. FLAG ved V2 — køber bør rådføre sig med kommunen. Olietank: sløjfningsattest fra autoriseret firma er påkrævet.

> **Olietank — konditionelt afsnit:**
> - Hvis der **ikke** er en olietank: skriv kort "Der er ikke oplysninger om nedgravet olietank på ejendommens grund, og der er ikke grundlag for yderligere undersøgelse heraf."
> - Hvis der **er** en olietank: beskriv sløjfningsstatus og inkluder standardtekst om udvidet ejerskifteforsikringens relevans, betingelserne for dækning og anbefaling til køber om at gennemgå forsikringsvilkårene.
> - Inkluder **aldrig** olietank-afsnittet, hvis der ikke er en tank — det skaber forvirring.

1. Er ejendommen kortlagt på V1 (mistanke) eller V2 (dokumenteret)? Kilde til forureningen?
2. Er der en nedgravet olietank? Er den sløjfet korrekt med dokumentation?
3. FLAG ved V2 — køber bør rådføre sig med kommunen om handlemuligheder ved ændret anvendelse eller gravearbejde.

---

### `{{ KONKLUSION_ANALYSE }}`

**Lovsamlinger:** Alle relevante love fra FASE 5 — dette afsnit sammenfatter hele analysen.
**Typiske komplikationer:** FLAG-punkter fra individuelle analyser skal alle fremgå her; glemte betingelser (bankgodkendelse, vurdering) er en alvorlig fejl; mægler-mailen skal have korrekt salutation.
**Ejendomstype-variation:** Betingelseslisten tilpasses ejendomstype — ejerlejlighed inkluderer typisk gennemgang af foreningsdokumenter som betingelse.
**Standardberegninger:** Alle FLAG-punkter fra fase 6 og 7 samles her med kildehenvisning. Underskudshandel fremgår her.
**Kritiske detaljer:** Mindst pkt. 1 (bankgodkendelse) og pkt. 2 (uafhængig vurdering) er faste betingelser der altid medtages. Mægler-mailen afsluttes med "Vi ser frem til at høre fra jer."

Claude skriver hele sektionen som fri tekst inkl.:
- Indledende juridisk vurdering ("I det modtagne materiale har jeg...")
- Betingelsesliste (nummereret) — mindst pkt. 1 og 2 er faste (bankgodkendelse + vurdering)
- Ønsker og spørgsmål til sælger (punktliste)
- Mægler-mail med korrekt salutation (Kære `{{ MAEGLER_NAVN }}`)
- Afslutning ("Vi ser frem til at høre fra jer.")
