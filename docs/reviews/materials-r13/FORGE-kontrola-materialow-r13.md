# FORGE R13 — kontrola materiałów twarzy i stroju

## Cel i zakres

Poprawka materiałów na zachowanej geometrii R12. Nie zwiększano liczby trójkątów ani nie uznawano jej za dowód jakości. Wymaganie wiernego odwzorowania całej postaci nadal pozostaje otwarte.

## Ustalenia

- Poprzedni materiał sukni zawierał duże proceduralne plamy, które dominowały nad splotem. UV rozciągało ten sam wzór inaczej na rękawach i tułowiu.
- Twarz korzystała z wcześniejszej referencji z mniejszą twarzą w kadrze. Jej kolor zawiera także oświetlenie zapisane na ilustracji.
- Materiał fotografii miał zbyt jednolitą odpowiedź na światło dla żywej skóry i kości.
- Pierwsza próba R13 wyglądała zbyt gładko. Kontrola importu FBX wykazała obecność map szorstkości i normalnych: nie był to brak tych map w pliku. Zwiększono matowość i drobną zmienność włókien. Kolejny regularny wzór sinusoidalny dawał kratkę; zastąpiono go drobnym, filtrowanym szumem o stałym ziarnie losowym.

## Wykonane zmiany

1. Nowe mapy PBR tkaniny: kolor, szorstkość i normalne w rozdzielczości 2048 × 2048, osobno dla kremowej i ciemnej połowy. Splot ma nominalny okres około 0,8 mm w kaflu 200 mm; rozmiary są przybliżeniem na nieidealnych UV, nie pomiarem fizycznej tkaniny.
2. Różne powtórzenia UV dla tułowia (6 × 3,35) i rękawów (1,8 × 2,85), aby ograniczyć różnicę skali włókien. Zachowano istniejące szwy i nadano im osobny kolor. Geometria szwów nie została przebudowana.
3. Dwa materiały twarzy: żywa połowa z delikatniejszym mikroreliefem, szkieletowa z większą szorstkością. Mapa szorstkości różnicuje usta, nos i policzek; obszary są przybliżone, nie wynikają z odzyskanych pomiarów materiałowych.
4. Ostatnią referencję Screenshot_20260912-170529.png dopasowano do wcześniejszej przez minimalizację różnic RGB w 4524 próbkach twarzy. Skala 1,339954; przesunięcie x −163,5078 px, y −140,0902 px; błąd RMS RGB 0,00851 w skali 0–1. Zmieniono współrzędne UV, pozostawiając obraz źródłowy bez edycji. To ta sama ilustracja w większym kadrze; nie twierdzimy, że powstały nowe, odzyskane szczegóły twarzy.
5. Usunięto niepodłączone węzły z używanych materiałów. Tekstury są osadzone w plikach modelu.

## Weryfikacja

Podglądy powstają z ponownie zaimportowanego FBX, a nie z wygenerowanej ilustracji. Kamera i światła odpowiadają R12, próbki renderowania zwiększono z 24 do 48, aby ograniczyć szum. Kontrola obejmuje twarz na wprost i pod kątem, całą postać z przodu/boku/tyłu oraz zbliżenie tkaniny.

## Granice wyniku

R13 nie naprawia niewłaściwego obrysu nosa, sztucznej nasady włosów, połączenia szyi ani geometrii uśmiechu. Część charakterystycznych cech nadal istnieje tylko w kolorze zdjęcia. Materiał twarzy zawiera oświetlenie referencji, co ogranicza naturalność przy innych światłach i kątach. Wzór włókien tkaniny jest autorską interpretacją widocznego materiału. Nie potwierdzono zgodności z oryginałem ani gotowości modelu dla klienta. Poprzednia wersja R12 została zachowana. Nie wdrożono tej próby na Oracle ani na stronie.

Końcowy import FBX potwierdził 1 955 886 trójkątów, 417 obiektów z UV i brak brakujących obrazów tekstur. Geometria i liczba trójkątów są takie same jak w R12.

## Własna ocena końcowych podglądów

Widoczny regularny wzór kratki został usunięty; kremowa tkanina ma drobniejszą, nieregularną fakturę i czytelne istniejące szwy. Ciemna połowa pozostaje wizualnie zbyt jednolita, a faktura kremowej części jest nadal miękka w tej rozdzielczości renderu. Nie potwierdzam wiernego odtworzenia tkaniny z referencji. Zmiana twarzy jest subtelna: sama wymiana źródła i szorstkości nie rozwiązała podobieństwa ani deformacji pod kątem. Gotowość dla klienta: NIE. Ten etap dostarcza sprawdzony technicznie plik roboczy i udokumentowaną korektę materiałów, nie kończy rekonstrukcji.
