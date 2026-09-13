# FORGE World Studio — demo do testów

Odrębny świat roboczy dla projektu Cube Chess. To demonstracja tworzenia i używania modeli, nie gotowa gra, symulator inżynierski ani automatycznie zatwierdzony sklep.

## Uruchomienie

W katalogu tego pliku:

```sh
python3 -m http.server 4173
```

Otwórz `http://localhost:4173`. Wymagany WebGL 2 oraz przeglądarka obsługująca moduły JavaScript i IndexedDB. Strona nie wymaga npm ani dostępu do CDN. Biblioteki Three.js 0.185.1 i JSZip są w katalogu vendor z licencjami.

## Co można zrobić

- „Przygotuj zlecenie” tworzy rzeczywisty GLB bryły lub jednego z jawnych szablonów. Nieznany obiekt kieruje do Astry; nie jest zastępowany dowolnym szablonem. Obsługiwane: sześcian, kula, walec, stożek, torus, graniastosłup, ośmiościan, dwudziestościan, dom, auto, koparka, astronauta, schemat ISS, właz, radiator, antena, drzewo, plansza 8 × 8.
- Wymiary w promptach w mm/cm/m. Maksymalny wymiar jest mierzony po zbudowaniu geometrii. Przykład: `Niebieski graniastosłup 10 cm, boki 6`.
- Partia obsługuje do 30 różnych opisów, po jednym w wierszu, i maksymalnie 100 obiektów łącznie. Wiele kopii korzysta z jednego wygenerowanego GLB; oryginał nie jest ponownie generowany ani zmniejszany. Każda nowa wersja ma oddzielny identyfikator i SHA-256.
- Sterowanie kamerą myszą/palcem. Spacer i sterowanie zaznaczonym obiektem: WASD/strzałki, przyciski na ekranie. Esc wraca do edytora. To uproszczony ruch bez zaawansowanej fizyki i animowanego rigu.
- Misja ISS: podejście do trzech znaczników, E/skan, wytworzenie i zamontowanie części. Usterki są fikcyjnymi celami gry, nie stanem rzeczywistej ISS. Drukowane części są testowymi makietami.
- Archiwum GLB, tekstur PNG i dźwięków WAV na tym urządzeniu; zapis świata, import GLB, eksport całego ZIP i odtworzenie. IndexedDB nie jest gwarancją niezniszczalnej kopii: pobieraj ZIP i przechowuj poza przeglądarką.
- Osobny podgląd z materiałami i neutralną geometrią, siatka, pomiar, eksport oryginalnego GLB i roboczego STL z maksymalnym wymiarem 100 mm.
- Proceduralne materiały PNG 1K/2K/4K/8K generowane w workerze z rzeczywistą liczbą pikseli. To nie fotorealistyczna rekonstrukcja ze zdjęcia. PNG jest osobnym plikiem materiału. PBR z fotografii wymaga Oracle/Blendera.
- Dźwięki proceduralne: sygnał, alarm, silnik; WAV PCM 44,1 kHz.
- Zestawienie B2B: modele, sztuki, wymiary, SHA, materiał, kolor, region. Cennik za kg i wykonawca nie są potwierdzone; nie ma przycisku płatnego zamówienia.
- Czat poleceń lokalnych i opcjonalne dyktowanie zależne od przeglądarki. Przykłady: `dodaj dom 10 cm`, `przenieś x 5 z 3`, `obróć 45`, `leć na ISS`. Mikrofon nie uruchamia zlecenia automatycznie; użytkownik sprawdza tekst.
- Automatycznie składane instrukcje do Codexa: limit 9999 znaków, geometria przed teksturami, zachowanie referencji i mastera, kopie LOD, raport zamiast niepotwierdzonej deklaracji jakości.
- Link do petycji Sebastiana o zachowanie ISS.

## Astra + Blender

GitHub Pages nie wykonuje Blendera i nie przechowuje klucza OpenAI. Przewidziano oddzielny, autoryzowany most do istniejącego Oracle; plik `bridge/server.py` jest przygotowany, ale nie został zainstalowany na Oracle w tej sesji. Połączenie ze starym Studio działa; odczyt 13 września 2026 wskazuje v33, gpt-6-astra, codex-mcp.

Most uruchamia się na serwerze z istniejącym `~/froge-connector`. Wymaga Python 3.9+. Nie zmienia starej konfiguracji, nie usuwa modeli i nie wprowadza anonimowego dostępu do generowania.

```sh
python3 bridge/server.py --worker-root "$HOME/froge-connector" --origin https://teslaeco.github.io
```

Nasłuchuje wyłącznie na `127.0.0.1:8866`. Do połączenia z opublikowaną stroną administrator musi udostępnić ten port przez swoje istniejące HTTPS/reverse proxy i wpisać w stronie jego adres oraz token sesji wygenerowany w terminalu. Nie otwieraj portu worker 8765 w Internecie. Token sesji wygasa po godzinie, pozostaje w pamięci karty, nie jest zapisywany w repozytorium. Klucz dostępu do istniejącego worker pozostaje wyłącznie na Oracle.

Kolejka zapisuje żądania w SQLite i zleca jeden model naraz. Ponowienie identycznego ID nie powoduje nowego płatnego zlecenia. Błędy Oracle zachowują stan do diagnostyki. Nie ma pomiaru procentowego w worker v33, więc w tym trybie interfejs wyświetla aktywność, etap i czas, a procent dopiero, jeśli serwer go podaje. Limit 30 minut nie jest udawaną estymacją.

Most wykonuje pełne kopie dostępnych GLB/BLEND/masterów, eksportów, tekstur, referencji i instrukcji do `~/forge-world-state/archive/<job>/<hash>/`. Zachowuje źródła. Interfejs klienta kopiuje GLB na urządzenie; pełne archiwum serwerowe pozostaje prywatne.

## Modele Julii i Królowej

Dokładne źródła: Julia `076cb6e8-c3de-4a59-a7b9-c0dfeb2d0e0d`, Queen `99397623-e45c-48dc-95ec-6f84446a54d5`. Są to wyniki robocze. Nie zastępować ich starszą modelką E19. Oba aktualne GLB oraz edytowalne BLEND odzyskano przez uwierzytelniony interfejs Studio. Pliki GLB w models/ są eksportami podglądu z widoczną skalą i orientacją, nie deklarowaną bitowo identyczną kopią surowego GLB Oracle. Oryginalne pliki BLEND są w oddzielnym archiwum modeli. Zapisano sumy SHA-256 i pochodzenie w models/manifest.json. W archiwum strony można wczytać obie postacie; pliki pobierają się dopiero po kliknięciu.

## Weryfikacja i publikacja

```sh
npm install --ignore-scripts --no-save ./vendor/three
npm test
python3 -m unittest discover -s bridge -p 'test_*.py'
```

Sprawdzono programowo wszystkie 18 typów brył, zachowanie skali, eksport i ponowne wczytanie GLB pięciu typów, materiały, limit promptu, WAV, autoryzację mostu, kolejkę i archiwizację z SHA. Przeglądarka kontrolna nie może otworzyć lokalnego adresu/plików z powodu polityki URL; gra wymaga jeszcze testu wizualnego i interakcji na dozwolonym, opublikowanym adresie. Nie deklarujemy ukończenia tego testu.

Tworzenie nowego publicznego repozytorium `teslaeco/Forge-World-Studio` zostało zablokowane przez automatyczny przegląd zgód. Wymagane potwierdzenie przy publikacji. Źródła są zapisane w prywatnej gałęzi `codex/forge-world-demo-20260913` projektu `teslaeco/Froge-MPC-2-test`, w katalogu `world-demo`. Istniejące witryny pozostają zachowane.
