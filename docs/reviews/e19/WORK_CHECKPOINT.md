# E19 / Oracle v35 — checkpoint po naprawie wydania

Stan przygotowania dokumentacji: 13 września 2026. Praca E19 jest osobnym etapem po scaleniu PR #11. Źródła modelu, rendery, audyt produkcji i wdrożenia muszą mieć osobne potwierdzenia.

## Kod i wydanie — potwierdzone

- PR #11 scalony do `codex/v27-mcp-startup-audit`; merge `23a7b5859f6093073bedeb037b2ba0e75b142c7b`. Dalsza gałąź: `codex/e19-anatomy-production-audit`.
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
- Skrypt renderuje ponownie importowane GLB przy wspólnych kamerach i światłach. Do końcowego handoff dołączyć faktycznie ukończone widoki i `render-verification.json`; nie zastępować ich ilustracją generatywną.

## Audyt i nierozwiązane sprawy

- Wejściowy E18R został zmierzony i nie spełnia kryteriów gotowego produktu fizycznego. Jego liczb błędów nie przypisywać E19. Osobny audyt finalnego E19 i jego ewentualnej kopii produkcyjnej wymagają własnych raportów bieżących plików.
- Nowe skrypty audytu oraz konwersji produkcyjnej przeszły testy małej sceny kontrolnej; sama próbka nie dowodzi ukończenia kopii drukowalnej postaci. Brak potwierdzonej próbki fizycznej, pełnych pomiarów grubości, przecięć, podpór i profilu wykonawcy.
- Meshy jest porównywany z dostarczonych screenshotów. Nie mamy jego eksportu do kontrolowanego benchmarku. Złożone postacie, wachlarz i szachownice mają oddzielne poziomy dowodów; nie ogłaszać rankingu ani zmyślonych procentów.
- Nadal niedoskonałe: podobieństwo twarzy, żywe oko, nos, profil czaszki i grupowanie włosów. 8K map ciała nie rozwiązuje tych braków.
- **Nie uruchomiono instalatora ani wdrożenia v35 na Oracle**: brak sesji SSH. Dopiero wynik instalacji właściciela i health potwierdzają wersję. Scalenie PR nie zmienia serwera.
- Ostatni potwierdzony publiczny Site: wersja 2 z E18R. Publikację E19 potwierdzić oddzielnym odczytem deploymentu. Prywatny Studio pozostawał w wersji 47; nie deklarować jego aktualizacji bez potwierdzenia.
- Julia w bluzie i Atlas z wcześniejszych zgłoszeń nadal wymagają swoich eksportów. E19 w sukni nie zastępuje tamtych modeli.
- Nie wykonano treningu wag Astra, treningu L4 ani nowej płatnej generacji API. Nie podłączono płatności, zamówień B2B ani produkcyjnego CAM/sterowania laserem.

Przed odpowiedzią końcową uzupełnić ten checkpoint wyłącznie o uzyskane potwierdzenia finalnych renderów, końcowego audytu, zapisanych plików i ewentualnej publikacji. [Porównanie i zakres](COMPARISON-E19.md).


### Dopisane po ponownym imporcie E19
Wszystkie sześć widoków E19 ukończone, dodatkowe zbliżenie mastera 8K ukończone. Hash i rozdzielczości potwierdzone w final/render-verification.json. Audyt wizualnego eksportu ma otwarte powierzchnie; nie akceptować go jako fizycznego produktu. Osobna kopia 200 mm i jej kontrola są nadal w toku. Nowe obrazy porównawcze pochodzą z rzeczywistych renderów.
