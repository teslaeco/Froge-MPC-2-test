# V27 — błąd instalacji i audyt repozytoriów

Zgłoszenie 2026-09-12: Oracle, Python 3.9, `MCP tool not advertised: []`,
jedno żądanie do lokalnej atrapy odpowiedzi, `turn.failed`, `FROGE_V26_ERROR`.
To awaria testu instalacyjnego, nie dowód błędu modelu 3D ani opłaty API.

## Potwierdzone błędy kodu v26

- Uruchamianie wyłączało `code_mode_host`, choć oficjalny katalog CLI
  0.154.0 dla `gpt-6-astra` definiuje `tool_mode: code_mode_only`.
  Pusta odpowiedź lokalnego `/models` dodatkowo nie powinna decydować o
  dostępności podstawowego narzędzia przy nowej instalacji i pustym cache.
- Instalator pobierał tylko `codex`, bez osobnego `codex-code-mode-host`.
- Test szukał bezpośredniej funkcji w płaskim `tools`; Code Mode używa
  `custom_tool_call` do `exec`, a funkcje MCP są dostępne wewnątrz niego.
  Schematy mogą również być zawinięte w namespace.
- Zapis diagnostyki pomijał treść zdarzeń `error`/`turn.failed` i ostrzeżenia.
- Wycofanie kodu po błędzie eksportu nie przywracało poprzedniego
  `verified.json`, co mogło wyłączyć wcześniej sprawdzony silnik.

Samo zdjęcie nie rozstrzyga wszystkich wewnętrznych przyczyn pustego katalogu;
szczegóły błędu startowego były usuwane przez stary filtr. Poprawka usuwa
potwierdzone braki i wymaga sprawdzenia całego połączenia przed akceptacją.

## Zmiany

V27 instaluje oba oficjalne programy 0.154.0 z kontrolą SHA256 dla x86_64 i
ARM64. Jawnie włącza Code Mode Only i jego host, zachowując izolację,
wyłączenie powłoki i zewnętrznych narzędzi. Atrapa modelu zleca rzeczywiste
wywołanie `get_current_model`. Test wymaga wyniku z właściwym identyfikatorem,
sześciu narzędzi i faktycznego pustego stanu modelu. Sam tekst/error nie przechodzi.
Brak `exec` blokuje żądanie przed API. Kod i potwierdzenie weryfikacji są
przywracane przy nieudanej aktualizacji; modele i klucze pozostają zachowane.
Diagnostyka bez sekretów pozostaje na Oracle po rollbacku.

## Repozytoria i PR

| Element | Potwierdzony stan przed v27 |
|---|---|
| Opublikowana strona | Sites 42, źródło `f41e4fb300c96c5b0b5f56a918ac4a1bc44aae93` |
| Repozytorium Sites | main `a29689ebce64cb4bd4b050b598416fe2813d9bab`, zawiera v26 |
| GitHub main | `bac2827fc1ec31e71dc0f5c586df43c507338725`, starszy kod |
| PR #9 | scalony 11.09 o 20:47 UTC do `codex/reference-fidelity-4k-8k` |
| PR #8 | otwarty draft do main; head `d4e7af532cde4e7bd8ab5efc4fece2fef55adef3`, 30 commitów przed main |
| PR #6 / #7 | otwarte starsze zmiany; nie scalono ich automatycznie |
| CI PR #9 | brak statusów i workflow runs; nie oznacza zielonych testów |
| Review PR #9 | brak wątków uwag w API |

Scalenie PR #9 nie aktualizowało GitHub main ani instalacji Oracle.
Nie należy traktować v26 opublikowanej strony jako dowodu aktualizacji serwera.
Nowy PR synchronizuje bieżący worker ze źródła Sites i dodaje test CI
Codex–MCP na Pythonie 3.9 i 3.12 bez sekretów ani płatnego API.
Starsze PR pozostają do osobnego przeglądu, bez utraty ich historii.

## Weryfikacja i granice

Wyniki wykonanych testów i SHA paczki: `reviews/v27/verification.json`.
Host Code Mode pobrano, zweryfikowano i uruchomiono lokalnie (`--help`).
Pełny CLI w zagnieżdżonym środowisku nadal zatrzymuje się przed pierwszym
żądaniem i nie ukończył testu. Nie obchodzono izolacji. Ten sam test na Oracle
pozostaje obowiązkowy; wymagane `CODEX_MCP_REAL_CLI_ROUNDTRIP_OK` i `FROGE_V27_OK`.
Nie wykonano nowej płatnej generacji ani pomiaru podobieństwa/szybkości.

## Źródła

- [OpenAI: MCP w Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [OpenAI: zdarzenia trybu nieinteraktywnego](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Oficjalny katalog CLI 0.154.0](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/models-manager/models.json)
- [Oficjalne testy Code Mode / MCP](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/core/tests/suite/code_mode.rs)
- [Wydanie i program Code Mode host](https://github.com/openai/codex/releases/tag/rust-v0.154.0)
