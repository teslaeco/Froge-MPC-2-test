# Polecenie wykonawcze Codexa — generator FORGE

Zaktualizuj istniejący generator strony i PR #8, zachowując jego działające funkcje. Meshy służy jako wzorzec oceny; nie podstawiaj jego modelu jako wyniku FORGE.

1. Popraw geometrię upiętej fryzury przy skroniach, za uszami i na karku. Zachowaj anatomiczną siatkę twarzy, UV i ruch oczu; dopasowanie skóry nie może deformować gałek ocznych. Oceniaj prawdziwe ujęcia GLB, w tym szare materiały.
2. Licz proceduralne mapy włosów, mikrostruktury skóry i kryształów w rozdzielczości wynikającej z wybranego profilu, maksymalnie 4096 px dla tych map. Zachowaj źródłowe fotografie do 8192 px, bez sztucznego powiększania. Podawaj rzeczywiste rozmiary i pochodzenie detalu.
3. Oddziel budżet zdjęć wejściowych od budżetu pełnych materiałów. Obsłuż zestaw 8K koloru + trzy mapy 4K, jeśli wystarcza RAM; odrzucaj przekroczenie przed zmianą obrazów. Nie obniżaj jakości po cichu.
4. Używaj ograniczonego kontenera 4 GiB dla zwykłych zleceń i 8 GiB dla profilu 8K. Przed AI sprawdzaj 10 GiB dostępnej pamięci dla trybu 8K. Zachowaj izolację, brak sieci w Blenderze, limity CPU/procesów i brak swapu.
5. Zachowaj plik Blender oraz GLB z materiałami. Wyłącz kwantyzację pozycji w eksporcie 4K/8K; nie upraszczaj modelu głównego. Sprawdź geometrię, UV, kolory i materiały po eksporcie i ponownym imporcie.
6. Dodaj wersjonowanie możliwości pracownika i komunikaty strony, zaktualizuj instalator z kopią i cofnięciem zmian, wykonaj testy, rzeczywistą generację oraz kompilację strony. Zapisz kod i wyniki w istniejącym PR.

Nie zmieniaj silnika gry, nie migruj chmury i nie uruchamiaj płatnych usług w ramach tej aktualizacji. Nie nazywaj wyższego rozmiaru pliku nowym szczegółem zdjęcia ani zgodnością z oryginałem. Odsłoń ograniczenia szablonu i szacowanie niewidocznej strony.
