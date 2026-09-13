## Stan końcowy wznowienia — 2026-09-13

Aktualny raport: [DELIVERY-2026-09-13.md](DELIVERY-2026-09-13.md).

- Kod v34 zweryfikowany w CI na commit `ad8844cd8d350c0af6939e1a0cda847dd87e3f9b`: 146 testów na każdej z wersji Python 3.9 i 3.12, rzeczywisty Blender/MCP/GLB/FBX, atlas i szachownice. [Run 34730631366](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34730631366) zakończony sukcesem.
- Wykonano rzeczywistą lokalną korektę E18R (nasada włosów i sheen czarnej sukni), ponowny import GLB i kontrolowane rendery przed/po. 6 354 061 trójkątów. Nie przebudowano twarzy, oczu, szyi ani sylwetki.
- Publiczny Site wersja 2 opublikowany: https://forge-studio-public.terraformingplanet.chatgpt.site . Commit źródeł `8d716ebcccc107b5c542ffac03d2c417d62e3f35`; deployment `appgdep_6aa5fd40babc8191a8ad6efe181a99a3` potwierdzony jako succeeded. Źródłowy E18 GLB oraz nowy E18R GLB są zachowane w Git i Site.
- **Nie zainstalowano v34 na Oracle** — brak aktywnej uwierzytelnionej sesji SSH. Przekazano paczkę i polecenie Cloud Shell; nie twierdzić, że serwer został zaktualizowany bez odczytu jego FROGE_V34_OK i health.
- **Nowe Julia/Atlas nie zostały przebudowane** — dostępne są zrzuty, referencja i rekord zlecenia; eksport aplikacji wymaga tożsamości właściciela (401). Do kontynuacji potrzebne są GLB/BLEND tych zleceń. Julia w bluzie nie jest E18 w sukni.
- Prywatny Site nadal wersja 47, klon HTTP500; nie zastąpiono go publicznym pokazem. Gate hosta odrzuca niekompletne dowody, ale cały komplet widoków/pomiarów nie powstaje jeszcze automatycznie.
- Nie uruchomiono L4, treningu wag ani płatnej nowej generacji. Wcześniejszy master/4K usunięty przez porządkowanie środowiska nie został odzyskany; wcześniejsze wzmianki o osobno dostępnych ciężkich masterach są historyczne.
- PR #11 pozostaje draft. Zachować wcześniejsze porównania Meshy jako ocenę ze screenów, nie nowy kontrolowany benchmark. Zachować notatki naukowe i ChessArena jako pamięć/testy projektu.


---

## Checkpoint rozpoczęcia wznowienia

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
