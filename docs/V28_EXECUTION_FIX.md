# FORGE v28 — wykonanie zadania i raporty błędów

## Co potwierdzono

Użytkownik potwierdził instalację v27 zrzutem FROGE_V27_OK.
Kolejne zlecenie ce122db3-2957-41da-89a5-993aa662a379 (2026-09-12 01:20:55 UTC)
nie zapisało modelu: 160 s, 12 zapytań, 2412 tokenów odpowiedzi i rozumowania,
Blender 0 s. Stan failed i brak artefaktu potwierdzono w bazie strony.
Kod v27 sam zwracał HTTP 429 po lokalnym limicie 12 zapytań. Nie zapisywał
tej przyczyny; użytkownik widział ogólny błąd Codexa zamiast źródła limitu.

Nie uzyskano dostępu do prywatnego pełnego logu Oracle: odczyt API wymaga
normalnego logowania użytkownika. Dokładny powód dwunastu decyzji Astry
przed pierwszą budową pozostaje niepotwierdzony. Nie przypisujemy go bez
logów brakowi kredytów ani jednej konkretnej instrukcji.

## Naprawy

- Lokalny limit ma własny kod FORGE_JOB_BUDGET i terminalny status 422.
  Limit pozostaje 12 zapytań, 36000 tokenów oraz 900 sekund.
- Błędy OpenAI zachowują kod, źródło, status HTTP i Retry-After. Błąd
  kredytów/rozliczeń nie uruchamia automatycznie kolejnych prób.
- Błąd argumentów MCP zachowuje identyfikator wywołania i szczegół do
  poprawienia. Wcześniej odpowiedź z id=null gubiła powiązanie z żądaniem.
- finish_model z issues=[] przechodzi właściwą walidację: dodano brakujące
  minItems. Wcześniejszy test JobTools.call omijał walidację transportu.
- Trzy identyczne kolejne błędy narzędzia zatrzymują pętlę przed kolejnym API.
- Instrukcja wskazuje dokładne nazwy narzędzi w Code Mode, await/text i
  przekazywanie rzeczywistych renderów jako obrazów. Kilka ujęć można pobrać
  w jednym wywołaniu zamiast zużywać osobną turę API na każde.
- Raport rozróżnia brak modelu od istniejącego szkicu i pokazuje rzeczywisty
  przebieg MCP, bez zapisu zdjęć, rozumowania i argumentów narzędzi.
- Instalator wymaga teraz prawdziwego Codex → Code Mode → MCP → Blender →
  GLB → obrazy renderów → FBX, a nie tylko odczytu stanu połączenia.
  Odpowiedzi AI są kontrolne; ten test nie kupuje generacji.
- Produkcyjny Blender nadal działa w dotychczasowym kontenerze. Adapter
  lokalnego Blendera istnieje wyłącznie do CI i nie wchodzi do instalatora.

## Paczki nie były identyczne

| Wersja | Bajty ZIP | SHA-256 |
| --- | ---: | --- |
| v26 | 15532639 | 44ad43131c6aa5cb0ebcd55cee5da21daef3463eae5f32bdbdb36213ced5df6d |
| v27 | 15536825 | 836205fc9738841037101de0bf903ba03b51fcee10c7ba4565b0ef635d3e46c9 |

Różnica: 4186 bajtów. Większość paczki to zachowane zasoby geometrii i
tekstur. Wielkość ZIP-a nie jest pomiarem jakości ani zakresu poprawki.
Oryginalne paczki zachowano.

## Weryfikacja i ograniczenia

Pierwszy pełny test CI na 193d2fff88b8c34d723202f469c7ab94af720f44 przeszedł:
https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34665550799
Python 3.9 wykonał rzeczywisty model, trzy ujęcia i FBX przez oficjalny Codex
0.154.0 i Blender 4.3.0. Python 3.12: transport MCP i regresje. Ostateczna
weryfikacja wydania zostanie zapisana w docs/reviews/v28/verification.json.

Nie wykonano nowej płatnej generacji zdjęcia, pomiaru podobieństwa ani
porównania szybkości generacji przez Astrę. Test kontrolny nie jest takim
pomiarem. Oracle v28 wymaga uruchomienia instalatora przez użytkownika.

Repozytorium: PR #10 jest wersją roboczą opartą o gałąź PR #8. PR #9 był
scalony do tej gałęzi, nie do main. Nie scalamy automatycznie starych PR.

Dokumentacja OpenAI dotycząca różnych przyczyn HTTP 429:
https://developers.openai.com/api/docs/guides/error-codes
Dokumentacja Codexa i MCP:
https://learn.chatgpt.com/docs/extend/mcp?surface=cli
