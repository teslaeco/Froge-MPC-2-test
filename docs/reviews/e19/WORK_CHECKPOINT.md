# E19 / Oracle v35 — checkpoint po naprawie wydania

Stan przygotowania dokumentacji: 13 września 2026. Praca E19 jest osobnym etapem po scaleniu PR #11. Źródła modelu, rendery, audyt produkcji i wdrożenia muszą mieć osobne potwierdzenia.

## Kod i wydanie — potwierdzone

- PR #11 scalony do `codex/v27-mcp-startup-audit`; merge `23a7b5859f6093073bedeb037b2ba0e75b142c7b`. Korekta E19 i dowody są w osobnym [PR #12](https://github.com/teslaeco/Froge-MPC-2-test/pull/12), nadal draft, na gałęzi `codex/e19-anatomy-production-audit`.
- Zweryfikowany runtime v35: commit `4c6c7fb000a98627264d7c6bcca1f441eb760fe2`, [CI 34733597773](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34733597773). Oba logi potwierdzają 150 testów, Python 3.9 i 3.12. Zadanie 3.9 wykonało rzeczywisty Codex/MCP/Blender, GLB/FBX, sześć przypadków atlasów i szachownice 64/512 pól.
- Gotowa paczka `froge-v35.zip`: 394 642 B, SHA256 `913918c69dd44a0579b71819522204d1c31f7d5eb4b38c952659347dd9b11c2a`; payload `da7bc39d22b829f757c548beea44db3fdffa57e08188df356b3d47a70ced0d23` zgodny z CI.
- Sprawdzono CRC, kompilację i osadzone źródła: serwer i instalator 35, `referenceAcceptanceRevision=1`, `workerRelease=v35-reference-acceptance`. Komunikat ukończenia zadania stosuje rzeczywistą hostową ocenę aktualnego eksportu.
- ZIP odtworzono deterministycznie ze sprawdzonych źródeł; nie deklarować identyczności binarnej z oryginalnym archiwum CI. Nie tworzono brakujących atlasów zastępczych.

## Sprostowanie v34

Wcześniejszy ZIP o nazwie v34 zawierał serwer i instalator deklarujące wersję 33. Testy nie sprawdzały tożsamości wydania. **Nie używać v34; obowiązuje [instrukcja v35](../ORACLE-v35.md).**

Doprecyzowanie wcześniejszego checkpointu: host gate był już używany przez API jakości i `model_status`. Brakujące połączenie dotyczyło tekstowego komunikatu ukończenia zadania, który ufał surowej akceptacji agenta. Stwierdzenie, że żadna kontrola hosta nie działała, byłoby zbyt szerokie. V35 naprawia zarówno to niespójne raportowanie, jak i wersję/capability oraz wymagania instalatora.

## Rzeczywisty model E19 — wygenerowany, nie zatwierdzony jako produkt

- Połączono trzy lokalne korekty zęby/oko, ciało/mapy i włosy. [Raport budowy](final/build-report.json): 6 384 581 trójkątów, 379 obiektów siatkowych. Zachowano źródłowy E18R.
- 24 korony zębowe, cztery łoża korzeni, nowa cofnięta głębia ust; obecne ciemne oko w kostnej połowie i lokalny brzeg oczodołu. Nie zwiększano globalnej głowy.
- Wspólna korekta szyi, torsu, gorsetu i szwów; 124 naprawione trójkąty UV. Trzy mapy torsu/szyi 8192 × 8192 px są bake'iem materiałów proceduralnych. Twarz pozostaje przy odziedziczonej teksturze o niższej rozdzielczości.
- Zwężono 312 rdzeni włosów, zachowano drobne włókna i wcześniejszą nasadę. Odrzucono eksperymenty tworzące regularną zasłonę.
- `FORGE-E19-8K.glb`: 64 211 024 B, SHA256 `f5196a7e6b822d50bbfdaa9d7f6051919b7d48a2e6a84fa5f3082cfc45c5e4f9`.
- `FORGE-E19-web.glb`: 27 521 620 B, SHA256 `08b88ea54b5046e579a9dab0e4f85342ffabdf3b9ed5932c3d49a00ec2b63cb4`, mapy ciała 2K. Późniejsza optymalizacja wymaga nowego raportu/hash-u.
- Ukończono sześć rzeczywistych widoków E19 po ponownym imporcie GLB oraz dodatkowe zbliżenie ciała z mastera 8K. Porównanie E18R/E19 korzysta ze wspólnych kamer i oświetlenia. [Manifest renderów](final/render-verification.json) potwierdza hashe i rozdzielczości; podglądy nie są ilustracjami generatywnymi.

## Audyt i nierozwiązane sprawy

- Audyty wejściowego E18R i finalnego E19 są osobne. [Wizualny E19](audit/E19-production-audit.json) ma 19 001 otwartych krawędzi, 47 116 krawędzi należących do więcej niż dwóch ścian oraz 124 634 trójkąty zdegenerowane po dokładnym połączeniu identycznych pozycji. Master nie jest gotową bryłą produkcyjną.
- Ukończono osobną kopię konstrukcyjną 200 mm: STL oraz ponownie importowany GLB mają 2 120 444 trójkąty, jedną połączoną składową i zero wykrytych błędów topologii krawędzi oraz degeneracji. [Raport STL](print/print-STL-production-audit.json), [raport GLB](print/print-GLB-production-audit.json) i [manifest końcowy](print/print-final-delivery-manifest.json) dotyczą konkretnych finalnych plików.
- **Kopia konstrukcyjna została odrzucona wizualnie do sprzedaży:** poszarpane włosy, uproszczone rysy i uzębienie oraz niepotwierdzone podparcie tułowia. Brak kwalifikacji procesu, próbki fizycznej, pełnych pomiarów minimalnych grubości, przecięć i podpór. Jedna zamknięta składowa nie oznacza gotowego produktu. [Ograniczenia](print/README-PRINT-E19.md).
- Dodatkowa izolowana próba wygładzenia włosów i piedestału również nie została przyjęta: wygląd nadal niewystarczający, wysokość 199,9386 mm poza założeniem 200 ±0,01 mm. Nie zastąpiła plików końcowych.
- Przeszło 20 testów Python metryk i reguły dopuszczenia oraz 20 testów Node formularza i pobierania plików. Testy Node używają kontrolowanego DOM, nie przeglądarkowego WebGL. Reguła dopuszczenia wiąże ocenę z hashem STL i po odrzuceniu wymaga naprawy; to moduł offline, jeszcze nie blokada zamówień wdrożona na Oracle.
- Meshy jest porównywany z dostarczonych screenshotów. Nie mamy jego eksportu do kontrolowanego benchmarku. Złożone postacie, wachlarz i szachownice mają oddzielne poziomy dowodów; nie ogłaszać rankingu ani zmyślonych procentów.
- Nadal niedoskonałe: podobieństwo twarzy, żywe oko, nos, profil czaszki i grupowanie włosów. 8K map ciała nie rozwiązuje tych braków.
- **Nie uruchomiono instalatora ani wdrożenia v35 na Oracle**: brak sesji SSH. Dopiero wynik instalacji właściciela i health potwierdzają wersję. Scalenie PR nie zmienia serwera.
- Publiczny FORGE Studio z E19 opublikowano jako **wersję 3**: https://forge-studio-public.terraformingplanet.chatgpt.site . Źródła: `fe05d7400b64fefd44736863d870174b5c00280e`; deployment `appgdep_6aa61c9f6c208191870473026181a2be` ma stan **succeeded**. Prywatnego Studio ani Oracle nie zaktualizowano.
- Julia w bluzie i Atlas z wcześniejszych zgłoszeń nadal wymagają swoich eksportów. E19 w sukni nie zastępuje tamtych modeli.
- Nie wykonano treningu wag Astra, treningu L4 ani nowej płatnej generacji API. Nie podłączono płatności, zamówień B2B ani produkcyjnego CAM/sterowania laserem.

Rendery, końcowy audyt i publikacja E19 są ukończone. Kopia konstrukcyjna pozostaje odrzucona do sprzedaży; moduł oceny procesu jest offline. Dowód publikacji: `docs/reviews/e19/publication-receipt.json` w repozytorium.
