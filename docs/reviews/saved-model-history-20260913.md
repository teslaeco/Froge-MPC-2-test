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
