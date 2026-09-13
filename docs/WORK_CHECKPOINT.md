# E19 / Oracle v35 — checkpoint po naprawie wydania

Stan przygotowania dokumentacji: 13 września 2026. Praca E19 jest osobnym etapem po scaleniu PR #11. Źródła modelu, rendery, audyt produkcji i wdrożenia muszą mieć osobne potwierdzenia.

## Kod i wydanie — potwierdzone

- PR #11 scalony do `codex/v27-mcp-startup-audit`; merge `23a7b5859f6093073bedeb037b2ba0e75b142c7b`. Korekta E19 i dowody są w osobnym [PR #12](https://github.com/teslaeco/Froge-MPC-2-test/pull/12), nadal draft, na gałęzi `codex/e19-anatomy-production-audit`.
- Zweryfikowany runtime v35: commit `4c6c7fb000a98627264d7c6bcca1f441eb760fe2`, [CI 34733597773](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34733597773). Oba logi potwierdzają 150 testów, Python 3.9 i 3.12. Zadanie 3.9 wykonało rzeczywisty Codex/MCP/Blender, GLB/FBX, sześć przypadków atlasów i szachownice 64/512 pól.
- Gotowa paczka `froge-v35.zip`: 394 642 B, SHA256 `913918c69dd44a0579b71819522204d1c31f7d5eb4b38c952659347dd9b11c2a`; payload `da7bc39d22b829f757c548beea44db3fdffa57e08188df356b3d47a70ced0d23` zgodny z CI.
- Sprawdzono CRC, kompilację i osadzone źródła: serwer i instalator 35, `referenceAcceptanceRevision=1`, `workerRelease=v35-reference-acceptance`. Komunikat ukończenia zadania stosuje rzeczywistą hostową ocenę aktualnego eksportu.
- ZIP odtworzono deterministycznie ze sprawdzonych źródeł; nie deklarować identyczności binarnej z oryginalnym archiwum CI. Nie tworzono brakujących atlasów zastępczych.

## Sprostowanie v34

Wcześniejszy ZIP o nazwie v34 zawierał serwer i instalator deklarujące wersję 33. Testy nie sprawdzały tożsamości wydania. **Nie używać v34; obowiązuje [instrukcja v35](reviews/ORACLE-v35.md).**

Doprecyzowanie wcześniejszego checkpointu: host gate był już używany przez API jakości i `model_status`. Brakujące połączenie dotyczyło tekstowego komunikatu ukończenia zadania, który ufał surowej akceptacji agenta. Stwierdzenie, że żadna kontrola hosta nie działała, byłoby zbyt szerokie. V35 naprawia zarówno to niespójne raportowanie, jak i wersję/capability oraz wymagania instalatora.

## Rzeczywisty model E19 — wygenerowany, nie zatwierdzony jako produkt

- Połączono trzy lokalne korekty zęby/oko, ciało/mapy i włosy. [Raport budowy](reviews/e19/final/build-report.json): 6 384 581 trójkątów, 379 obiektów siatkowych. Zachowano źródłowy E18R.
- 24 korony zębowe, cztery łoża korzeni, nowa cofnięta głębia ust; obecne ciemne oko w kostnej połowie i lokalny brzeg oczodołu. Nie zwiększano globalnej głowy.
- Wspólna korekta szyi, torsu, gorsetu i szwów; 124 naprawione trójkąty UV. Trzy mapy torsu/szyi 8192 × 8192 px są bake'iem materiałów proceduralnych. Twarz pozostaje przy odziedziczonej teksturze o niższej rozdzielczości.
- Zwężono 312 rdzeni włosów, zachowano drobne włókna i wcześniejszą nasadę. Odrzucono eksperymenty tworzące regularną zasłonę.
- `FORGE-E19-8K.glb`: 64 211 024 B, SHA256 `f5196a7e6b822d50bbfdaa9d7f6051919b7d48a2e6a84fa5f3082cfc45c5e4f9`.
- `FORGE-E19-web.glb`: 27 521 620 B, SHA256 `08b88ea54b5046e579a9dab0e4f85342ffabdf3b9ed5932c3d49a00ec2b63cb4`, mapy ciała 2K. Późniejsza optymalizacja wymaga nowego raportu/hash-u.
- Ukończono sześć rzeczywistych widoków E19 po ponownym imporcie GLB oraz dodatkowe zbliżenie ciała z mastera 8K. Porównanie E18R/E19 korzysta ze wspólnych kamer i oświetlenia. [Manifest renderów](reviews/e19/final/render-verification.json) potwierdza hashe i rozdzielczości; podglądy nie są ilustracjami generatywnymi.

## Audyt i nierozwiązane sprawy

- Audyty wejściowego E18R i finalnego E19 są osobne. [Wizualny E19](reviews/e19/audit/E19-production-audit.json) ma 19 001 otwartych krawędzi, 47 116 krawędzi należących do więcej niż dwóch ścian oraz 124 634 trójkąty zdegenerowane po dokładnym połączeniu identycznych pozycji. Master nie jest gotową bryłą produkcyjną.
- Ukończono osobną kopię konstrukcyjną 200 mm: STL oraz ponownie importowany GLB mają 2 120 444 trójkąty, jedną połączoną składową i zero wykrytych błędów topologii krawędzi oraz degeneracji. [Raport STL](reviews/e19/print/print-STL-production-audit.json), [raport GLB](reviews/e19/print/print-GLB-production-audit.json) i [manifest końcowy](reviews/e19/print/print-final-delivery-manifest.json) dotyczą konkretnych finalnych plików.
- **Kopia konstrukcyjna została odrzucona wizualnie do sprzedaży:** poszarpane włosy, uproszczone rysy i uzębienie oraz niepotwierdzone podparcie tułowia. Brak kwalifikacji procesu, próbki fizycznej, pełnych pomiarów minimalnych grubości, przecięć i podpór. Jedna zamknięta składowa nie oznacza gotowego produktu. [Ograniczenia](reviews/e19/print/README-PRINT-E19.md).
- Dodatkowa izolowana próba wygładzenia włosów i piedestału również nie została przyjęta: wygląd nadal niewystarczający, wysokość 199,9386 mm poza założeniem 200 ±0,01 mm. Nie zastąpiła plików końcowych.
- Przeszło 20 testów Python metryk i reguły dopuszczenia oraz 20 testów Node formularza i pobierania plików. Testy Node używają kontrolowanego DOM, nie przeglądarkowego WebGL. Reguła dopuszczenia wiąże ocenę z hashem STL i po odrzuceniu wymaga naprawy; to moduł offline, jeszcze nie blokada zamówień wdrożona na Oracle.
- Meshy jest porównywany z dostarczonych screenshotów. Nie mamy jego eksportu do kontrolowanego benchmarku. Złożone postacie, wachlarz i szachownice mają oddzielne poziomy dowodów; nie ogłaszać rankingu ani zmyślonych procentów.
- Nadal niedoskonałe: podobieństwo twarzy, żywe oko, nos, profil czaszki i grupowanie włosów. 8K map ciała nie rozwiązuje tych braków.
- **Nie uruchomiono instalatora ani wdrożenia v35 na Oracle**: brak sesji SSH. Dopiero wynik instalacji właściciela i health potwierdzają wersję. Scalenie PR nie zmienia serwera.
- Publiczny FORGE Studio z E19 opublikowano jako **wersję 3**: https://forge-studio-public.terraformingplanet.chatgpt.site . Źródła: `fe05d7400b64fefd44736863d870174b5c00280e`; deployment `appgdep_6aa61c9f6c208191870473026181a2be` ma stan **succeeded**. Prywatnego Studio ani Oracle nie zaktualizowano.
- Julia w bluzie i Atlas z wcześniejszych zgłoszeń nadal wymagają swoich eksportów. E19 w sukni nie zastępuje tamtych modeli.
- Nie wykonano treningu wag Astra, treningu L4 ani nowej płatnej generacji API. Nie podłączono płatności, zamówień B2B ani produkcyjnego CAM/sterowania laserem.

Rendery, końcowy audyt i publikacja E19 są ukończone. Kopia konstrukcyjna pozostaje odrzucona do sprzedaży; moduł oceny procesu jest offline. Dowód publikacji: `docs/reviews/e19/publication-receipt.json` w repozytorium.

---

# Checkpointy historyczne — bieżący stan E19 i v35 opisano powyżej

## Stan końcowy wznowienia — 2026-09-13

Raport historycznego etapu E18R: [DELIVERY-2026-09-13.md](reviews/resume-2026-09-13/DELIVERY-2026-09-13.md).

- Kod v34 zweryfikowany w CI na commit `ad8844cd8d350c0af6939e1a0cda847dd87e3f9b`: 146 testów na każdej z wersji Python 3.9 i 3.12, rzeczywisty Blender/MCP/GLB/FBX, atlas i szachownice. [Run 34730631366](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34730631366) zakończony sukcesem.
- Wykonano rzeczywistą lokalną korektę E18R (nasada włosów i sheen czarnej sukni), ponowny import GLB i kontrolowane rendery przed/po. 6 354 061 trójkątów. Nie przebudowano twarzy, oczu, szyi ani sylwetki.
- Publiczny Site wersja 2 opublikowany: https://forge-studio-public.terraformingplanet.chatgpt.site . Commit źródeł `8d716ebcccc107b5c542ffac03d2c417d62e3f35`; deployment `appgdep_6aa5fd40babc8191a8ad6efe181a99a3` potwierdzony jako succeeded. Źródłowy E18 GLB oraz nowy E18R GLB są zachowane w Git i Site.
- **Nie zainstalowano v34 na Oracle** — brak aktywnej uwierzytelnionej sesji SSH. Przekazano paczkę i polecenie Cloud Shell; nie twierdzić, że serwer został zaktualizowany bez odczytu jego FROGE_V34_OK i health.
- **Nowe Julia/Atlas nie zostały przebudowane** — dostępne są zrzuty, referencja i rekord zlecenia; eksport aplikacji wymaga tożsamości właściciela (401). Do kontynuacji potrzebne są GLB/BLEND tych zleceń. Julia w bluzie nie jest E18 w sukni.
- Prywatny Site nadal wersja 47, klon HTTP500; nie zastąpiono go publicznym pokazem. Gate hosta odrzuca niekompletne dowody, ale cały komplet widoków/pomiarów nie powstaje jeszcze automatycznie.
- Nie uruchomiono L4, treningu wag ani płatnej nowej generacji. Wcześniejszy master/4K usunięty przez porządkowanie środowiska nie został odzyskany; wcześniejsze wzmianki o osobno dostępnych ciężkich masterach są historyczne.
- W tym historycznym checkpointcie PR #11 był draftem; później scalono go zgodnie z potwierdzeniem powyżej. Zachować wcześniejsze porównania Meshy jako ocenę ze screenów, nie nowy kontrolowany benchmark. Zachować notatki naukowe i ChessArena jako pamięć/testy projektu.


---

## Historyczne checkpointy

# E18 delivery checkpoint — 2026-09-12

Main candidate E18: 6,315,947 FBX triangles; 369/369 UV mesh objects; source SHA 28673fc400228a756d80128b89885ff7f0a017d857f517058cfb1bc689b7ffb6. Six actual reimport views and HQ 2048x2560 produced. Web GLB 23,161,896 bytes, 6,315,623 triangles; texture downsizing and export triangulation documented. Preserve E15/E16/E17 originals. Local model edits are separate from the generator runtime patch.

16 CPU regression tests passed. Blender 4.3.0 tests measured tagged 64/512-cell positive and negative fixtures. Actual runtime invokes evidence and board review; new module included in updater file allow-list. No new weights, L4 job, Oracle installation or full host acceptance integration. Visual likeness remains unfinished, including lower nose, eyelids and regular hair grouping.

Public showcase published: https://forge-studio-public.terraformingplanet.chatgpt.site . Canonical Site source aed971eae22d1c98f9ce061fd1d9a0522c875fe4. Contains public preview, optional 3D rotation, local brief/quote downloads, Queen model and 15s EN/PL trailer. No live supplier dispatch/payment. The existing private operator Studio was not modified.

PR #11 codex/e17-reference-fidelity-public-studio targets codex/v27-mcp-startup-audit. Keep as draft pending visual improvements and production host integration. Reports, comparisons and technical error memory in docs/reviews/e17; private ChessArena evidence in docs/training/e17.

A 646 MB local master archive exists. An attempted extra Google Drive backup was rejected by automatic approval review because the user did not specify that destination/payload; do not retry without explicit authorization. Public web copies and Git-backed source/comparisons are saved. Complete delivery coverage: docs/reviews/e17/TASK-COVERAGE.md.

## Prior checkpoint

# E17 active checkpoint

Main task: improve actual E16 hair/teeth/anatomy from supplied reference; model build pending from dedicated agent. Secondary Queen/fan rebuilt; video 15s produced and validated. Generator runtime changes pending integration, source literature and curated error catalog complete. Sources in docs/reviews/e17 and docs/training/e17; no full L4 training or Astra weights claimed. Private ChessArena PR115 provides QA training source but weights/results not recovered in reviewed tree. User's requested public client site is separate from operator studio; static source prepared under public-studio, Site ID appgprj_6aa5c12d4f4c81919545504d438b3ff3. Not deployed yet. Existing Sites clone failed with server HTTP500 three bounded attempts; private studio unchanged. No Oracle worker deployment. Artifact saving via Library unavailable this turn. Models/renders remain local until final handoff.


## Wznowienie 2026-09-13

Nowe zgłoszenia Julii w bluzie i figurki Atlas oraz stan wznowienia opisano w [checkpoint](reviews/resume-2026-09-13/RESUME-CHECKPOINT.md) i [analizie porównawczej](reviews/resume-2026-09-13/REFERENCE-CASES-2026-09-13.md). Ten etap nie potwierdza jeszcze instalacji na Oracle ani poprawienia nowych eksportów.
