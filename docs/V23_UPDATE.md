# FORGE v23 — swobodne powierzchnie i tekstury z referencji

## Cel i rzeczywista zmiana

Poprzedni test Astry v22 nie zachował oczekiwanej twarzy, fryzury ani stroju.
V23 rozszerza narzędzia dostępne Astrze i dodaje ogólne przypisanie zdjęć do
geometrii. To aktualizacja kodu generatora, nie trening nowego modelu AI.

- `surface_grid`: regularna siatka punktów kontrolnych XYZ, interpolowana do
  powierzchni, z opcjonalną fizyczną grubością; przydatna dla paneli, powłok,
  fragmentów ubrań i innych zakrzywionych kształtów.
- `contour_loft`: interpolowane, swobodne przekroje o równych liczbach punktów,
  bez ograniczenia każdego przekroju do elipsy. Obsługuje asymetryczne bryły.
- Plan sceny v2 zawiera `reference_views`: kamery, numery dostarczonych zdjęć
  i wielokątne maski pikseli przypisane do nazwanych części. Nowe zlecenie
  zdjęciowe nie może przejść z pustą projekcją ani samym dawnym szablonem.
- Blender projektuje zachowane piksele na ściany skierowane do kamery, mieszczące
  się w masce i widoczne w testach głębokości. Wybiera lepszy kąt i skalę obrazu
  spośród dostępnych widoków. Zasłonięte ściany zachowują dotychczasowe materiały.
- FBX/OBJ dostaje wspólny kanał koloru UV złożony osobno dla ścian używających
  różnych materiałów. Kanały źródłowe i dane głównego GLB pozostają zachowane.
- Budżet AI: do 600 s planowania i do 240 s oceny, 840 s łącznie. Ocena `keep`
  nie musi przepisywać całej sceny. Blender: do 600 s pierwszej budowy oraz
  rezerwa 300 s na przebudowę, 900 s łącznie. Większy budżet może zwiększyć koszt API.
- Uwierzytelniony `GET /v1/jobs/{id}/quality` raportuje geometrię, rzeczywiste
  tekstury, projekcję, pomiary twarzy i stan oceny. Sam zapis pliku nie jest
  oznaczany jako akceptacja jakości. Ten endpoint nie jest jeszcze narzędziem
  WebMCP opublikowanego interfejsu strony.

## Sprawdzenie

62 wykonania testów Python przeszły, w tym transport HTTP, uwierzytelnienie
raportu, walidacja planu, rezerwy czasu, eksport i przywracanie kodu aktualizacji.
Część modułów współdzieli testy HTTP; liczba nie oznacza 62 nowych testów.
`git diff --check` przeszedł.

Natywny Blender 4.3 zbudował dwa rodzaje zamkniętych powierzchni kontrolnych.
Sprawdzono manifold siatek, widoczny przód i tył pokryty dwoma obrazami oraz
odrzucenie zasłoniętej ściany. Ponowny import FBX zachował liczbę trójkątów.
Sprawdzono także konsolidację UV i przywrócenie oryginalnych kanałów po eksporcie.

Osobny obiekt kontrolny instalatora ma 196 wierzchołków i 364 trójkąty;
nowe narzędzia, dwie poprawnie rzutowane ściany i eksporty FBX/OBJ/STL przeszły.
To testy narzędzi na zaprojektowanych danych. Nie są nową generacją Astry ani
potwierdzeniem podobieństwa dowolnej postaci. Nie wykonano w tej aktualizacji
nowego płatnego zapytania AI ani testu jakości na wielu rzeczywistych zdjęciach.

Pełną paczkę 54 plików porównano bajtowo ze źródłem; Python i ZIP przeszły
sprawdzenie integralności. Natywne dowody są w `reviews/v23-native-verification.json`.

## Ograniczenia i następny test jakości

Astra nadal szacuje geometrię, kamerę i maski. Nowe narzędzia umożliwiają lepsze
plany, lecz nie dowodzą, że model wybierze poprawne parametry dla każdego zdjęcia.
Niedokładna kamera może rozminąć teksturę z geometrią. Zasłonięte oraz niewidoczne
powierzchnie wymagają rekonstrukcji. Kolor zdjęcia zawiera sfotografowane światło;
nie jest odzyskanym fizycznym albedo. Normalne, szorstkość i transmisja materiałów
nie są automatycznie odzyskiwane ze zdjęcia. Pełna zgodność shaderów FBX/GLB nie
jest gwarantowana. Twarz nadal korzysta z bazy anatomicznej i dostępnych pomiarów.

Po instalacji należy ocenić rzeczywiste generacje: postać, przedmiot z ostrymi
krawędziami oraz obiekt organiczny, przy tych samych kamerach referencji. Porównać
sylwetkę, szczegóły, przód/profil/tył, mapy i FBX. Zwiększenie liczby pikseli mapy
nie jest miarą poprawnego kształtu. Pełne odwzorowanie każdego modelu nie zostało
osiągnięte ani zweryfikowane w tej wersji.

## Instalacja i stan

Paczka: `froge-v23.zip`. W Oracle Cloud Shell wybierz Menu → Upload i wgraj ZIP.

```bash
python3 -m zipfile -e "$HOME/froge-v23.zip" "$HOME/froge-v23"
python3 "$HOME/froge-v23/froge-v23.py"
```

Instalator zachowuje obecny serwer, połączenie, zapisany OpenAI i modele. Robi
kopię kodu, testuje instalację bez AI i wycofuje zmianę przy błędzie. Prawdziwa
instalacja kończy się `FROGE_V23_OK`, potem odśwież stronę i sprawdź połączenie.

Na koniec przygotowania: Oracle nadal ma ostatnio potwierdzone v22. V23 nie
zainstalowano z tej sesji. Site ostatnio potwierdzono jako v38; wcześniejsze
pobieranie źródła blokował HTTP 500. Nie wykonano nowego wdrożenia strony.
Pokazany interfejs nadal opisuje zmniejszanie zdjęć do 1600 px; wdrożenie obsługi
większych referencji w interfejsie pozostaje oddzielnym wymaganiem.

PR #9 pozostaje otwarty. Testy narzędzi nie zastępują akceptacji wyglądu.
Źródło modelu i obsługiwanych ustawień: [OpenAI — GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra).
