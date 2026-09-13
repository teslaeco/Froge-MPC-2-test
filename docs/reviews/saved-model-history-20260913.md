# Zapisane modele — checkpoint 2026-09-13

Zgłoszenie: drewniana postać i osiemnastościan znikają z dostępnych modeli.

## Potwierdzone
- Produkcyjne D1 ma oba rekordy ze stanem succeeded i nazwą GLB:
  - osiemnastościan: 2000d271-08d1-4123-b014-137bfcaecaaf
  - drewniana postać: 26daac02-a948-4c5e-88ba-b6757a385eac
- Istnienie rekordów nie potwierdza dostępności bajtów R2 ani poprawności geometrii.
- Kod w GitHub na 1fdb696c2dee4a7bf0c3ddf80ca6264c51d54b53 ogranicza historię do 10 zleceń i ukrywa aktywny model z listy.
- Odczyt zapisanych wyników w tym kodzie jest zależny od odszyfrowania połączenia Oracle; odczyt statusu wymaga też zapisanej konfiguracji.
- Prywatny Site pozostaje w wersji 47, źródło e3d60697db43744f6c09157328560c66a031f9a2. Tego źródła nie ma w sprawdzonym GitHubie. Próby klonowania źródeł Site kończą się HTTP 500 lub limitem czasu. Nie wolno podmieniać Site starszą kopią z GitHuba.

## W toku
Przygotowanie poprawki listy i niezależnego od Oracle odczytu archiwum w GitHubie. Wdrożenie na Site oraz odczyt obu rzeczywistych GLB pozostają niepotwierdzone. Nie uruchomiono nowej generacji, nie zatwierdzono modeli do katalogu i nie zmieniono danych istniejących zleceń.

## Przygotowana poprawka
- Pierwszy odczyt obejmuje ostatnie zlecenia oraz osobną stronę 20 zapisanych modeli, dzięki czemu późniejsze nieudane próby ich nie wypychają.
- Starsze wyniki są dostępne przez stronicowanie według daty i identyfikatora.
- Widoczna lista obejmuje również aktualny model, datę, podgląd 3D i pobranie GLB.
- Dostępność pliku jest sprawdzana w R2; brak pliku pozostawia widoczny rekord z jednoznacznym komunikatem.
- Odczyt zapisanych GLB i zakończonych zleceń nie wymaga aktywnego Oracle ani odszyfrowania jego obecnego klucza.
- Zachowano kontrolę właściciela. Nie zmieniono schematu, danych produkcyjnych ani akceptacji modeli do katalogu.

## Weryfikacja
Lokalnie przeszło 69 testów Vitest (realny SQLite i kontrolowane pliki testowe) oraz ścisłe sprawdzenie typów API i interfejsu. Testy obejmują 40 późniejszych nieudanych zleceń, stronicowanie z identycznymi datami, utratę klucza Oracle, brak GLB, ponowienie nieudanego zapisu i ponowne otwarcie strony. To testy zachowania aplikacji, nie badanie rzeczywistej geometrii obu modeli.

Ponowna próba odczytu obu rzeczywistych GLB przez udokumentowane uwierzytelnienie Sites dotarła do API, które odpowiedziało HTTP 401. Sesja właściciela jest wymagana; nie podszywano się pod nią. Pliki produkcyjne nadal nie zostały pobrane ani ocenione.

## Bloker wdrożenia
Aktualny kod prywatnego Site pozostaje niedostępny przez źródłowy Git (HTTP 500/timeout). Poprawka dotyczy kopii GitHub; nie wolno oznaczać jej jako działającej na Site. Wdrożenie wymaga pobrania aktualnego źródła Site, przeniesienia tej poprawki z zachowaniem nowszej obsługi Codex, testów i publikacji. Po wdrożeniu należy potwierdzić pobranie oraz otwarcie obu wymienionych GLB w sesji właściciela.
