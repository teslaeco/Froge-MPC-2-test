# Studio 3D z dowolnego opisu

Domyślny tryb strony głównej wysyła pełny opis do Meshy, zamiast przepuszczać go przez parser czterech brył. Nie ma listy dozwolonych nazw obiektów. Generator może przyjąć np. „A teraz zrób drzewo dąb”; jakość i zgodność wyniku zależą od Meshy. Nie jest to CAD ani gwarancja wykonania każdego pomysłu.

## Podłączenie i użycie

1. Otwórz „Połączenie AI”, podaj własny klucz API Meshy i sprawdź połączenie. Klucz jest trzymany w pamięci karty, nie w localStorage, sessionStorage, repozytorium ani eksporcie. Może być też skonfigurowany jako sekret serwera `MESHY_API_KEY` przez administratora strony. Nie wklejaj go do rozmowy.
2. Wpisz lub podyktuj opis (do 800 znaków). Żaden wymiar ani kąt nie jest wymagany. Kliknięcie „Generuj model 3D” wysyła zadanie korzystające z kredytów API Meshy. W tym trybie pisanie nie uruchamia automatycznych płatnych żądań.
3. Aplikacja tworzy geometrię przez Meshy-6, następnie opcjonalnie nakłada tekstury PBR 2K. Wyświetla postęp bieżącego etapu zwracany przez API. To asynchroniczne generowanie, nie rozmowa Realtime/Astra ani edycja geometrii podczas mówienia. Kolejny opis tworzy nowy model, nie edytuje semantycznie poprzedniego.
4. „Wstrzymaj śledzenie” zatrzymuje oczekiwanie w przeglądarce, nie usuwa ani nie anuluje zadania Meshy. Identyfikator, opis i etap są zapisywane w sessionStorage na czas karty. „Sprawdź zapisane zadanie” wznawia odczyt bez ponownego tworzenia geometrii. Niepewnego żądania tekstur nie ponawiamy automatycznie. Po błędzie tekstur można osobno pobrać geometrię.
5. Gotowy model można obrócić, skalować i pobrać jako GLB z materiałami lub STL w mm. Podgląd i eksport korzystają z tego samego obiektu Three.js. Pliki nie są przechowywane trwale przez stronę — pobierz je, zanim zasoby Meshy wygasną.

## Opcjonalne wymiary

Domyślnie najdłuższy bok ma 10 cm. Puste pola zachowują proporcje. Jeden wymiar ustawia skalę proporcjonalnie; kilka wymiarów pozwala zmienić proporcje. Wymiary są w cm, obrót w stopniach wokół osi X/Y/Z. Są to obroty całego obiektu, nie precyzyjne kąty konstrukcyjne. Gabaryty pod podglądem mierzone są po obrocie. GLB używa metrów, STL milimetrów. Dokładne wymiary zapisane jedynie w opisie nie są gwarantowane przez generator — do dokładnego skalowania użyj opcjonalnych pól.

## Zaplecze i granice weryfikacji

Worker udostępnia tylko konkretne operacje Meshy pod `/api/3d/`. Klucz przekazuje wyłącznie do API Meshy, nie do adresu pliku. Pobiera GLB z dozwolonych hostów zasobów Meshy, odrzuca przekierowania oraz obce źródła żądań. Klucz nie jest logowany. Strona zachowuje dotychczasowy dostęp prywatny. Publikacja szerzej wymaga własnej polityki autoryzacji, limitów i rozliczania generacji. Limit podglądu: 64 MB i milion trójkątów; zewnętrzne zasoby GLB są odrzucane, Draco jest obsługiwane lokalnym dekoderem.

Testy sprawdzają wysłanie opisu dębu bez wymiarów, etapy preview/refine, brak klucza, brak kredytów, niedozwolone źródła i adresy plików, nieponawianie niepewnych operacji, skalowanie, eksport STL oraz interfejs. Testy API korzystają z kontrolowanych odpowiedzi zastępczych. Nie przeprowadzono rzeczywistej płatnej generacji, ponieważ nie podłączono klucza konta. Mikrofon i renderowanie na telefonie nie były testowane na urządzeniu. Przed drukiem lub użyciem technicznym wymagana jest kontrola i ewentualna naprawa siatki.

Dokumentacja integracji: [Meshy Text to 3D](https://docs.meshy.ai/en/api/text-to-3d), [uwierzytelnienie](https://docs.meshy.ai/en/api/authentication), [GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html), [GLTFExporter](https://threejs.org/docs/pages/GLTFExporter.html).

---

# Tryb brył parametrycznych

Zakładka „Bryły parametryczne” zawiera lokalny edytor. Wprowadza rakietę o średnicy 10 mm i wysokości 50 mm, podgląd WebGL oraz eksport geometrii i tekstury. Nie zmienia oryginalnej strony konkursowej.

## Użycie

1. Wpisz „Zrób rakietę, szerokość 1 cm, długość 1 cm, wysokość 5 cm, metal z oknem”. Kliknij „Zastosuj polecenie”.
2. Włącz „Wprowadzaj polecenia na żywo”, aby wykonywać rozpoznane zmiany po 650 ms przerwy w pisaniu. Można dopowiadać nowe wymiary i kolory bez przerywania podglądu. Pola wymiarów działają od razu.
3. „Dyktuj polecenie” uruchamia rozpoznawanie mowy pl-PL dopiero po kliknięciu. Widoczne są transkrypcja, stan mikrofonu, zatrzymanie i błędy. Finalne zdanie trafia do pola polecenia; przy włączonym trybie na żywo aktualizuje model. Wstępne rozpoznanie jest tylko podglądem tekstu.
4. Przeciągnij model, zmień powiększenie, zatrzymaj obrót lub wybierz przód/górę. „Cofnij” przywraca poprzednią specyfikację (do 30 kroków w bieżącej sesji).
5. Pobierz glTF z teksturą PNG, STL, samą teksturę lub specyfikację z wymiarami i informacją o wersji.

## Wymiary i uczciwe granice

- Wewnętrzne parametry są w milimetrach, glTF w metrach; STL nie koduje jednostek, dlatego nazwa i dokumentacja określają mm. Zaimportuj STL w mm.
- Średnica dotyczy okrągłego korpusu. Cztery opcjonalne lotki zwiększają szerokość i głębokość do około 1,6 średnicy; rzeczywiste gabaryty całej siatki są wyświetlane pod podglądem.
- Kąt nosa to kąt wierzchołkowy stożka. Zbyt długi nos jest odrzucany, a poprawna poprzednia wersja pozostaje dostępna.
- Okrąg jest próbkowany do 32–256 segmentów, wielokrotności czterech. Panel podaje maksymalne odchylenie cięciwy korpusu; nie deklaruje matematycznie idealnego koła z wielokątów.
- Okno jest elementem tekstury, nie otworem lub oddzielną szybą. Tekstury są proceduralne, 128 × 128 PNG. Metal/ceramika/karbon określają wygląd, nie rzeczywisty materiał produkcji.
- Podgląd korzysta z dokładnie tych samych pozycji, normalnych i UV co eksport. Oświetlenie podglądu jest przybliżone; zewnętrzny renderer glTF może inaczej wyświetlić materiał PBR.
- STL nie zawiera tekstur. Lotki są oddzielnymi zamkniętymi bryłami przecinającymi korpus; wymagana jest operacja scalenia i kontrola wydruku u wykonawcy. Nie deklarujemy gotowości produkcyjnej, tolerancji procesu ani bezpieczeństwa mechanicznego.
- Pole tekstowe rozpoznaje opisane parametry i cztery bryły: rakietę, walec, stożek, kulę. Pokazuje rozpoznane zmiany; inne szczegóły wymagają podłączonego generatora AI. Nie ma obecnie modelu Astra, Realtime API ani dowolnego generowania tekst-na-3D.
- Dyktowanie zależy od przeglądarki i jej zezwoleń; może korzystać z usługi zewnętrznej i internetu. Nie jest pełną dwukierunkową rozmową z AI. Nagrania nie są zapisywane przez aplikację. [Dokumentacja SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition).
- Historia i model pozostają w pamięci bieżącej strony. Odświeżenie przywraca model startowy; eksportuj specyfikację, aby zachować plik. Import zapisanej specyfikacji i trwała baza projektów to dalszy etap.

## Narzędzia dla agenta

`inspect_live_3d_studio` zwraca aktualną specyfikację, rewizję i zmierzone gabaryty. `update_live_3d_studio` przyjmuje pełną specyfikację i `expectedRevision`. Wymaga zgodnej rewizji, waliduje zakresy, nie wykonuje dostarczonego kodu i aktualizuje dokładnie ten sam model co panel użytkownika. Starsze polecenie nie nadpisze nowszej edycji użytkownika. Działa przez centralny mechanizm rejestracji WebMCP w obsługiwanej przeglądarce. [Dokumentacja WebMCP](https://developer.chrome.com/docs/ai/webmcp/imperative-api).

Testy obejmują parser PL z jednostkami i przecinkami, sprzeczne wymiary, topologię korpusu, orientację powierzchni, zgodność glTF z pozycjami podglądu, skalę STL, dekodowanie PNG, zmiany tekstury, wymiary lotek, panel użytkownika, cofanie i konflikt wersji przy poleceniach agenta. Obsługa rzeczywistego mikrofonu i renderowanie na konkretnym telefonie wymagają sprawdzenia na urządzeniu.
