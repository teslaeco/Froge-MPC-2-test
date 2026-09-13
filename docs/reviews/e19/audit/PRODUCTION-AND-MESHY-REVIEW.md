# E19 — audyt produktu fizycznego i uczciwe porównanie

Stan 2026-09-13. Wykonano pomiar rzeczywistego wejściowego E18R, nie samą ocenę renderu. Plik GLB ma SHA256 `6f8bef167a6d0e9dc67d4fce67df3782f0bdffb69ede54f8f62a799520f5b6db`. E19 wymaga osobnego audytu po eksporcie; wynik E18R nie jest wynikiem E19.

## Co wykazał pomiar E18R

Blender 4.3.0 ponownie zaimportował GLB, pobrał geometrię po ewaluacji i transformacjach obiektów. Audyt analizował trójkąty każdego obiektu osobno. Zduplikowane wierzchołki o **dokładnie identycznych pozycjach** połączono wyłącznie w analizie, żeby szwy UV eksportu nie były automatycznie uznawane za dziury. Nie użyto tolerancji, która mogłaby zamknąć rzeczywiste szczeliny. Źródłowy model nie został zmieniony.

| Pomiar | Wynik E18R | Znaczenie |
|---|---:|---|
| Obiekty siatkowe | 369 | To edytowalna scena wizualna, nie dowód jednej bryły |
| Trójkąty | 6 354 061 | Liczba nie mierzy podobieństwa ani drukowalności |
| Obiekty z błędami topologii | 283 | Wymagają oddzielnej wersji produkcyjnej |
| Krawędzie otwarte po analizie identycznych pozycji | 19 001 | Część powierzchni nie zamyka bryły |
| Krawędzie należące do więcej niż dwóch trójkątów | 44 024 | Topologia niejednoznaczna jako pojedyncza powierzchnia bryły |
| Krawędzie dwóch trójkątów z niespójnym kierunkiem | 8 481 | Wymagają kontroli orientacji powierzchni |
| Trójkąty zdegenerowane | 121 092 | Pole ≤ 10⁻¹² mm²; wiele pochodzi z końcówek i biegunów włókien |
| Składowe połączone, suma osobnych obiektów | 3 975 | Nie oznacza 3975 gotowych oddzielnych części do wydrukowania |
| Rozmiar natywny X/Y/Z | 718,067 × 450,128 × 1186,056 mm | Wysokość zamawianej figurki nie została określona |

Największe źródła błędów: `E17 individual hair fibers and swept hairline` ma 119 972 zdegenerowane trójkąty; `anatomical-head` ma 15 209 otwartych krawędzi; suknia 984, warstwa szyi i ramion 568. Otwarte elementy shaderów i ozdobnych włókien bywają poprawne w renderze, ale nie stanowią kompletnego modelu produkcyjnego. Suma krawędzi ponad dwóch ścian obejmuje również degeneracje w oryginalnej geometrii, nie jest pomiarem wzajemnych przecięć obiektów.

Nie zmierzono pełnej grubości ścian, samoprzecięć, przecinania obiektów, wewnętrznych powłok, stateczności, podpór ani dostępu narzędzia. Podane objętości zamkniętych pojedynczych obiektów są algebraiczne i mogą zawierać nakładające się obszary; nie wolno sumować ich jako masy produktu. Aktualny wynik: **blokada dopuszczenia E18R jako gotowego produktu fizycznego**.

## Wykryty konkretny błąd ust

Kontrola modelu przez agenta rekonstrukcji ust wykazała, że wcześniejszy obiekt `Recessed oral cavity` miał środek na Z ≈ 1,484 m, a zęby znajdowały się około Z 1,445–1,464 m. Wnętrze ust było przesunięte względem łuku zębowego; samo policzenie obiektów „zęby” lub „głowa” nie wykrywa takiej usterki. Nowy przypadek regresji musi sprawdzać pozycję wnętrza ust względem łuków i render od dołu, na którym ujawnia się pustka. E19 wymaga oceny faktycznego eksportu po tej poprawce.

## Dwie wersje jednego projektu

1. **Wersja wizualna** zachowuje materiały, UV, oczy, drobne włókna i powierzchniowe detale. Tekstury 8192 × 8192 mają sens tylko przy rzeczywistym detalu i dobrym wykorzystaniu UV; nie naprawiają kształtu zęba ani szczeliny między szyją i głową.
2. **Kandydat produkcyjny** wymaga ustalonego rozmiaru, zamkniętych brył, bezpiecznej grubości detali, połączeń i podstawy. Przy roboczym założeniu 200 mm planowana osobna kopia ma podstawę 5 mm, nominalny voxel 0,4 mm i pominięte mikrowłókna; duże pasma pozostają. Grubość dodanej powłoki 0,9 mm jest parametrem budowy, a nie zmierzoną minimalną grubością całego wyniku. Trzeba zmierzyć eksport i obejrzeć twarz oraz włosy po tej transformacji.

„Wypełniony” musi być doprecyzowany w specyfikacji wykonawcy. Zamknięta siatka opisująca objętość i 100% wypełnienia FDM to różne rzeczy. Wypełnienie jest ustawieniem slicera; dokumentacja Prusa wskazuje, że także typ wzoru i procent wypełnienia wpływają na wynik. Nie wykonano rzeczywistego wydruku ani nie ustawiono klientowi automatycznie 100%. [Prusa — Infill](https://help.prusa3d.com/article/infill_42).

Minimalna grubość zależy od procesu, maszyny, materiału, podparcia, obciążenia i skali. Nie ustanawiamy jednej „bezpiecznej” wartości dla wszystkich figurek. Cienkie włosy i zęby trzeba mierzyć po przeskalowaniu oraz sprawdzić, czy przetrwają mycie, odrywanie podpór i użytkowanie. [Formlabs — Minimum Wall Thickness for 3D Printing](https://formlabs.com/blog/minimum-wall-thickness-3d-printing/).

## Druk, laser i obróbka kamienia

| Proces | Wymagany wynik i kontrola | Stan |
|---|---|---|
| FDM | Bryła w mm, materiał i dysza, ściany i detale, orientacja, podpory, slicer i próbka | Nie zweryfikowano procesu |
| SLA/DLP | Bryła, żywica, grubości i podpory, ewentualne kanały odpływowe dla wersji celowo pustej, mycie i utwardzanie | Nie zweryfikowano procesu |
| SLS/MJF | Profil materiału/maszyny, grubości, usuwanie proszku i łączenia | Nie zweryfikowano procesu |
| Grawer laserowy kamienia | Widok/obraz lub relief przeznaczony do wskazanej maszyny, próba na rodzaju kamienia | Nie jest automatycznie pełną rzeźbą 3D |
| Frezowanie kamienia CNC | Półfabrykat, osie i mocowanie, średnice narzędzi, dostęp do podcięć, tolerancje, CAM i symulacja kolizji | Oddzielny projekt technologiczny |

Trotec opisuje grawer kamienia jako powierzchniowy efekt matowienia przy niewielkim usuwaniu materiału. To podstawa do fotografii i wzorów na kamieniu; z tego opisu nie wynika zdolność dowolnego lasera do wyrzeźbienia kompletnej figurki z bloku. Wniosek projektowy: potrzebny jest wybór konkretnego wykonawcy i procesu, a nazwy „laser” i „CNC” nie mogą być używane zamiennie. [Trotec — Laser engraving stone](https://www.troteclaser.com/en/laserable-materials/laser-engraving-stone).

## Anatomia jako konkretne reguły modelowania

Siekacze mają korony z krawędzią tnącą, kły wyraźny guzek, zęby przedtrzonowe i trzonowe inne powierzchnie żujące. Korony nie powinny tworzyć prostego szeregu jednakowych kostek. Korzenie są osadzone w zębodołach szczęki i żuchwy; w uśmiechu nie trzeba pokazywać wszystkich zębów dorosłego uzębienia. To wiedza użyta do projektowania geometrii, nie trening wag modelu. [OpenStax — The Mouth, Pharynx, and Esophagus](https://openstax.org/books/anatomy-and-physiology-2e/pages/23-3-the-mouth-pharynx-and-esophagus).

Czaszka wymaga osobnego kształtu oczodołu, kości jarzmowej, szczęki i żuchwy; nie należy zastępować całej strony kostnej gładką połową elipsoidy z okrągłą dziurą. W referencji projektowej oko po stronie kostnej pozostaje ciemne i cofnięte. Jest to stylizacja tej konkretnej grafiki, a nie standard prawidłowej kompletnej czaszki anatomicznej. [OpenStax — The Skull](https://openstax.org/books/anatomy-and-physiology-2e/pages/7-2-the-skull).

## Uczciwe porównanie z Meshy

Dostępny dowód Meshy to zrzut ekranu użytkownika, także w widoku bez tekstur. Nie mamy jego pliku źródłowego do porównania zamknięcia, masy, materiałów, grubości ani identycznego oświetlenia. Archiwalne zestawienie dotyczy E15/E18, a nie zakończonego nowego E19. Nie publikujemy procentowego rankingu produktów ani zmyślonych metryk podobieństwa.

| Szczegół | Obserwacja z Meshy na screenie | Obserwacja FORGE / Astra + Blender | Granica wniosku |
|---|---|---|---|
| Twarz i uśmiech | Łagodniejsze, bardziej ciągłe przejście policzek–usta–żuchwa | E18R ma nienaturalny układ części zębów i zbyt płaskie obszary z boku ust | Meshy wypada lepiej w tym ujęciu tej postaci |
| Czaszka i szyja | W clay widać wyraźniej połączoną anatomię szczęki, żuchwy i szyi | Render E18R zawiera ostry wycięty brzeg szczęki i szczeliny widoczne od dołu | Zrzut nie dowodzi bezbłędnej całej bryły Meshy |
| Włosy | Duże falujące masy lepiej podążają za referencją | FORGE daje edytowalne włókna, ale ich liczba nie usuwa efektu zbyt równych sznurów | Włókna to cecha edycji, nie automatyczna przewaga realizmu |
| Materiały | Wygląd referencyjny na screenie, inne światło | E18R ma zweryfikowaną poprawkę nadmiernie białego sheen czarnej sukni | Nie porównujemy „jakości 8K” ze screenem |
| Wachlarz królowej | Brak obecnego źródła i pomiarów tego samego zadania Meshy | Istnieje nasz model wachlarza i wcześniejsza ocena użytkownika | Wcześniejsza pochwała jest obserwacją użytkownika, nie odtworzonym benchmarkiem |
| Szachownice | Użytkownik zgłosił błędne pola/kolory we wcześniejszych próbach | Repo ma mierzalne testy 64/512 pól i naprzemienności materiałów | Nie jest to nowy test wszystkich możliwości Meshy |
| Gotowość do sprzedaży fizycznej | Nie zmierzono pliku | E18R zmierzono i zablokowano jako gotowy master | Nie wolno twierdzić, że jeden render dowodzi produkcyjnej przewagi |

Meshy jest wartościowym punktem odniesienia dla rekonstrukcji obrazu. FORGE / Astra + Blender może uzupełniać taki workflow przez precyzyjne poprawki, kontrolę struktur, edycję materiałów i jawne raporty. Powyższe to obserwacje konkretnych dostępnych przykładów; nie dowód ogólnej przewagi któregokolwiek produktu.

## Bramka jakości dla klienta i wykonawcy

`production_gate.py` jest przygotowanym modułem do integracji. Host musi sam policzyć SHA256 bieżącego eksportu i odczytać zaufany wynik workera. Raport starszej rewizji, samo `manufacturing_ready=true` od modelu lub zaznaczenie „akceptuję wygląd” nie dopuszcza zlecenia fizycznego.

Proponowany przepływ: wygeneruj → faktycznie eksportuj i ponownie zaimportuj → porównaj przód/bok/tył i clay → uruchom audyt techniczny → pokaż klientowi widok oraz konkretne regiony błędów → popraw tylko te regiony → ponownie zmierz nowy plik → osobno zatwierdź wygląd oraz specyfikację produkcji. Wynik nieudanej próby zostaje do obejrzenia z oznaczeniem wersji roboczej.

Obecny moduł pozwala na przegląd wizualny, ale **nie autoryzuje fizycznego zamówienia**: w schemacie audytu v1 nie ma dowodów kompletnego badania grubości, przecięć, procesu ani próbki. Przeniesienie modułu do repo nie oznacza jeszcze podłączenia go do endpointu sklepu lub instalacji Oracle.

## Odtwarzanie audytu

```bash
blender -b --threads 2 --python audit_mesh_blender.py -- \
  --input FORGE-E18R.glb --output E18R-production-audit.json
python -m unittest discover -s . -p 'test_*.py' -v
```

`mesh_metrics.py` wymaga NumPy; opcjonalne SciPy przyspiesza wyznaczanie składowych, ale skrypt Blendera działa też bez SciPy. 16 testów przeszło: zamknięta kostka, szwy UV, rzeczywista dziura, odwrócona ściana, oddzielne bryły, degeneracje, błędne indeksy/liczby, mikroszczelina i bramka blokująca niewłaściwy SHA, wymiar oraz niepotwierdzone dopuszczenie.

Skrypt `build_print_candidate.py` został przygotowany do osobnej kopii finalnego E19. Samo jego istnienie nie oznacza ukończenia kandydata. Każdy rzeczywisty build ma własny `print-build-report.json` oraz audyt ponownego importu.

## Sprawdzenie wykonania pipeline

Mała rzeczywista scena kontrolna (walec i kula, robocze 100 mm) przeszła konwersję i ponowny import GLB: 53 916 trójkątów, jedna składowa połączona, zero krawędzi otwartych/ponaddwuściennych/niespójnych oraz zero degeneracji. Wysokość GLB wyniosła 100,000005 mm, algebraiczna objętość 13 562,194 mm³. To test działania skryptu i jednostek, **nie pomiar końcowego E19**. W kopii produkcyjnej łączenie szwów używa jawnej tolerancji 0,0001 mm; audyt źródłowy nadal łączy tylko identyczne pozycje. Wynik w `print-pipeline-fixture-verification.json`.
