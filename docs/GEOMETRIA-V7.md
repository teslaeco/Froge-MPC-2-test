# Geometria v7 — 7 września 2026

Poprawka wynika z dwóch błędów profilu zgłoszonych przy wieżowcu oraz zbyt uproszczonej figurki rapera. Zrzut ekranu nie zawiera pełnego planu JSON; testujemy klasę poprawnych profili wcześniej odrzucanych, a nie odzyskany plan tamtego zlecenia.

- Profile obrotowe obsługują zamknięte obrysy, odcinki opadające, uskoki i promień zero na osi. Przecięcia, ujemne promienie i brak objętości nadal są błędami. Kolejność punktów nie jest sortowana.
- Ekstruzja umożliwia nieokrągły, np. trójramienny rzut budynku, uskoki, fasadę z oknami i osobny materiał tarasów.
- Nowa operacja person tworzy twarz, palce, ubrania o połączonej siatce, buty i dodatki. To nadal proceduralna figurka; nie obiecujemy fotorealizmu ani podobieństwa do konkretnej osoby.
- Operacje loft i gęstsze siatki zaokrąglonych brył poprawiają również modele składane indywidualnie. Zachowano limity 200 tys. wierzchołków, 400 tys. trójkątów i 12 MB GLB.

## Sprawdzenie

44 testy Python i 26 testów API/interfejsu przeszło. Build strony z TypeScript zakończył się powodzeniem. W prawdziwym bpy 4.3.0 / NumPy 1.26.4 zbudowano i ponownie wczytano GLB dębu, rakiety, figurki oraz wieżowca. Sprawdzono osadzone PNG, limity geometrii, rozmiar GLB i zamkniętą siatkę wieżowca/iglicy. Obejrzano rendery zaimportowanych plików GLB. Dodatkowo zbudowano wariant szerokiej sylwetki z czapką i mikrofonem oraz szczupłej sylwetki bez nakrycia głowy.

| Ręcznie opracowany plan kontrolny | Wierzchołki | Trójkąty | GLB | Lokalny etap Blender |
|---|---:|---:|---:|---:|
| Figurka rapera | 95022 | 189828 | 5341744 B | 2,76 s |
| Wieżowiec inspirowany Dubajem | 792 | 1572 | 948032 B | 0,15 s |

Powyższe czasy dotyczą wyłącznie lokalnego komputera testowego, bez renderowania podglądu i bez wywołania OpenAI. Nie są czasami generowania na Oracle ARM ani obietnicą czasu dla nowych opisów. Plany kontrolne są ręcznie napisane; generator nie podmienia nimi zleceń użytkownika.

## Uruchomienie

Zainstaluj froge-oracle-geometry-v7.zip na istniejącym Oracle jako opc. Aktualizator wykonuje kopię kodu i wycofuje zmianę, jeśli nowy worker nie potwierdzi wersji 7. Zachowuje połączenie, klucz OpenAI oraz zapisane modele. Strona wymaga wersji 7 przed nowym generowaniem. Po aktualizacji odśwież stronę i uruchom nową generację. Stare GLB nie zostają automatycznie przeliczone.

Brak dostępu z tego środowiska do prywatnego klucza OpenAI i SSH Oracle uniemożliwia wykonanie aktualizacji oraz nowego płatnego zlecenia za użytkownika.
