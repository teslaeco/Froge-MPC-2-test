# Codex + Blender — Studio 3D

## Co działa w kodzie

- Wycofano integrację Meshy, formularz klucza, płatne żądania i kolejkę dostawcy. Dotychczasowe adresy `/api/3d/` zwracają 410 bez połączeń z dostawcą.
- Strona przyjmuje GLB i własny format Froge JSON z dowolną geometrią: wierzchołki, trójkąty, UV, materiały i proceduralne tekstury. Nie rozpoznaje nazw obiektów przez wybór czterech presetów. Nie uruchamia jednak samodzielnie LLM ani tej rozmowy.
- Agent WebMCP odczytuje polecenie przez `get_3d_modeling_request`, sprawdza format przez `get_3d_scene_schema` i dostarcza wynik przez `apply_3d_model_scene`. Wymagane requestId i revision odrzucają wyniki dla starszych poleceń. Ręczny import unieważnia wcześniejsze żądanie.
- Osobna zakładka zachowuje lokalny edytor brył parametrycznych.
- Dodatek do Blendera można pobrać z `/downloads/froge-blender-addon.zip`; instrukcję z `/downloads/BLENDER-INSTRUKCJA.txt`. Paczka jest odtwarzana ze źródeł podczas budowania.

## Blender i lokalne AI

Dodatek jest przeznaczony dla Blendera 4.2+. Importuje scenę JSON do nowej kolekcji, nie kasuje istniejących obiektów. Tworzy siatki i mapy UV, pakuje tekstury do projektu, eksportuje wybraną kolekcję GLB. Pełen projekt zapisuje się standardowo przez File > Save As.

Opcjonalne projektowanie z opisu działa przez Ollama na tym samym komputerze. Dodatek odczytuje listę już zainstalowanych modeli; nie pobiera nic samodzielnie i odrzuca modele oznaczone jako chmurowe. Użytkownik wpisuje opis w dodatku albo wczytuje plik polecenia ze strony. Lokalny model zwraca strukturalny plan kompozycji sfer, prostopadłościanów, rur oraz własnych siatek. Biblioteka geometryczna zamienia go w zwalidowaną siatkę. Jest to modelowanie kompozycyjne, nie fotorealistyczna rekonstrukcja ani system CAD. Jakość dowolnego opisu zależy od użytego modelu. Ollama jest osobnym AI, nie Codexem.

Żądanie do Ollama wykonuje wątek korzystający tylko z biblioteki standardowej Pythona. Wszystkie operacje Blender API wykonuje timer głównego wątku. AI nie może dostarczać kodu do wykonania. Przycisk odrzucenia wyniku nie gwarantuje zatrzymania obliczeń po stronie Ollama.

**Nie ma bezpośredniego połączenia telefonu z desktopowym Blenderem ani stale działającego agenta.** Potrzebny jest komputer z Blenderem; przy lokalnym AI także z uruchomionym Ollama. Strona pozostaje podglądem i miejscem wymiany poleceń/plików. Agent z dostępem WebMCP może aktualizować stronę; zwykłe otwarcie jej nie dowodzi obecności agenta.

## Przykład: smok Codexa

Skrypt `scripts/create-dragon.py` tworzy autorski szkic orientalnego smoka: 94 edytowalne części, 36 960 trójkątów, łuskowany korpus, złoty brzuch, rogi, oczy, wąsy, cztery łapy i podstawka. To gotowy przykład utworzony programowo przez Codexa; nie jest wynikiem każdego nowo wpisanego polecenia ani wierną kopią konkretnej postaci. Przecinające się części wymagają scalenia i kontroli przed drukiem. `scripts/package-blender.py` odtwarza model i ZIP z kodu źródłowego, bez Blendera i sieci.

## Wymiary, tekstury i eksport

Wymiary i obroty są opcjonalne. Domyślnie najdłuższy bok ma 10 cm. Jeden podany wymiar skaluje proporcjonalnie, kilka może zmienić proporcje. Kąty obracają cały model; nie określają kątów konstrukcyjnych. GLB ma jednostki metrów, STL należy importować w mm. Eksportowany Froge JSON zachowuje źródłowe współrzędne w cm przed zmianami skali i obrotu. Blender konwertuje osie (x,y,z) → (x,-z,y) i cm → m.

Tekstury są rzeczywistymi mapami 128×128 dla materiałów solid/scales/bark, bez płatnej usługi. Każda część ma UV. Geometria źródłowa i podgląd są wspólne z eksportem; GLB/STL zachowują transformację podglądu. Żaden wynik nie otrzymuje automatycznej gwarancji gotowości do produkcji.

## Weryfikacja i ograniczenia

Testy obejmują walidację siatek i indeksów, odrzucanie kodu i starych wyników, brak płatnych wywołań, opcjonalny panel wymiarów, skalę STL, dodatnią orientację siatek sfer/prostopadłościanów/rur, poprawność sceny smoka, składnię Pythona i paczkę ZIP. Wykonano podgląd kontrolny geometrii smoka. Próba instalacji Blender bpy nie powiodła się, więc **nie przeprowadzono testu dodatku we właściwym Blenderze ani rzeczywistego generowania przez Ollama**. Nie testowano mikrofonu na telefonie.

Źródła interfejsów: [Blender Python API](https://docs.blender.org/api/current/), [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs), [Ollama chat API](https://docs.ollama.com/api/chat).

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
