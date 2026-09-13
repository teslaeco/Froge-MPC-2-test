# E17 — włosy i lokalne detale, wynik roboczy

Bazą jest E16. Nie zmieniono globalnej wielkości głowy ani położenia żywego oka. Nie osiągnięto jeszcze pełnego podobieństwa referencji.

## Zmiany faktycznie wykonane

- 312 istniejących rdzeni pasm zwężono do 50% ich wcześniejszego promienia. Wokół nich powstało 3120 osobnych, drobniejszych włókien o zwężających się końcówkach.
- Dodano 800 krótkich włókien układanych na powierzchni nasady włosów. Usunięto 52 wcześniejsze pasma nasady o tępo uciętych końcach. Łącznie powstało 3920 nowych włókien w prawdziwej geometrii.
- Po lewej stronie obrazu włosy mają sześć odcieni brązu, po prawej sześć odcieni siwizny. Siwizna jest nową wskazówką artystyczną użytkownika, nie kolorem wcześniejszego obrazu referencyjnego.
- Lokalnie dopracowano 18 koron zębów: zwężenie przy szyjce, delikatna krzywizna krawędzi, zmniejszenie głębokości i przesunięcie do wnętrza ust. Zmieniono kolor i szorstkość szkliwa.
- Dodano niewielki relief obojczyków i korektę obrysu gorsetu pod biustem. Nie powiększano całego tułowia.
- W pliku Blender dodano proceduralny relief porów skóry. Nie jest on wypaloną, przenośną teksturą normal: nie należy deklarować jego zachowania w FBX/GLB.

## Ocena wizualna i pozostałe braki

Zmiana koloru i grubości pasm jest widoczna. Nadal widać płaski klin nasady przy przedziałku; nowe włókna nie usunęły tego problemu całkowicie. Włosy nadal mają zbyt regularne grupowanie i nie osiągają fotorealizmu referencji. Uśmiech, powieki i połączenie twarzy ze szkieletem wymagają dalszego rzeźbienia.

W tej rewizji nie przebudowano oczodołu, żuchwy ani całej czaszki. Pozostały z E16, łącznie ze zbyt regularnym kształtem oczodołu i nieidealnym kącikiem ust. Żywe oko zachowano świadomie; nie powtórzono odrzuconego powiększenia głowy z R15. Widoki boku i tyłu dokumentują aktualny model, nie potwierdzają zgodności z niewidocznymi powierzchniami referencji.

## Pliki i weryfikacja

Master ma 5 922 115 trójkątów. Wzrost względem E16 pochodzi przede wszystkim z nowych włókien, nie z bezcelowego podziału całej twarzy. Taka liczba nie jest sama w sobie miarą podobieństwa ani gotowości produkcyjnej.

Rendery `after-face`, `after-front`, `after-angle`, `after-left`, `after-back`, `after-clay` pochodzą z ponownie importowanego FBX. `after-verification.json` zawiera jego SHA-256, liczbę trójkątów, siatek z UV i kontrolę dostępności tekstur. Ustawienia kamery i światła są takie same jak w podglądach E16. Obraz clay pokazuje faktyczną geometrię bez materiałów fotograficznych.

Osobna kopia `FORGE-model-E17-web.glb` używa Draco i obniżonej rozdzielczości tekstur: kolor maksymalnie 1024 px, mapy normal/roughness maksymalnie 512 px. Nie wykonano ręcznej decymacji. Ponowny import GLB wykazał 5 921 791 trójkątów, o 324 mniej niż FBX; ten sam wynik ma indeksacja nieskompresowanego GLB, więc różnica pochodzi z eksportu GLB, nie z zastosowania Draco. `web-verification.json` dokumentuje rzeczywisty ponowny import GLB. Master BLEND/FBX/GLB zachowuje wyższe rozdzielczości.

Nie przeprowadzono fizycznego druku, riggingu, animacji tej postaci ani treningu wag modelu AI w ramach tego skryptu. E17 jest lokalną edycją modelu; zmiany generatora i jego procedur oceny muszą być weryfikowane osobno.
