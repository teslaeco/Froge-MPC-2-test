## Osiemnastościan — raport 2026-09-13

Raport: [porównanie FORGE / Meshy](README.md). PR: [#13](https://github.com/teslaeco/Froge-MPC-2-test/pull/13), baza `codex/v27-mcp-startup-audit`.

- Przygotowano stronę `public/comparisons/polyhedron-2026-09-13/index.html`, raport Markdown, dane JSON, pięć oryginalnych obrazów oraz kontrolę integralności i linków. Zapis przez integrację GitHub. Obrazy mają sygnaturę JPEG mimo przesłanych nazw PNG; publikowane kopie zmieniają tylko rozszerzenie.
- Potwierdzono rekord zlecenia `2000d271-08d1-4123-b014-137bfcaecaaf`: `codex-mcp`, 578,9 s, zapis GLB i ostrzeżenie o błędach/nieukończonej ocenie. Nie odczytano eksportów modeli; próba pobrania modelu ze Studio zwróciła HTTP 403.
- Werdykt dotyczy widocznej regularności prętów: FORGE lepszy w pokazanym przypadku. Nie potwierdzono układu 18 ścian ani gotowości do druku. 18/48/32 to warunek specyfikacji, nie pomiar modeli. Hashe dostarczonej i zapisanej wejściowej referencji różnią się.
- Commit `9ceeaf244fab0b74e2b2313ac6f6663d8f4250cb` uzyskał dwa zielone sprawdzenia `evidence-and-links`; run PR: [34765789758](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34765789758). Końcowa poprawka dodaje galerię bezpośrednio do Markdown i jest objęta tym samym workflow; przed scaleniem odczytać wynik jej dokładnego SHA.
- Wdrożenie prywatnego Studio pozostaje **wersją 47**, źródło `e3d60697db43744f6c09157328560c66a031f9a2`, deployment `appgdep_6aa4d7f7538c81918ba273fb23acab3e` potwierdzony jako succeeded.
- **Nowej strony raportu nie opublikowano.** Odczyt remote HEAD Sites zadziałał; pobranie źródeł zakończyło się timeoutem, a drugi ograniczony czasowo odczyt zakończył się `RPC failed; HTTP 500; expected 'packfile'`. Nie zastępować prywatnego Studio starszym GitHub `main` ani publicznym pokazem.
- Następny krok po naprawie źródeł Sites: zastosować tylko pliki raportu do aktualnej wersji Studio, zweryfikować/zbudować istniejący projekt, wypchnąć źródło, zapisać wersję i wdrożyć z zachowaniem dostępu; potwierdzić status oraz adres `/comparisons/polyhedron-2026-09-13/index.html`.
- Nie uruchomiono płatnego AI, Blendera, instalacji Oracle ani nowej generacji. Nie scalano starszych draftów.

---

