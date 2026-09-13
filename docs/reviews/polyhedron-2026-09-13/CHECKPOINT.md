# Porównanie osiemnastościanu — checkpoint 2026-09-13

- Zadanie: ocenić referencję Sebastiana i dwa wyniki (FORGE: Codex + Astra + Blender MCP; Meshy 7), zapisać raport w GitHub i na istniejącej stronie, scalić PR po zielonych sprawdzeniach.
- Źródło robocze: `teslaeco/Froge-MPC-2-test`, `codex/v27-mcp-startup-audit`, commit `23a7b5859f6093073bedeb037b2ba0e75b142c7b`. Gałąź raportu: `codex/polyhedron-comparison-2026-09-13`. `main` zawiera starszy kod.
- Odczytano AGENTS.md, bieżący WORK_CHECKPOINT i drzewo plików. W przejrzanym drzewie nie ma eksportów tego osiemnastościanu.
- Pięć dostarczonych PNG istnieje; zapisano w analizie ich rozmiary i SHA-256. Nie zmieniano obrazu referencji ani zrzutów.
- Prywatny Site `appgprj_6a9c7f472a208191aaae6df3fe3423bf`: wersja 47, źródło `e3d60697db43744f6c09157328560c66a031f9a2`, wdrożenie `appgdep_6aa4d7f7538c81918ba273fb23acab3e` potwierdzone jako succeeded. Dostęp właścicielski zachowany.
- Wstępna obserwacja: FORGE ma prostsze i równiejsze widoczne pręty; Meshy ma pofalowane krawędzie i zgrubienia węzłów. To ocena ekranowa jednego przypadku.
- Nie potwierdzono liczby ścian, planarity, zamknięcia siatki, druku ani pełnej zgodności. Komunikat FORGE mówi o roboczym wyniku i błędach / nieukończonej ocenie.
- Następne kroki: zebrać dostępne metadane zlecenia, zapisać pełny raport i stronę z oryginalnymi dowodami, uruchomić weryfikację raportu w GitHub Actions, sprawdzić PR, scalić tylko zielony commit. Wdrożenie strony wymaga osobnej weryfikacji; samo scalenie GitHub go nie potwierdza.
