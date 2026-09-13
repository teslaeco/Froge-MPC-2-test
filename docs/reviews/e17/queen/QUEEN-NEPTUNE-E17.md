# Królowa Neptuna E17 — dodatkowa postać z wachlarzem

To rzeczywisty, edytowalny model 3D zbudowany ponownie z istniejącego produkcyjnego scenariusza `couture-fan-v20.scene.json` oraz modułów `oracle_connector/runtime/`. Jest osobną postacią do projektu Julii. Nie jest nowym treningiem wag ani wierną rekonstrukcją twarzy z plakatu.

## Wynik i dowody

- 594 200 trójkątów, 305 367 wierzchołków przed ponownym importem.
- 103 obiekty siatki; zachowana osobna głowa, 2 oczy, 2 dłonie i 10 paznokci.
- Wachlarz: 10 segmentów, 11 żeber, 10 wirników z rzeczywistymi otworami; otwory sprawdzone 130 promieniami.
- Uchwyt dłoni: 5 sprawdzonych kontaktów opuszków, odległości powierzchni 0,024–1,676 mm. To kontrola wybranych punktów; nie dowodzi braku każdej kolizji palców.
- Ubranie: osobna dopasowana suknia, kryształowe płaszczyzny, cienkie szwy, kołnierz, rękawiczka, ramiona, peleryna oraz biżuteria.
- Test zawierania tułowia i nóg w sukni: 11 774 próbki, maksymalny stosunek obwiedni 0,98224. Nie jest to certyfikat drukowalności.
- Renderowane pliki PNG powstały z ponownie zaimportowanego `model.glb` w Blenderze 4.3, Cycles CPU, 24 próbki, 640 × 800 px.
- Eksportowano BLEND, GLB i FBX. Ponowny import i automatyczne kontrole dotyczą GLB; FBX nie uzyskał niezależnego testu renderowania.

## Granice wyniku

Dopasowanie twarzy do pierwotnego zdjęcia nie zostało wykonane (`photo_face_fit.applied=false`, `no_measured_face`). W sesji dostępny jest plakat o innej kompozycji. Zapisanych wcześniej 478 punktów twarzy nie przypisano do tego plakatu, ponieważ pochodzą z innego obrazu. Twarz jest parametryczną anatomią dorosłej kobiety; kolorystyka i elementy stroju nawiązują do wcześniejszego projektu.

Oglądanie renderów potwierdza obecność i układ wachlarza, ubrania oraz biżuterii. Twarz jest nadal zbyt ogólna, karnacja jest zbyt jasna względem plakatu, włosy przypominają jednolitą upiętą bryłę, a kryształowe płaszczyzny mają mocne jasne odbicia. Dół stroju, nogi i niewidoczne plecy są autorską interpretacją. Model nie został oceniony jako fotorealistyczny, zaakceptowany przez klienta ani gotowy do produkcji fizycznej.

## Powtórzenie

Źródło jest oparte na `teslaeco/Froge-MPC-2-test`, gałąź `codex/v27-mcp-startup-audit`, produkcyjnych plikach pobranych 2026-09-12. `build.py` korzysta z kopii modułów w `runtime/`. Dane anatomiczne i mapa skóry pochodzą z tych samych repozytoryjnych zasobów, nie z nowego zbioru treningowego. Główne poprawki E17 postaci żywej/szkieletowej wykonuje osobny proces.

```sh
blender --background --threads 2 --disable-autoexec --python-exit-code 1 --python queen-e17/build.py
blender --background --threads 2 --disable-autoexec --python-exit-code 1 --python queen-e17/render.py
```
