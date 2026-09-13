# E18 — lokalna rekonstrukcja oczodołu, policzka, żuchwy i nasady włosów

E18 jest osobną kopią E17; E17 zachowano. Rozmiar całej głowy i geometria żywego oka pozostają bez zmiany. To nadal wynik roboczy, nie potwierdzone wierne odwzorowanie referencji.

## Wykonane zmiany geometrii

- Zmieniono lokalnie 73 852 wierzchołki obrysu oczodołu i jego wnętrza. Otwór ma łagodnie asymetryczny obrys, bardziej płaski górny łuk i dolnozewnętrzny narożnik. Pierwszą, zbyt prostokątną próbę złagodzono po ocenie clay.
- Gałkę, tęczówkę i źrenicę po stronie czaszki zmniejszono spójnie do 72% wcześniejszego wymiaru, cofnięto o 0,014 jednostki sceny i przyciemniono. Oko nadal istnieje, lecz nie dominuje jako wystająca jasna kulka.
- Wyrzeźbiono miejscowy relief kości policzkowej, zagłębienie poniżej jej łuku i korektę powierzchni żuchwy. Nie zmieniano całkowitej szerokości czaszki.
- Wygładzono 884 wierzchołki krawędzi otworu ust wraz z sąsiadującymi rzędami. Zwężono szczelinę przy kąciku, a samą geometrię dolnego brzegu żuchwy uniesiono pod dolny łuk zębowy. Zmniejszono przez to duży otwarty obszar pod zębami. To zmiana siatki, nie zamalowanie dziury.
- Czarną wkładkę jamy ustnej cofnięto o 0,018 jednostki i zmniejszono jej wysokość. Zewnętrzne zęby cofnięto zgodnie z łukiem, a ich wysokości skorygowano miejscowo.
- Zrelaksowano 22 768 wierzchołków w dolnym przejściu nosa, ograniczając część ostrych zmarszczeń geometrii.
- Dodano 440 kosmyków przy czole, dopasowując każdy punkt trafieniem promienia w rzeczywistą powierzchnię nasady. E17 używał dopasowania do najbliższego punktu, które ściągało część kosmyków na krawędzie i pozostawiało odsłonięty klin. E18 pokrywa ten obszar gęściej prawdziwymi włóknami.

Model zachowuje brązowe włosy po lewej obrazu i siwe po prawej, zgodnie z nową wskazówką użytkownika. Siwizna nie pochodzi z wcześniejszej referencji. Łącznie w E17 i E18 dodano 4360 nowych włókien, oprócz 312 zwężonych wcześniejszych rdzeni.

## Ocena i ograniczenia

Przed eksportem obejrzano rzeczywisty render Blender z teksturą i clay. Cofnięcie oka, zwężenie szczeliny pod zębami i zagęszczenie nasady są widoczne. Nadal pozostają nieregularności dolnego nosa, uproszczony kącik ust, zbyt regularne grupowanie włosów i niepełne anatomiczne odwzorowanie kości czaszki. Materiały fotograficzne wciąż wykonują znaczną część pracy nad podobieństwem twarzy; clay nie ma takiego samego poziomu szczegółu jak referencja ani porównywany screenshot Meshy.

Nie odtworzono pełnego układu kostnego ani różnych grup wieku w tym pojedynczym modelu. Nie wykonano treningu wag modelu AI. Proceduralne pory skóry z E17 są dostępne w masterze Blender; nie należy deklarować ich zachowania jako wypalonych map normal w FBX/GLB.

## Weryfikacja plików

Master: 6 315 947 trójkątów. Wzrost pochodzi przede wszystkim z dodatkowych włókien nasady. Nie oznacza automatycznie większego podobieństwa ani gotowości do druku czy gry.

Finalne pliki FBX/BLEND/GLB oraz osobny web GLB znajdują się obok tego raportu. `after-verification.json` dokumentuje ponowny import FBX: SHA-256, liczbę trójkątów, siatek z UV i brakujące tekstury. Renderami finalnego FBX są `after-face.png`, `after-front.png`, `after-angle.png`, `after-left.png`, `after-back.png`, `after-clay.png`. Wcześniejsze `preview-*` są podglądami Blendera sprzed eksportu.

Web GLB używa Draco6 i mniejszych map: kolor do1024px, normal/roughness do512px. Nie wykonano ręcznej decymacji; dokładną liczbę trójkątów po eksporcie i ponownym imporcie zapisano w `web-verification.json`. Różnice triangulacji między FBX i GLB należy podawać zgodnie z tym pomiarem.

Potwierdzony ponowny import web GLB: 6 315 623 trójkąty, 369 siatek, brak brakujących tekstur, 23 161 896 bajtów. Nieskompresowany GLB ma również 6 315 623 trójkąty, więc różnica 324 względem FBX występuje na etapie eksportu GLB, nie wynika z Draco.

Dodatkowy render `E18-HQ-2048x2560.png` ukończono z tego samego ponownie importowanego FBX: 2048×2560px, 32 próbki Cycles, odszumianie. Jest to wyższa rozdzielczość podglądu, nie osobny model ani dowód fotorealizmu. `hq-verification.json` wiąże obraz z SHA finalnego FBX.
