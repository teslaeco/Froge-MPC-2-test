# Polecenie dla Codexa — FORGE MCP: wierna rekonstrukcja i tekstury 4K/8K

Kontynuuj istniejący Froge-MPC-2-test, przeczytaj AGENTS.md oraz docs/WORK_CHECKPOINT.md. Nie zastępuj nowszego generatora starszym PR. Wykonaj realne zmiany kodu i sprawdź je w Blenderze, następnie otwórz PR do main.

Celem jest zachowanie widocznej geometrii twarzy, anatomii, fryzury, kroju i kolorów oryginalnej kreacji: dopasowanej szmaragdowo-turkusowej sukni, niebiesko-srebrnego kołnierza, lekkich naramienników, odsłoniętego fragmentu skóry pod pachą, rękawiczki bez palców z nieregularnymi srebrnymi płytkami, kolczyków i kryształowego wachlarza z mechanizmami. Nie zastępuj sukni bluzą ani grubym pancerzem. Modelka ma naturalną skórę, charakterystyczne policzki, nos i usta, spójny kierunek wzroku, makijaż, rzęsy, włosy prowadzone nad uchem i za ucho. Pięć palców, paznokcie i rzeczywisty chwyt wachlarza są obowiązkowe.

1. Zachowaj źródło i wersje. Zmiana tekstur nie może przebudowywać geometrii, pozy, UV ani przypisania materiałów. Każdą edycję konkretnej części porównuj z poprzednim GLB; nie poprawiaj jej przez niezwiązany nowy preset. Skontroluj, czy powtórnie zapisane to samo zdjęcie nadal uruchamia właściwe mapowanie.
2. Obsłuż referencje do 4096 i 8192 px z kontrolą bajtów i pamięci, bez cichego rozciągania czy upscalingu. Pokaż rzeczywisty rozmiar źródła i tekstur w raporcie. 4K/8K tekstur, rozdzielczość renderu i jakość geometrii to osobne parametry. Mały obraz nie staje się źródłem 8K.
3. Dopasowuj siatkę na podstawie mierzonych punktów i zgodnych ujęć tej samej osoby. Utrzymuj grubość ubrania, ostre krawędzie dodatków i ciągłość UV. Niewidoczny tył i dół oznacz jako rekonstrukcję. Wyższa liczba wielokątów ani fotograficzne odbicia w teksturze nie dowodzą zgodności.
4. Materiały skóry, włosów, metalu i tkaniny muszą zachować kolory. Nie nazywaj zdjęcia z oświetleniem mapą fizycznego albedo. Nie wytwarzaj detali twarzy przez losowy szum ani nie nazywaj dopasowania uczeniem wag AI.
5. Uruchom aktualny generator, eksport GLB, ponowny import i rzeczywiste rendery: sylwetka, twarz z przodu, profil, trzy czwarte, dłoń i strój. Zapisz SHA pliku użytego do renderów. Porównaj z oryginałem i popraw wykryte błędy; nie używaj ilustracji jako renderu modelu.
6. Sprawdź transport zdjęć UI → API → Oracle, wersję/capabilities pracownika, zachowanie ustawień przy ponowieniu, pakiet aktualizacji, skalę i materiały GLB. Nie deklaruj wdrożenia na Oracle bez potwierdzenia health i nowej generacji na tym serwerze. Nie uruchamiaj nowych płatnych usług ani sprzedaży.
7. Kryterium zakończenia rekonstrukcji: wizualna zgodność stroju i twarzy zaakceptowana przez Sebastiana. Dopóki to nie nastąpi, oznacz PR jako draft i nazwij pozostałe różnice. Testy techniczne nie są oceną podobieństwa.

## Implementacja w tym PR

Nowszy generator v20/v25; obsługa referencji i maksymalnego eksportu tekstur 2K/4K/8K; brak automatycznego powiększania; eksport zachowujący proporcje; kontrola geometrii/UV/pozy/przypisań materiałów; rozpoznanie tej samej kompozycji po ponownym kodowaniu JPEG; ograniczenia rozmiaru i pamięci; raport rzeczywistych tekstur oraz capability referenceQualityRevision=1. Dalsza ręczna rekonstrukcja twarzy, włosów i stroju pozostaje konieczna. To aktualizacja programu, nie nowo wytrenowany model generatywny.
