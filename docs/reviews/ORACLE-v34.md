# Oracle v34 — instalacja sprawdzonej poprawki

Stan: **paczka gotowa; instalacja na Oracle nie została wykonana w tej sesji**.

Pobierz [froge-v34.zip](../../public/downloads/froge-v34.zip), a następnie prześlij ją przez Menu → Upload w swoim Oracle Cloud Shell, do katalogu domowego. W Cloud Shell musi być obecny dotychczasowy klucz `$HOME/ssh-key-2026-09-06.key`; nie przesyłaj klucza do czatu.

Uruchom:

```bash
python3 -m zipfile -e "$HOME/froge-v34.zip" "$HOME/froge-v34"
python3 "$HOME/froge-v34/froge-v34.py"
```

Instalator łączy się z dotychczasowym workerem `opc@141.148.242.30`. Zachowuje konfigurację i zlecenia, weryfikuje pięć istniejących dużych zasobów po SHA256 przed zmianą plików oraz sprawdza rzeczywiste eksporty i połączenie Codex/MCP/Blender. Zatrzymuje aktualizację przy aktywnym generowaniu; nie uruchamia domyślnie płatnego generowania postaci. W razie błędu instalacji wykonuje przewidziany rollback.

Potwierdzeniem instalacji jest końcowe `FROGE_V34_OK`, a po odświeżeniu połączenia Studio:
- `connectorVersion: 34`
- `referenceAcceptanceRevision: 1`
- `workerRelease: v34-reference-acceptance`

Sam ZIP lub zielone CI nie stanowi dowodu aktualizacji Oracle. Ta paczka nie zmienia prywatnego kodu strony Studio ani nie naprawia automatycznie wcześniej zapisanych modeli.

## Integralność i pochodzenie

- Testowany commit: `ad8844cd8d350c0af6939e1a0cda847dd87e3f9b`.
- [CI 34730631366](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34730631366): oba zadania zakończone sukcesem, 146 testów na Pythonie 3.9 i 3.12 oraz rzeczywiste kontrole Blender/MCP/eksportów/atlasów/szachownic.
- ZIP: 394 457 bajtów.
- SHA256 ZIP: `087f5bc8337e554738a03a335c12ad17cbef05ac555748348a2cc68249187dca`.
- SHA256 payloadu: `4313a9614e4cbbad2f0b4fd91a775cd1e7def483af5f2b1cbfa9b31877af9e85` — dokładnie ten sam co w udanym CI.

Natywne pobranie artefaktu GitHub zwróciło odnośnik, lecz pobranie jego bajtów w środowisku kończyło się HTTP403. Dostarczony ZIP odtworzono deterministycznie ze źródeł testowanego commitu i oryginalnego szablonu instalatora; sprawdzono identyczny hash payloadu z CI, CRC i kompilację kodu. Nie deklarujemy identyczności bajtowej z wewnętrznym ZIP-em CI, którego hash nie był dostępny. Pięć dużych zasobów zweryfikowało CI; brakujących lokalnych plików nie zastępowano. Instalator ponownie weryfikuje je na Oracle.

[Pełny raport integralności](resume-2026-09-13/froge-v34-verification.json).
