# V27 — błąd instalacji i audyt repozytoriów

Zgłoszenie 2026-09-12: Oracle, Python 3.9, `MCP tool not advertised: []`,
jedno żądanie do lokalnej atrapy odpowiedzi, `turn.failed`, `FROGE_V26_ERROR`.
To awaria testu instalacyjnego, nie dowód błędu modelu 3D ani opłaty API.

## Dokładna przyczyna komunikatu ze zrzutu

Niezależne CI odtworzyło problem. Oficjalny klient dla Astry używa
Responses Lite: katalog znajduje się w `input[].additional_tools`, a pole
`tools` na głównym poziomie jest celowo pomijane. Test v26 błędnie uznawał
brak tego pola za brak MCP. Proxy dodatkowo gubiło nagłówek
`x-openai-internal-codex-responses-lite` potrzebny do interpretacji formatu.
V27 odczytuje oba formaty i zachowuje ten nagłówek oraz oryginalny katalog.

## Dodatkowe potwierdzone błędy kodu v26

- Uruchamianie wyłączało `code_mode_host`, choć oficjalny katalog CLI
  0.154.0 dla `gpt-6-astra` definiuje `tool_mode: code_mode_only`.
  V27 jawnie utrzymuje tryb kodowy i instaluje jego osobny host.
- Instalator pobierał tylko `codex`, bez osobnego `codex-code-mode-host`.
- Test szukał bezpośredniej funkcji w płaskim `tools`; Code Mode używa
  `custom_tool_call` do `exec`, a funkcje MCP są dostępne wewnątrz niego.
  Schematy mogą również być zawinięte w namespace.
- Zapis diagnostyki pomijał treść zdarzeń `error`/`turn.failed` i ostrzeżenia.
- Wycofanie kodu po błędzie eksportu nie przywracało poprzedniego
  `verified.json`, co mogło wyłączyć wcześniej sprawdzony silnik.

Szczegóły błędu startowego były usuwane przez stary filtr. Poprawka wymaga
sprawdzenia całego połączenia przed akceptacją; nie pomija nieudanego testu.

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
Niezależny [test GitHub CI](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34661987718)
przeszedł na Pythonie 3.9 i 3.12: po 21 testów regresji oraz rzeczywisty obieg
Codex -> Code Mode -> Blender MCP -> wynik. Potwierdzono sześć narzędzi i
odpowiedź get_current_model. Testowany kod: `3ca6201b4c357ddb4b01e6c0516305f58cc1164a`.
Dodatkowo 65 testów UI/API/promptów strony i kontrola typów przeszły.
Nie wykonano nowej płatnej generacji ani pomiaru podobieństwa/szybkości.

## Źródła

- [OpenAI: MCP w Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [OpenAI: zdarzenia trybu nieinteraktywnego](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Oficjalny katalog CLI 0.154.0](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/models-manager/models.json)
- [Oficjalne testy Code Mode / MCP](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/core/tests/suite/code_mode.rs)
- [Wydanie i program Code Mode host](https://github.com/openai/codex/releases/tag/rust-v0.154.0)
