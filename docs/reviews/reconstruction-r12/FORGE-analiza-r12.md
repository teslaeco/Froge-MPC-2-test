# FORGE — analiza błędów i rekonstrukcja R12

## Wniosek

Zwiększenie liczby trójkątów z 1 do 2 milionów nie naprawiło podstawowych błędów odwzorowania. W poprzednich etapach zmieniły się materiały, pasma włosów, ubranie i niektóre fragmenty twarzy, jednak znaczna część powierzchni głowy zachowała wcześniejszy kształt. Przedstawianie liczby trójkątów jako głównego dowodu poprawy jakości było niewłaściwe.

## Pomiar zamiast oceny licznika

Porównałem powierzchnię głowy z wersji 1M z geometrią R11. Dla próbkowanych wierzchołków przedniej części głowy wyznaczyłem najbliższy punkt na siatce 1M. Próg niezmienności wynosił 0,00001 jednostki sceny.

| Obszar | Liczba próbek | Próbki na wcześniejszej powierzchni | Udział |
|---|---:|---:|---:|
| Cały badany przód głowy | 6858 | 4800 | 70,0% |
| Czoło | 622 | 622 | 100,0% |
| Pas oczu i policzków | 3170 | 2646 | 83,5% |
| Pas nosa | 1611 | 902 | 56,0% |
| Pas ust i brody | 1455 | 630 | 43,3% |

To próbkowanie wierzchołków według wysokości i położenia, a nie pomiar procentu powierzchni całego modelu. Nie uprawnia do stwierdzenia, że dokładnie 70% całej postaci jest identyczne. Pokazuje natomiast, że zasadnicza krytyka użytkownika jest uzasadniona. Podział trójkąta przez dodanie punktu w jego środku zachowuje jego powierzchnię: zwiększa licznik bez rekonstrukcji kształtu.

## Konkretne błędy

1. **Nasada włosów:** trójkątny, niemal symetryczny panel i poprzeczne, równoległe pasma. Referencja ma asymetryczne zejście włosów na skroń. Grubsza siatka istniejącego panelu tylko zachowywała ten błąd.
2. **Nos:** nieregularny, za duży otwór i ostre brzegi. Przesuwanie samych wierzchołków brzegu spowodowało dodatkowe fałdy; potrzebny był nowy układ ścian wokół otworu.
3. **Żuchwa:** osobna nakładka wystawała spod właściwej powierzchni brody. W widoku bez tekstur było widać odłączony półksiężyc. Zagęszczanie głowy nie scalało tego obiektu.
4. **Uzębienie:** zęby miały zbyt podobne korony, a dolny łuk był nadmiernie wyeksponowany. Tekstura nie zmienia ich obrysu.
5. **Szyja:** połączenie głowy z osobną powierzchnią klatki nadal jest niedopracowane. Próba usunięcia dolnego fragmentu głowy ujawniła nowe krawędzie; tę zmianę wycofano.
6. **Materiały:** część podobieństwa twarzy pochodzi z nałożonego zdjęcia, nie z wyrzeźbionych rysów. Na fotografii pozostaje oświetlenie referencji. Proceduralne pory i splot tkaniny są interpretacją materiału, nie odzyskaniem niewidocznych detali.
7. **Strój i sylwetka:** konstrukcja gorsetu, rękawów i fałd wciąż jest uproszczona. Samo zwiększanie rozdzielczości tekstur nie odtwarza konstrukcji ubrania.

## Co wykonano w R12

- Usunięto stary panel nasady włosów i 76 poprzecznych pasm. Zbudowano dopasowaną do powierzchni głowy, asymetryczną nasadę oraz 52 lokalne pasma prowadzące do skroni.
- Próby przebudowy nosa odrzucono po kontroli renderów: przesunięcie brzegu tworzyło fałdy, osobna łata dawała prostokątny obrys, a zszycie 1349 wierzchołków uporządkowanych kątowo tworzyło załamania. Przyczyną ostatniej porażki jest niezweryfikowane założenie, że zebrane krawędzie tworzą jeden kontur w projekcji. Przywrócono wcześniejszą powierzchnię głowy i zagłębienie nosa. Nos nie jest naprawiony.
- Usunięto odstającą nakładkę żuchwy i dodatkowy, oddzielny brzeg oczodołu.
- Zróżnicowano długości koron siekaczy i kłów oraz cofnięto dolne zęby.
- Poprawiono mapowanie odsłoniętego czoła. Pierwszą próbę z widocznym pasem błędnego UV odrzucono.
- Wprowadzono niewielką, miejscową zmianę krzywizny gorsetu. Nie oznacza to zakończenia rekonstrukcji stroju.

Nie wykonywano kolejnego globalnego zagęszczania dla samego licznika. Liczba trójkątów wynika z usunięcia wadliwych elementów i dodania nowych powierzchni.

## Jak oceniać wynik

Podglądy pochodzą z ponownie zaimportowanego FBX. Kamera zbliżenia została ustalona na podstawie głowy R11; zachowano kadr 640 × 800, światła i ustawienia renderowania. Porównanie przed/po zawiera wersję z materiałami oraz wersję bez tekstur. To pozwala oddzielić efekt zdjęcia i materiałów od rzeczywistej zmiany kształtu.

R12 jest częściową korektą i nie spełnia jeszcze żądania wiernej rekonstrukcji. Nasada włosów ma zmieniony obrys, ale nadal wygląda jak panel; zęby pozostają zbyt regularne. Nie przedstawiam tej wersji jako naprawionego modelu. Nie potwierdzono wiernego podobieństwa, poprawności całej anatomii ani gotowości do druku. Wciąż wymagają pracy: twarz i uśmiech, naturalność nasady włosów, połączenie szyi, oczodół oraz konstrukcja stroju. Tył i niewidoczne powierzchnie są interpretacją. Nie wdrożono zmian na Oracle ani na stronie.


## Następny zakres naprawy wynikający z analizy

1. Nos i okolica oczodołu: wyznaczyć rzeczywiste połączone pętle krawędzi, sprawdzić ich kolejność po sąsiedztwie siatki i dopiero wtedy budować powierzchnię. Sortowanie samych punktów według kąta nie zapewnia prawidłowej topologii. Zweryfikować nos bez materiałów, z przodu i z profilu.
2. Twarz: dopasować obrys nosa, policzka, kącika ust i brody do referencji. Zdjęcie jako kolor nie zastępuje modelowania rysów. Obecna pojedyncza referencja nie potwierdza geometrii tyłu głowy ani ukrytej strony twarzy.
3. Włosy: zastąpić widoczny panel przy czole stopniowym zagęszczeniem cienkich pasm prowadzonych od skóry; zachować zaakceptowane długie fale.
4. Szyja i ramiona: połączyć głowę i tułów ciągłą siatką z kontrolą przekrojów. Nie usuwać fragmentów tylko według wysokości.
5. Strój: odtworzyć linię dekoltu, szwy i kierunki fałd według referencji, a następnie ocenić ich wpływ na sylwetkę w neutralnym materiale.

Nie ustalono nowego arbitralnego limitu trójkątów jako kryterium jakości. Kryterium stanowi widoczna poprawa konkretnego obszaru przy identycznej kamerze, potwierdzona także bez tekstur.

Aktualna wersja robocza po wycofaniu wadliwej przebudowy nosa: 1955886 trójkątów. Ponowny import FBX potwierdził dokładnie tę liczbę, 417 obiektów siatkowych z UV i brak brakujących obrazów tekstur. To kontrola techniczna pliku, nie potwierdzenie podobieństwa.
