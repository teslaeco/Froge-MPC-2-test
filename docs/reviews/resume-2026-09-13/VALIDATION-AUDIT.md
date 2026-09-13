# Wznowienie: walidacja atlasu i edycji — 2026-09-13

Baza zmian: PR #11, `01bf1d05ed72eb4e9da48d513d5b34a1a71e34f2`. Baza gałęzi Oracle `codex/v27-mcp-startup-audit`: `5c02f9ff1243b88876fef2631346c480a70cfffa`. Pliki `AGENTS.md` i `docs/WORK_CHECKPOINT.md` przeczytane. Żadnych zmian zdalnych ani wdrożenia nie wykonano w tym podzadaniu.

## Potwierdzone problemy w kodzie

1. `code_policy.validate_code` sprawdzał AST, ale nie wykonywał kompilacji. `ast.parse('return 1')`, `break`, `continue` lub `yield` poza właściwym kontekstem przechodzą parsowanie i zawodzą dopiero w `compile` wykonywanym przez Blender. Poprawka kompiluje już sprawdzone AST bez jego wykonywania, przed zużyciem próby budowy.
2. `portrait.verify_components` czytał tylko `obj.data.materials` i bezpośrednie węzły obrazów. Pomijał nadpisanie materiału na poziomie obiektu oraz atlas w grupie węzłów. Poprawka odczytuje efektywne sloty obiektu i przegląda zagnieżdżone grupy z limitem oraz ochroną przed cyklem.
3. Komunikat `skin_atlas` nie pokazywał faktycznego materiału ani rozdzielczości; transmisja MCP usuwała nawet `minimum_edge`. Teraz przekazuje wymagane 2048 px, największą krótszą krawędź przypisanego obrazu, nazwy materiałów i obrazów oraz zakres kontroli. Zgodne liczniki głowy/oczu/dłoni/paznokci nie oznaczają poprawnego atlasu.
4. Edycje mogą używać `make_material(pattern='skin')`, lecz funkcja tworzy ogólną mapę 512 px. Taka mapa nie zastępuje anatomii ani atlasu referencyjnego. Kontrakt i diagnostyka nakazują zachowanie istniejącego atlasu oraz UV, a dla osobnej stylizacji kopię przypisanego materiału. Nie zmniejszono progu walidacji i nie zwiększono sztucznie rozmiaru szumu.
5. Log nie rozróżniał numeru nieudanego kandydata od rewizji zachowanego modelu. Każdy wpis ma teraz `build_attempts` i `attempt`; to drugie zawiera numer rzeczywiście uruchomionej budowy lub `null` dla błędu preflight. `revision` nadal wskazuje zachowany model. Historyczne wpisy bez tych danych pozostają niejednoznaczne.

## Sprawdzenie

- `python -m unittest test_validation_preflight -v`: **6 testów CPU**, wszystkie przeszły. Obejmują prawdziwy handler MCP/stdin, poprawną naprawę po SyntaxError, zachowanie modelu/review/revision/budżetu oraz numer nieudanego kandydata.
- Blender 4.3.0, `verify_skin_atlas_runtime.py`: **6 przypadków**, wszystkie przeszły. Rzeczywiste mesh, sloty materiałów i obrazy: atlas istniejący globalnie, lecz nieprzypisany; poprawne/niepoprawne nadpisanie materiału obiektu; grupa węzłów; obraz 4096×1024; kopia zachowująca atlas.
- Pełny raport natywnego testu: `verification/verification.json`. Dane fixture nie są wynikiem generacji użytkownika i nie mierzą podobieństwa twarzy.

## Granice ustaleń

Nie odzyskano `scene.json`, `edits.py` ani `anatomy-failure.json` konkretnego nowego zlecenia Julia. Zrzut ekranu nie ustala, który z opisanych wariantów wystąpił. Zwykły błąd składni typu `invalid syntax` był już odrzucany przez AST; nowa kompilacja naprawia dodatkową lukę błędów kontekstu, nie jest dowodem przyczyny tego zlecenia.

Kontrola atlasu potwierdza przypisanie i rozdzielczość obrazu w materiałach. Nie jest weryfikacją użycia kanału koloru w każdej gałęzi shadera, poprawności pikseli, UV ani podobieństwa do fotografii. To samo dotyczy przenośności grup shaderów do FBX/GLB.

Odtworzono do `resume-integration` 146 plików bazowych z dokładnie zgodnymi Git blob SHA, w tym 138 plików tekstowych Oracle i `anatomy.json.gz`. Brakuje czterech oryginalnych PNG >1 MB, których dostępne GitHub narzędzia nie zwróciły jako bajtów: female-skin, male-skin, cotton-jersey-albedo i indigo-denim-albedo. Nie utworzono zamienników. Pełny wymagany gate powinien działać na GitHub checkout z oryginalnymi zasobami. Braki i hashe zapisano w `resume-integration/source-restore-verification.json` oraz `source-restore-manifest.json`.

Lista pięciu zmienionych/nowych plików oraz SHA-256: `change-manifest.json`. Poprawka jest również skopiowana do katalogu integracyjnego. Nie zmieniano `run.py`, `reference_reconstruction.py` ani plików hosta równolegle poprawianych przez drugiego agenta.
