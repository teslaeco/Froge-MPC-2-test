# Froge MPC 2 test

Prywatna baza rozwoju sklepu TikTok Shop i studia modeli 3D na zamówienie, oparta na projekcie konkursowym **ForgeMCP — Multi-Agent Research & Game Studio**.

## Aktualny priorytet

Klient opisuje figurkę lub część → powstaje model 3D i podgląd → klient zatwierdza projekt → wykonawca B2B potwierdza możliwość produkcji, cenę i termin → produkcja → wysyłka → śledzenie zamówienia.

TikTok Shop ma być kanałem sprzedaży. Docelowy zasięg jest światowy, wdrażany etapami po weryfikacji obsługiwanych rynków, dostawców i dostawy. Zakres obejmuje też dropshipping gotowych produktów, w tym rozważaną klawiaturę „Codex Micro”; producent, dostępność i warunki współpracy pozostają do potwierdzenia.

**Stan tej kopii:** studio Codex + Blender, bez płatnego generatora i kluczy API. Strona przyjmuje geometrię od agenta WebMCP lub import GLB/JSON, daje podgląd i eksport. Do pobrania jest autorski dodatek Blender z importem modeli i opcjonalnym generowaniem przez lokalne Ollama. Przygotowano rzeczywisty model smoka: 94 części, 36 960 trójkątów i tekstury proceduralne. Wymiary i obroty są opcjonalne. Strona nie uruchamia samoczynnie Codexa, Blendera ani lokalnego modelu. Dodatek wymaga uruchomienia na komputerze; nie został jeszcze sprawdzony w rzeczywistym Blenderze.

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
