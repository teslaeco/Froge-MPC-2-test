# FORGE World — checkpoint 2026-09-13

Użytkownik zlecił publiczną nową stronę GitHub, generator tekst/zdjęcie, archiwum, grywalny świat Cube Chess, masowe modele i tekstury, misję renowacji ISS i link do petycji.

## Wykonano

- Odrębna aplikacja world-demo: 18 typów parametrycznych modeli, eksport GLB/STL, prawdziwe procenty wykonanych etapów i kulisty wskaźnik, automatyczne instrukcje <=9999 znaków.
- Świat 3D, sterowanie WASD/dotyk, kontrola wskazanego obiektu, transformacje, uproszczone kolizje brył budynków/pojazdów, autozapis, lokalne komendy i dyktowanie.
- Trzy demonstracyjne usterki ISS, części zapisywane przed montażem; fikcyjna misja, nie rzeczywista diagnoza stacji.
- Archiwum IndexedDB, niezależne wersje z SHA-256, ZIP backup/restore, import GLB bez zewnętrznych URI. Lokalny zapis wymaga własnych kopii ZIP.
- Partie do 30 różnych opisów i do 100 kopii w świecie; identyczne kopie współdzielą jeden GLB. Oracle działa po kolei, bez niekontrolowanego równoległego zwiększania kosztu.
- PNG proceduralne 1/2/4/8K oraz WAV 44.1kHz. To synteza proceduralna, nie fotorealistyczna generacja AI. Tekstury PNG są osobnymi plikami do użycia w Blenderze.
- Formularz B2B + CSV, kontrola geometrii i tekstur osobno, bez cen i dostawców udawanych jako potwierdzone.
- Petycja Sebastiana o zachowanie ISS.
- bridge/server.py: autoryzowana, trwała kolejka SQLite do istniejącego worker Oracle; token sesji w pamięci klienta, origin ograniczony, worker i most nasłuchują wyłącznie loopback; archiwum pełnych istniejących plików, bez zmiany źródeł. Nie zainstalowano mostu ani nie udostępniono nowego endpointu HTTPS.

## Modele odzyskane

Przez uwierzytelnione Studio i widoczne przyciski pobrano aktualne GLB i BLEND:
- Queen job 99397623-e45c-48dc-95ec-6f84446a54d5: GLB 30 916 276 B, SHA b99e5e8a2de78bddf3fcb1fff941ac15073d94369efd759d5f573dd7a20a9fa1; BLEND 39 523 580 B.
- Julia job 076cb6e8-c3de-4a59-a7b9-c0dfeb2d0e0d: GLB 16 833 328 B, SHA 283ae0198914b905689f8f37fac271ca337170b525d67bbc4bf348899880635d; BLEND 22 893 340 B.
GLB to eksport z podglądu Studio z widoczną skalą i orientacją, nie deklaracja zgodności bajtowej z surowym GLB worker. BLEND to plik z eksportu istniejącego worker. Oba wyniki robocze, geometria nie poprawiana w tym etapie. Nie zastąpiono ich E19. Metadane i hashe wszystkich plików: models/manifest.json. Pełna kopia w FORGE-Julia-Neptune-archiwum.zip. GLB dołączone do lokalnej paczki demo jako models/julia-current.glb i models/neptune-queen-current.glb; nie przesłano ciężkich binariów do gałęzi z kodem. Do publikacji dodać je z zachowanej paczki i sprawdzić hashe.

## Weryfikacja

11 testów Node i 5 testów Python przeszło. Obejmują rzeczywisty GLB export/reimport pięciu typów, wymiary wszystkich 18 typów, materiały, URI, limit promptu, WAV, idempotencję kolejki, autoryzację/CORS i archiwizację z SHA. Kontrola składni JS/Python OK. Statyczny HTML HTTP 200 w lokalnym serwerze.
Przeglądarka kontrolna zablokowała localhost i file URL zgodnie ze swoją polityką; nie obchodzić blokady. Brak testu wizualnego/pełnego E2E na opublikowanej nowej stronie. Nie twierdzić, że UI/Oracle bridge zostały zweryfikowane produkcyjnie.
W działającym prywatnym Studio WebMCP get_3d_generation_status potwierdził Oracle v33, gpt-6-astra, codex-mcp, ready=true. Wbrew wcześniejszemu założeniu v34 nie jest potwierdzone jako zainstalowane.

## Publikacja — blokada

Nowe publiczne repo teslaeco/Forge-World-Studio NIE zostało utworzone. Automatyczny przegląd odrzucił browser Create repository jako public exposure/access change wymagające potwierdzenia w chwili działania mimo wcześniejszej zgody użytkownika. Nie obchodzić odrzucenia innym narzędziem ani repo. Zgromadzić gotowy kod/paczkę, następnie poprosić o dokładne potwierdzenie utworzenia publicznego repo i publikacji demo z GLB obu postaci. Potem ustawić GitHub Pages i sprawdzić całą aplikację na dozwolonym URL. W przyszłym etapie konieczne uruchomienie mostu Oracle z uwierzytelnionym HTTPS; klucz OpenAI nie może trafić do publicznej strony.

Źródła zapisane w prywatnej gałęzi codex/forge-world-demo-20260913 repo teslaeco/Froge-MPC-2-test. Początkowy commit ec7c7a0780a2a254c455e137b9aa73e3f32a12ac; końcowy commit po tym pliku. Istniejące strony Sites pozostają bez zmian: prywatna v47, publiczna v3.
