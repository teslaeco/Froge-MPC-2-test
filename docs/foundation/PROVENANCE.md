# Pochodzenie fundamentu

## Kod

- Repozytorium źródłowe: https://github.com/Terraforming-Planet/ForgeMCP-Multi-Agent-Research---Game-Studio
- Skopiowany commit: `bf18b297ff49a510c69578c98ece0d2224d34a44` z gałęzi `main`.
- Repozytorium docelowe: https://github.com/teslaeco/Froge-MPC-2-test
- Skopiowano wszystkie 164 pliki śledzone przez Git w tym commicie. Jest to kopia drzewa plików; nie przeniesiono pełnej historii Git, issues, PR, sekretów konta ani ustawień wdrożeń.
- [Manifest](source-manifest.json) zawiera mapowanie ścieżek i sumy SHA-256 każdego pliku źródłowego.

Pliki aplikacji pozostają niezmienione. Oryginalny README przeniesiono do `UPSTREAM_README.md`, aby nowy README mógł opisywać bieżący zakres. Cztery workflow zachowano bajt w bajt w `workflows/` z rozszerzeniem `.disabled`; nie testują przypadkowo starej witryny ani nie uruchamiają jej publikacji i zadania Codex. Oryginalny `.openai/hosting.json` zachowano jako `hosting.original.json`, aby kopia nie wskazywała aktywnie na istniejącą stronę konkursową.

Odnośniki do Terra, Cube i dawnego wdrożenia wewnątrz skopiowanego kodu pozostają oryginalnymi odnośnikami. Aplikacja testowa nie została jeszcze przekierowana na nowe usługi.

## Projekt Devpost

- Projekt: https://devpost.com/software/forgemcp-multi-agent-research-game-studio
- Identyfikator: `1416148`.
- Konkurs: The WebMCP Challenge, https://webmcp.devpost.com/
- Film: https://www.youtube.com/shorts/wepGsmTqDQQ
- API zwróciło stan `published` oraz datę zgłoszenia `2026-09-03T21:01:17.477-04:00`.
- Data ostatniej aktualizacji pobranego projektu: `2026-09-05T07:11:09.544-04:00`.

`DEVPOST_DESCRIPTION.md` zachowuje treść pola `description`; `devpost-project.json` zachowuje dostępne metadane, tagline, daty i odnośniki. Narzędzie zwraca żywy, edytowalny projekt, nie zamrożony stan zgłoszenia. Nie pobrano zdjęć/miniatury, odpowiedzi na dodatkowe pytania zgłoszeniowe ani nieudostępnionych pól takich jak pełna lista „Built with”.

Nie zmieniano oryginalnego zgłoszenia Devpost ani źródłowego repozytorium. Nowy plan TikTok/3D jest oddzielnym kierunkiem rozwoju po skopiowaniu fundamentu.
