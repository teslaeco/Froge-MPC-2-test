# Wznowienie — 2026-09-13

Stan bazowy: PR #11, commit `01bf1d05ed72eb4e9da48d513d5b34a1a71e34f2`. Ten zapis jest checkpointem pracy, a nie deklaracją zakończonego wdrożenia.

- Odzyskano publiczną stronę i rzeczywisty web GLB E18 ze źródeł istniejącego Site. Model w sukni jest oddzielny od nowej Julii w bluzie.
- Aktualny prywatny Site: wersja 47. Native Sites potwierdza, że publikacja nie deklaruje serwera MCP. Klon źródeł istniejącego prywatnego Site kończy się HTTP 500. Nie utworzono zastępczego projektu.
- Natywny odczyt tabeli zleceń potwierdza Julię `076cb6e8-c3de-4a59-a7b9-c0dfeb2d0e0d`: artefakt GLB zapisany, rezultat roboczy wymagający korekty, 741,9 s. Pobranie jego eksportów przez interfejs aplikacji zwraca 401; nie zmieniono zabezpieczeń aplikacji ani nie podszywano się pod nagłówki tożsamości.
- Plansze `JULIA-reference-vs-reported-failure.webp` i `ATLAS-reported-failure.webp` przedstawiają wejściowe referencje oraz zgłoszone błędne wyniki. Nie są podglądami nowych modeli.
- Audyt wykazał nieudany wcześniejszy GitHub Actions: testy aktualizatora nie uwzględniały nowego pliku `reference_reconstruction.py`. Poprawka i pełna ponowna weryfikacja w toku.
- Sprawdzone lokalnie luki walidacji: kod akceptowany przez AST, ale odrzucany przez compile; atlas głowy wewnątrz grupy węzłów lub przypisany przez obiekt pomijany przez wcześniejszy gate. Nie udowodniono, że to dokładnie przyczyna danego zlecenia Julii, ponieważ nie odzyskano jego sceny i kodu prób.
- Brak uwierzytelnionej sesji SSH Oracle w tej sesji. Poprzednia paczka E18 nie została zainstalowana na Oracle. Przygotowanie i sprawdzenie nowej paczki trwa; instalacja wymaga rzeczywistego potwierdzenia serwera.

Pozostaje: zintegrować poprawki, przejść pełny wymagany zestaw testów, wykonać korektę odzyskanego E18 z identycznymi kamerami przed/po, opublikować wyniki i dostarczyć zweryfikowaną aktualizację Oracle. Nowa Julia i Atlas wymagają dostępu do swoich eksportów do korekty geometrii. Testów regresji nie nazywamy treningiem wag ani uruchomieniem GPU L4.
