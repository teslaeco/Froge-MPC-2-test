# E16 — korekta geometrii i materiałów

Baza: dostarczony przez użytkownika FORGE-model-E15.blend. E15 zachowany bez zmian. E16 jest częściową korektą techniczną, a nie ukończonym wiernym odwzorowaniem ilustracji.

## Wykonane zmiany

- Dopasowano 2790 wierzchołków górnej szyi do rzeczywistej powierzchni głowy. Zmniejszono widoczny uskok pod żuchwą; dodano delikatny relief obojczyków i ścięgien szyi.
- Przebudowano obrzeże otworu nosa i jego wnętrze na podstawie istniejącej pętli 538 wierzchołków. Zachowano ciągłość kolejności krawędzi, dodano przejście powierzchni i lokalne wygładzanie. Usunięto dawną płaską przesłonę nosa.
- Lokalnie zwężono kącik ust po stronie czaszki; wspólnie przesunięto odpowiednie fragmenty głowy, uzębienia i jamy ustnej. Nie przebudowano całego uzębienia ani żywego uśmiechu.
- Podniesiono środkowy fragment dekoltu i delikatnie dopasowano talię. Dopasowano 3000 wierzchołków szwów do powierzchni sukni, ograniczając odstające pasma.
- Utworzono dwie nowe mapy koloru tkanin na bazie istniejących tekstur: zmniejszono kontrast dużych plam, dodano subtelne zróżnicowanie splotu. To modyfikacja map koloru, nie pełna rekonstrukcja tkaniny z fotografii.
- Skorygowano parametry materiału ciepłej skóry tułowia.

Zachowano globalny rozmiar głowy i geometrię żywego oka z E15. Nie powtórzono poszerzenia czaszki z R15. Włosy pozostały z E15.

## Weryfikacja

Ponownie wczytano wyeksportowany FBX w pustej scenie Blendera. Wynik: 2 008 003 trójkąty, 419 obiektów siatkowych, wszystkie z UV, brak brakujących aktywnych obrazów tekstur. Rendery porównawcze pochodzą z FBX, przy stałej kamerze i oświetleniu dla E15/E16; nie są ilustracjami generowanymi obrazowo. Widok bez tekstur pokazuje rzeczywistą geometrię.

Liczba trójkątów jest pomiarem eksportu, nie miarą podobieństwa. Nie wykonano certyfikacji do druku ani pełnego testu wszystkich przecięć i szczelności. Skala fizyczna wymaga osobnego ustalenia przed wydrukiem.

## Ocena i pozostałe braki

Przejście szyi w żuchwę jest gładsze, a szwy lepiej przylegają do sukni. Nadal nie osiągnięto jakości grafiki referencyjnej. Nasada włosów przypomina osłonę, pasma są zbyt regularne, żywe oko zbyt mocno polega na teksturze fotograficznej, a kształt powiek i naturalność uśmiechu wymagają przebudowy. Obrzeże nosa i szczęka wciąż wymagają rzeźbienia, podobnie jak dopasowanie sylwetki i fałdy ubrania. Nie zatwierdzono podobieństwa.

Referencja przedstawia przód i tylko część sylwetki. Tył i zasłonięte powierzchnie modelu są interpretacją. Tło, księżyc i taśma filmowa nie zostały odtworzone w tym etapie. Nie ma podstaw do stwierdzenia, że odtworzono wszystkie elementy ilustracji.

## Pliki

- FORGE-model-E16.blend — scena z edytowalnymi obiektami i spakowanymi obrazami.
- FORGE-model-E16.fbx — eksport z osadzonymi teksturami.
- FORGE-model-E16.glb — eksport do podglądu z materiałami.
- POROWNANIE-E16.png — E15/E16 i widok ukośny.
- WIDOKI-E16.png — przód, lewy bok i tył.
- GEOMETRIA-E16.png — porównanie bez tekstur.

Brak wdrożenia strony i zmian na Oracle. Kod korekty i raport zapisano w repozytorium projektu. Zapis trwałych kopii plików 3D w tej sesji jest niedostępny; pliki do pobrania pozostają w bieżącym obszarze roboczym.
