# FORGE R14 — zęby, oczy, szyja i karnacja

## Wykonane zmiany

- Przebudowano 18 koron zębowych. Zamiast dawnych brył powstały wypukłe powierzchnie z zaokrąglonymi narożami, zwężeniem przy szyjce i zróżnicowanymi proporcjami siekaczy, kłów oraz zębów bocznych. Krawędzie sieczne skorygowano po pierwszym renderze, który dawał zbyt owalny kształt. Dolne zęby cofnięto bardziej niż górne. Ciepła barwa szkliwa ma delikatny gradient przy szyjce.
- Żywe oko pomniejszono o 4% w płaszczyźnie twarzy i cofnięto o 0,0012 jednostki sceny. Zachowano istniejące powieki i tekstury.
- Zgodnie z nową prośbą dodano oko do oczodołu czaszki: osobną gałkę, brązową tęczówkę i źrenicę. Jest celowo osadzone głęboko i ciemne. Pierwszą, zbyt jasną wersję cofnięto jeszcze o 0,009 jednostki i przyciemniono. Wcześniejsze wymaganie pustego oczodołu nie jest stosowane do tej wersji, ponieważ użytkownik poprosił o oko.
- Płynnie skrócono odcinek szyi: powierzchnie powyżej przejścia przesunięto w dół o 0,032 jednostki sceny, z łagodnym przejściem między wysokościami 1,30–1,445. Głowa, oczy, uzębienie i włosy zostały przemieszczone tą samą funkcją. Są to jednostki sceny, nie centymetry gotowej figurki po przeskalowaniu do 10 cm.
- Dopasowano 35 949 wierzchołków dolnego fragmentu głowy do węższego przekroju wewnątrz szyi. Nie wycinano kolejnego otworu i nie deklarujemy zespawania głowy z tułowiem: obiekty pozostają osobne.
- Dodano niewielką wypukłość żywego policzka, zachowując jego UV. Zmieniono karnację ramion, szyi i tułowia na cieplejszą oraz przyciemniono wnętrze ust. Skorygowano bladość pierwszego wariantu.
- Ograniczono połysk ciemnej sukni. Zachowano materiały i splot R13; nie przebudowywano w tym etapie konstrukcji stroju.

## Kontrola techniczna i podglądy

Źródło: zachowana wersja R13. Podglądy powstają po ponownym imporcie FBX. Kontrola obejmuje twarz na wprost, twarz pod kątem, przód, lewy bok, tył i neutralny materiał bez tekstur. Zachowano kamerę i światła porównania; przesunięcie głowy wynika z faktycznego skrócenia szyi. R14 używa 32 próbek renderu; wcześniejsze R13 używało 48.

Liczba trójkątów wynikająca ze sceny: 1 990 254. Nie dodawano płaskich podziałów, żeby osiągnąć arbitralny licznik. Przyrost wynika głównie z nowych koron i elementów oka. W nowych koronach przeliczono normalne na zewnątrz i sprawdzono dodatnią objętość każdej zamkniętej bryły; nie zastępuje to kontroli całej postaci pod kątem druku. Eksport ma zachować dwie gałki oczne, UV i osadzone tekstury; wynik importu znajduje się w raporcie technicznym.

## Ograniczenia

To korekta modelu, nie potwierdzona wierna rekonstrukcja ani model zatwierdzony dla klienta. Nadal wymagają pracy: naturalność nasady włosów, obrys otworu nosowego, podobieństwo i ciągłość powierzchni twarzy oraz szczegóły konstrukcji sukni. Kolor żywej twarzy nadal pochodzi w dużej mierze z fotografii referencji zawierającej jej oświetlenie. Cienie w renderze wynikają także ze świateł i geometrii; nie zostały przedstawione jako odzyskane fizyczne właściwości skóry. Tył i niewidoczne partie są interpretacją. Nie potwierdzono szczelności ani gotowości do druku.

Nie wdrożono zmian na Oracle ani na stronie. Zachowano wcześniejsze pliki.

## Wynik kontroli końcowej

Ponowny import FBX: 1 990 254 trójkąty, 420 obiektów siatkowych z UV, dwie gałki oczne i brak brakujących obrazów tekstur. Podglądy zapisano po utworzeniu końcowego FBX. W neutralnym materiale widać zaokrąglone korony, rzeczywistą gałkę wewnątrz oczodołu i krótszą szyję. Pod kątem zęby nadal wymagają dopracowania łuku i połączenia z tkankami ust; nie są traktowane jako rekonstrukcja stomatologiczna. Oko w czaszce jest widoczne i głęboko osadzone, lecz jego pozycja i wygląd są interpretacją prośby użytkownika, nie potwierdzoną rekonstrukcją niewidocznej anatomii. Poprawa proporcji szyi nie oznacza połączenia topologii głowy i tułowia.
