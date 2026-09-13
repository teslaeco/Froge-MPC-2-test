# Froge MPC 2 test

Prywatna baza rozwoju sklepu TikTok Shop i studia modeli 3D na zamówienie, oparta na projekcie konkursowym **ForgeMCP — Multi-Agent Research & Game Studio**.

## Wznowienie 13 września — jakość modelu i Oracle v34

Nowa Julia w bluzie i figurka Atlas pokazały istotne niedopasowanie geometrii oraz materiałów. [Porównanie wejściowych przypadków](docs/reviews/resume-2026-09-13/REFERENCE-CASES-2026-09-13.md) rozdziela obserwacje ze screenów od pomiarów pliku 3D. E18 w sukni pozostaje osobnym modelem.

Poprawka v34 obejmuje kompilację edycji przed zużyciem próby Blendera, faktyczne przypisania atlasu głowy, jednoznaczną historię kandydatów oraz ocenę hosta związaną ze skrótami aktualnego eksportu i referencji. Oko w kostnej połowie jest wymagane, gdy pokazuje je bieżąca referencja; pusty oczodół nie jest domyślnym wymaganiem dla każdej czaszki. Więcej trójkątów nie zastępuje właściwego kształtu.

[Instrukcja wykonania i kryteria](docs/reviews/v34/POLECENIE-CODEX.txt) oraz testy są pamięcią projektu. Nie są treningiem wag ani uruchomieniem GPU L4. Meshy w dostarczonych próbach daje lepsze podobieństwo twarzy; Blender i agent pozwalają lokalnie edytować oraz sprawdzać geometrię. Nie wyciągamy ogólnego rankingu z różnych kamer i oświetlenia.

**Wdrożenie:** źródła i paczka aktualizacji nie oznaczają instalacji. Dopiero `FROGE_V34_OK` oraz stan Oracle z `connectorVersion=34`, `referenceAcceptanceRevision=1` i `workerRelease=v34-reference-acceptance` potwierdzają instalację. Aktualny status pracy: [checkpoint](docs/WORK_CHECKPOINT.md). Publiczny [podgląd FORGE](https://forge-studio-public.terraformingplanet.chatgpt.site) przedstawia modele robocze; nie uruchamia płatnego generowania ani zamówień B2B.

## Aktualny priorytet

Klient opisuje figurkę lub część → powstaje model 3D i podgląd → klient zatwierdza projekt → wykonawca B2B potwierdza możliwość produkcji, cenę i termin → produkcja → wysyłka → śledzenie zamówienia.

TikTok Shop ma być kanałem sprzedaży. Docelowy zasięg jest światowy, wdrażany etapami po weryfikacji obsługiwanych rynków, dostawców i dostawy. Zakres obejmuje też dropshipping gotowych produktów, w tym rozważaną klawiaturę „Codex Micro”; producent, dostępność i warunki współpracy pozostają do potwierdzenia.

**Historyczny opis startowej kopii (późniejsze etapy powyżej i w checkpoint):** studio Codex + Blender, bez płatnego generatora i kluczy API. Strona przyjmuje geometrię od agenta WebMCP lub import GLB/JSON, daje podgląd i eksport. Do pobrania jest autorski dodatek Blender z importem modeli i opcjonalnym generowaniem przez lokalne Ollama. Przygotowano rzeczywisty model smoka: 94 części, 36 960 trójkątów i tekstury proceduralne. Wymiary i obroty są opcjonalne. Strona nie uruchamia samoczynnie Codexa, Blendera ani lokalnego modelu. Dodatek wymaga uruchomienia na komputerze; nie został jeszcze sprawdzony w rzeczywistym Blenderze.

## Fundament konkursowy

- [Oryginalna treść opisu Devpost](docs/foundation/DEVPOST_DESCRIPTION.md)
- [Metadane projektu Devpost i odnośniki](docs/foundation/devpost-project.json)
- [Oryginalny README ForgeMCP](docs/foundation/UPSTREAM_README.md)
- [Źródło, sposób kopiowania i granice archiwum](docs/foundation/PROVENANCE.md)
- [Plan TikTok Shop i modeli 3D](docs/TIKTOK_3D_ROADMAP.md)

Kod aplikacji, testy, zasoby, licencja i informacje o autorach pochodzą z repozytorium konkursowego, z commita `bf18b297ff49a510c69578c98ece0d2224d34a44`. Zachowano moduły Terra i Cube jako część fundamentu; bieżący rozwój skupia się na handlu oraz modelach 3D.

Treść Devpost jest kopią aktualnego, edytowalnego projektu pobraną podczas importu, a nie gwarantowanym obrazem zgłoszenia z chwili upływu terminu konkursu. Twierdzenia w opisie konkursowym pozostają historycznym opisem autora; sam import nie jest ich ponownym audytem.

## Co można wykorzystać

| Element | Obecny stan | Dalsza praca |
| --- | --- | --- |
| Podgląd modeli i eksport glTF/PNG | Kod skopiowany z Product Lab | Figurki, części i nowe formaty eksportu |
| Modelowanie agentowe | Dowolne siatki WebMCP, import GLB/JSON, dodatek Blender | Uruchomienie dodatku i lokalnego AI na komputerze użytkownika |
| Szkice produktów i zapytań B2B | Lokalne szkice Shopify/B2B | Osobny adapter TikTok Shop i rzeczywiści wykonawcy |
| Koordynator i narzędzia WebMCP | Skopiowane z ForgeMCP | Zadania ofert, modeli, zamówień i wysyłek |
| Zamówienia, płatności, produkcja | Integracje niepodłączone | Integracja, weryfikacja i test pełnego przebiegu |

## Uruchomienie

```bash
npm ci
npm run dev
```

Strona główna `/#/` otwiera studio Codex + Blender. Można otworzyć gotowy projekt smoka, pobrać scenę do Blendera, zaimportować GLB/JSON, opcjonalnie zmienić wymiary i pobrać GLB/STL. Polecenie tekstowe przygotowuje żądanie dla agenta; samo kliknięcie nie wywołuje LLM. Agent korzysta z `get_3d_modeling_request`, `get_3d_scene_schema` i `apply_3d_model_scene`. Gdy agent nie ma dostępu do strony, użytkownik przenosi przygotowany model przez plik.

Dodatek do Blendera znajduje się w `blender_addon/froge_studio`. Obsługuje dane geometrii oraz lokalne Ollama pod `127.0.0.1:11434`. Model lokalny wybiera użytkownik spośród zainstalowanych modeli; dodatek nie pobiera modeli ani nie korzysta z chmury. Nie wykonuje kodu zwróconego przez AI.

`npm run dev` uruchamia interfejs. `npm run build` wymaga Node i Python 3 (wyłącznie biblioteka standardowa), generuje model i ZIP dodatku, następnie buduje Vite i Worker. Nie wymaga instalacji Blendera. Stare trasy płatnego API odpowiadają 410 i nie wykonują połączeń z dostawcą.

Dawna strona konkursowa: `/#/contest`. Laboratorium modeli i szkiców handlowych: `/#/shop-lab`. Szczegóły: [Studio 3D](docs/STUDIO_3D.md).

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Oryginalne workflow GitHub Actions zapisano jako nieaktywne pliki w `docs/foundation/workflows/`, a powiązanie z poprzednią stroną jako `docs/foundation/hosting.original.json`. Ta kopia nie uruchamia automatycznie publikacji ani starego zadania Codex. Źródłowe `netlify.toml` zachowano jako konfigurację bazową; aktualna wersja jest przeznaczona dla prywatnej strony Sites wskazanej w `.openai/hosting.json`.

Licencja odziedziczonego kodu: [MIT](LICENSE). [Informacje o komponentach zewnętrznych](THIRD_PARTY_NOTICES.md).

## Katalog i sprzedaż

Panel `/shop`: trwały katalog, prywatne pliki 3D, wycena, szkice Shopify CSV, opisy TikTok i zapytania B2B. Model ze studia można zapisać bezpośrednio jako produkt. Kanały sprzedaży i zdalny Blender wymagają konfiguracji; panel nie udaje aktywnej sprzedaży. Szczegóły: [docs/COMMERCE.md](docs/COMMERCE.md).


## Reference-driven 3D reconstruction — E18 working result

FORGE combines reference analysis, editable Blender scenes and repeatable export checks. We are developing a workflow for game assets and custom objects such as chess sets, globes and decorative tableware. The public experience is intended to remain simple: describe an object, inspect a preview and prepare a manufacturing enquiry.

Our current character study exposes a real limitation: **the supplied Meshy result follows the reference more closely than our E15/E16 model**, especially around the eyes, smile, hair roots and clothing. Meshy is a strong complementary tool. Our approach adds explicit constraints, named editable parts, local repairs and repeatable checks; those capabilities do not by themselves establish better visual quality.

Sebastian also reported an earlier example where our workflow followed the geometry of a fan more accurately. That observation is retained as a regression case to reproduce, not presented as a measured general advantage. The goal is to combine useful approaches and improve the outcome for the artist.

E17 introduced thinner hair, 3,920 geometric fibres, local tooth-crown adjustments and small torso/garment relief changes. E18 adds 440 root fibres, reshapes the orbital region, recesses the skeletal eye, refines the cheek/jaw and narrows the open region under the teeth. Its re-imported FBX contains 6,315,947 triangles and 369 UV-mapped mesh objects, with no missing active texture images in the reported import. The edits are visible, but hair grouping, eyelids, the lower nose and mouth transitions still require work. E18 is not accepted as a faithful or production-ready reconstruction.

The reference remains the authority for visible features. The newly requested grey hair on the skeletal side is a deliberate art-direction change; it must not be scored as exact colour reproduction of the earlier brown-haired reference. Procedural skin pores exist only in the Blender master; they were not baked for FBX/GLB. The preserved global head proportions avoid the rejected R15 enlargement. E18 contains local skeletal edits, but it does not reconstruct the complete skull or rebuild the living eyelids.

![Meshy screenshot and actual E16/E18 model evidence](docs/reviews/e17/assets/final-comparison.webp)

![E18 front, left profile and back from the re-imported FBX](docs/reviews/e17/assets/e18-views.webp)

Our learning record stores failures, preferred revisions, reference requirements and acceptance checks. This is **application memory and evaluation work**, not a claim that the weights of OpenAI's Astra model have been retrained. OpenAI's documentation distinguishes evaluation, prompt improvements and fine-tuning as separate activities. [OpenAI model optimization](https://developers.openai.com/api/docs/guides/model-optimization)

The generator patch adds reconstruction instructions to the planner and emits reference-review evidence from the worker. It binds model, reference and review-image hashes, with an explicit refresh command after new evidence is supplied. It also measures tagged 8×8 and 8×8×8 board geometry and eligible flat material colours. Sixteen CPU regression tests and real Blender checks on 64/512-cell fixtures are reported; wrong materials and missing cells are detected. These tests do not measure facial likeness or texture pixels. Independent visual evidence still requires a reviewer, and the anatomy gate covers a single character. [Workflow review](docs/reviews/e17/GENERATOR-REVIEW.md)

See [the visual comparison](docs/reviews/e17/COMPARISON-E17.md), [the reconstruction prompt](docs/reviews/e17/PROMPT-E17.md), [the error catalogue](docs/reviews/e17/error-catalog.json), [the production workflow](docs/reviews/e17/PRODUCTION-WORKFLOW.md) and [comparison provenance](docs/reviews/e17/comparison-manifest.json). Model availability, tests actually run and remaining defects must be read with the accompanying artifact report. A saved export or a higher polygon count does not constitute visual acceptance, animation readiness or manufacturing approval.

The intended B2B workflow quotes material usage, colours, manufacturing process and finishing before an order is accepted. A preview and a quote form are not a claim that payment, supplier assignment or physical fulfilment is already operating.


Public preview: [FORGE Studio](https://forge-studio-public.terraformingplanet.chatgpt.site). [Request coverage](docs/reviews/e17/TASK-COVERAGE.md).
