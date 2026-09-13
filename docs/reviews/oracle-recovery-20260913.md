# FORGE — aktualizacja Oracle i odzyskanie zapisanych modeli

Paczka zawiera sprawdzony instalator v34 odzyskany z repozytorium projektu oraz nowy skrypt `forge-oracle.py`. Aktualizacja nie została jeszcze uruchomiona na Oracle w tej rozmowie.

## W Oracle Cloud Shell

Pobierz `FORGE-Oracle-aktualizacja.zip` i prześlij przez Menu → Upload do katalogu domowego Cloud Shell. Użyj tej samej sesji, w której masz dotychczasowy klucz `ssh-key-2026-09-06.key` oraz zapisany host serwera. Następnie wklej:

```bash
python3 -m zipfile -e "$HOME/FORGE-Oracle-aktualizacja.zip" "$HOME/FORGE-Oracle-aktualizacja"
python3 "$HOME/FORGE-Oracle-aktualizacja/forge-oracle.py"
```

Skrypt łączy się z dotychczasową maszyną `opc@141.148.242.30` przez istniejące SSH. Nie pyta o nowe klucze API i nie uruchamia płatnej generacji. Nie wysyłaj klucza SSH do czatu.

1. Odczytuje wersję i liczbę aktywnych zleceń. Aktywna kolejka blokuje instalację; skrypt niczego nie anuluje.
2. Jeżeli wersja jest starsza niż v34, uruchamia oryginalny sprawdzony instalator v34. Jeśli działa v34 lub nowsza, pozostawia ją. Instalator zachowuje konfigurację, połączenie i modele; weryfikuje istniejące duże zasoby, wykonuje testy i ma mechanizm przywrócenia kodu po błędzie.
3. Sprawdza rzeczywiste `connectorVersion` przez lokalny endpoint health. Sam zapis plików nie wystarcza do potwierdzenia aktualizacji.
4. Wyszukuje dokładnie zlecenia Julii `076cb6e8-c3de-4a59-a7b9-c0dfeb2d0e0d` oraz Królowej `99397623-e45c-48dc-95ec-6f84446a54d5` w `~/froge-connector/state/jobs`.
5. Pakuje istniejące GLB/BLEND i dozwolone pliki sceny/edycji/raportu, po czym kopiuje archiwum do Cloud Shell. Nie kopiuje konfiguracji, kluczy ani żądań API. Zapisuje SHA-256. Oryginały pozostają na Oracle.

Końcowy komunikat `FROGE_MODELS_EXPORTED: /home/.../FORGE-modele-julia-neptune-....zip` podaje plik do pobrania przez Menu → Download. Przy każdym modelu zostaje wypisany wynik: `exported`, `missing` albo `active-not-exported`. `exported` nie oznacza naprawionej geometrii ani zgody na produkcję. Brakującego modelu skrypt nie zastąpi wcześniejszą modelką.

Jeżeli aktualizacja jest blokowana przez inne aktywne zadanie, możesz skopiować tylko zakończone modele, bez instalacji:

```bash
python3 "$HOME/FORGE-Oracle-aktualizacja/forge-oracle.py" --export-only
```

Nie ponawiaj instalacji po przerwaniu połączenia bez sprawdzenia wersji/stanu na Oracle. Jeśli host SSH lub klucz nie są rozpoznane, użyj dotychczasowej skonfigurowanej sesji Cloud Shell. Nie wyłączaj weryfikacji hosta. Jeżeli zgłoszono brak zgodnych dużych zasobów, instalacja zatrzyma się przed ich podmianą — komunikat poda brakujący zasób.

## Co aktualizuje v34

Zapisany kod poprawia rozpoznawanie atlasów materiałów, sprawdza składnię edycji przed próbą Blendera, rozdziela historię błędów od aktualnej oceny i wymaga dowodów zgodności modelu z referencją. Zachowuje wcześniejsze kontrole anatomii, materiałów i eksportu. Nie podnosi limitów konta ani nie trenuje wag modelu.

To aktualizacja workera Oracle. Karty sklepu, wyszukiwarka B2B i kompozytor strony są w odrębnej przygotowanej paczce strony; samo uruchomienie Oracle nie publikuje tych zmian. W34 to wersja workera. Odzyskane `froge-v19.zip` pozostaje archiwum i nie jest automatycznie instalowane jako W19.

Nie naprawia samoczynnie zapisanej siatki Królowej. Przy błędzie `Free couture hand has no garment to check` trzeba odczytać właściwą scenę i historię edycji, sprawdzić istniejącą geometrię stroju oraz przypisania `character`/`froge_role`. Nie należy wyłączać walidatora. Polecenie dalszej naprawy: `POLECENIE-CODEX.txt`.

## Sprawdzenie i pochodzenie

- Nowy skrypt: 7 testów lokalnych — ochrona przed cofnięciem wersji, blokada aktywnej kolejki, dokładne numery zleceń, brak sekretów w eksporcie, zgodność SHA, odrzucenie dowiązań i zachowanie istniejących plików. Kompilacja Python poprawna. Nie uruchomiono go jeszcze na Oracle.
- ZIP v34: 394457 B, SHA-256 `087f5bc8337e554738a03a335c12ad17cbef05ac555748348a2cc68249187dca`.
- Payload v34: `4313a9614e4cbbad2f0b4fd91a775cd1e7def483af5f2b1cbfa9b31877af9e85`; sprawdzono zgodność z raportem projektu, CRC i kompilację plików Python.
- Źródło: `teslaeco/Froge-MPC-2-test`, gałąź `codex/v27-mcp-startup-audit`, `public/downloads/froge-v34.zip`. Raport wskazuje testowany commit `ad8844cd8d350c0af6939e1a0cda847dd87e3f9b` oraz [CI 34730631366](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34730631366). Nie uruchamiano ponownie tych historycznych 146 testów ani Blendera w tej sesji.
- Pobrano też `froge-v33.zip`, `/MCP2/froge-v19.zip` i `/MCP2/FORGE-modelka-4K.zip`. Ten ostatni zawiera GLB 39711312 B i Blender 62696468 B; oba hashe zgadzają się z jego oryginalnym manifestem. To wcześniejsza modelka; nie utożsamiono jej z bieżącą Julią ani nową Królową.

Sam fakt odnalezienia `froge-v19.zip` nie dowodzi, że to aktywny generator oznaczany przez właściciela W19. Archiwum zostało zachowane do porównania, bez cofania obecnej instalacji.
