# Froge MPC 2 test

Prywatna baza rozwoju sklepu TikTok Shop i studia modeli 3D na zamówienie, oparta na projekcie konkursowym **ForgeMCP — Multi-Agent Research & Game Studio**.

## Aktualny priorytet

Klient opisuje figurkę lub część → powstaje model 3D i podgląd → klient zatwierdza projekt → wykonawca B2B potwierdza możliwość produkcji, cenę i termin → produkcja → wysyłka → śledzenie zamówienia.

TikTok Shop ma być kanałem sprzedaży. Docelowy zasięg jest światowy, wdrażany etapami po weryfikacji obsługiwanych rynków, dostawców i dostawy. Zakres obejmuje też dropshipping gotowych produktów, w tym rozważaną klawiaturę „Codex Micro”; producent, dostępność i warunki współpracy pozostają do potwierdzenia.

**Stan tej kopii:** przeniesiony kod i dokumentacja; brak podłączonego TikTok Shop, płatności, dostawcy generatywnych modeli 3D i wykonawcy produkcji. Istniejący generator jest proceduralny i obsługuje określone kształty. Sam eksport glTF nie potwierdza przydatności modelu do druku lub produkcji.

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
| Proceduralne kształty | Deterministyczne presety | Podłączenie generowania AI dla swobodnych opisów |
| Szkice produktów i zapytań B2B | Lokalne szkice Shopify/B2B | Osobny adapter TikTok Shop i rzeczywiści wykonawcy |
| Koordynator i narzędzia WebMCP | Skopiowane z ForgeMCP | Zadania ofert, modeli, zamówień i wysyłek |
| Zamówienia, płatności, produkcja | Integracje niepodłączone | Integracja, weryfikacja i test pełnego przebiegu |

## Uruchomienie

```bash
npm ci
npm run dev
```

Istniejące laboratorium modeli i szkiców handlowych: `/#/shop-lab`. Interfejs zachowuje wygląd oraz nazwy konkursowego ForgeMCP; przebudowa pod TikTok jest następnym etapem.

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Oryginalne workflow GitHub Actions zapisano jako nieaktywne pliki w `docs/foundation/workflows/`, a powiązanie z poprzednią stroną jako `docs/foundation/hosting.original.json`. Ta kopia nie uruchamia automatycznie publikacji ani starego zadania Codex. Źródłowe `netlify.toml` zachowano jako konfigurację bazową; nowego wdrożenia nie utworzono.

Licencja odziedziczonego kodu: [MIT](LICENSE). [Informacje o komponentach zewnętrznych](THIRD_PARTY_NOTICES.md).
