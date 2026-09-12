# E15 — powrót do R14 i porównanie z Meshy

R15 został odrzucony przez Sebastiana: pogorszył podobieństwo i proporcje głowy. E15 zbudowano od nowa z zachowanego R14. Nie wykorzystano deformacji czaszki, oczu ani tułowia z R15.

## Konkretna poprawka E15

Geometria głowy, oczy, zęby, ciało i UV są identyczne z R14. Sprawdzono skróty współrzędnych wierzchołków, transformacji i UV dla 55 obiektów spoza fryzury. Dotychczasowe wady tych powierzchni pozostają; ta poprawka naprawia regresję R15, nie stanowi nowej rekonstrukcji twarzy.

Zmodyfikowano 312 prowadnic włosów: promień pasm zmniejszono o 22%, a nadmiernie odsuniętą zewnętrzną część fryzury zbliżono do głowy. Szerokość całej grupy tych pasm spadła z 0,4449 do 0,4045 jednostki sceny, czyli o około 9,1%. Nie jest to pomiar szerokości czaszki — czaszka pozostała z R14. Włosy otrzymały bardziej matową odpowiedź materiału.

Model ma 1 990 254 trójkąty po uwzględnieniu modyfikatorów, tyle co R14. Surowe siatki bez modyfikatorów mają 1 989 930 trójkątów. Nie dodawano wielokątów w celu podbicia licznika. R15 miał 6 419 299 trójkątów i mimo tego został słusznie odrzucony pod względem podobieństwa.

## Meshy kontra nasz model Astra + Blender

Porównanie opiera się na dwóch screenach użytkownika: Screenshot_20260912-190442.png (tekstury) oraz Screenshot_20260912-190054.png (geometria). Nie udostępniono pliku 3D z Meshy. Kamery, perspektywa, oświetlenie i skala podglądów są różne, dlatego nie jest to pomiar błędu rekonstrukcji ani test wydajności.

| Element | Meshy na dostarczonych screenach | Nasz E15 oparty na R14 |
|---|---|---|
| Rysy twarzy | Bliższy referencji obrys policzka, oczu i uśmiechu | Zachowane rysy R14, nadal uproszczone |
| Uśmiech i uzębienie | Lepsze włączenie zębów w usta i linię szczęki | Widoczne osobne korony; nadal sztuczna krawędź ust |
| Czaszka i nos | Spójniejsze przejścia oczodołu, nosa i policzka | Otwór nosowy i przejścia powierzchni wymagają przebudowy |
| Szyja | Ciągła forma z czytelnymi detalami | Nadal widoczne uproszczenia i połączenie części |
| Fryzura | Lepsza masa i kierunek fal, szczególnie przy czole | Węższa niż poprzednio, lecz nadal regularne grube pasma i nienaturalna nasada |
| Ubranie | Wyraźniejsza konstrukcja gorsetu, krawędzie i fałdy | Mniej wierna konstrukcja i zbyt regularna powierzchnia |
| Detale sceny | Widoczne elementy taśmy filmowej i otoczenia | Brak ich w naszym modelu |
| Liczba trójkątów | 3 057 126 według interfejsu na screenie | 1 990 254, sprawdzone po imporcie FBX |

Widok bez tekstur pokazuje, że podobieństwo naszego żywego oka i mimiki w dużym stopniu zależy od tekstury. Sama powierzchnia nie odtwarza tych cech wystarczająco. To istotniejszy problem niż liczba wielokątów.

**W tej konkretnej próbie Meshy wygrywa podobieństwem i spójnością geometrii.** Większa liczba trójkątów R15 nie pomogła, ponieważ problem dotyczył podstawowego kształtu i połączeń powierzchni. E15 przywraca preferowaną bazę R14, ale nie dorównuje jeszcze wynikowi Meshy.

Nie oceniono pliku Meshy pod względem UV, liczby oddzielnych obiektów, szczelności siatki, jakości eksportu, czasu ani kosztu generacji. Zielony znacznik drukowalności na screenie nie jest przeprowadzonym przez nas testem.

## Weryfikacja i status

Rendery E15 powstały z ponownie zaimportowanego FBX. Porównanie R14/R15/E15 ma identyczną kamerę i oświetlenie. Zestaw Meshy/E15 jest opisanym porównaniem screenów i renderów, z zachowaniem proporcji wycinków. Nie użyto generatora obrazów do udawania wyniku 3D. Model pozostaje wersją roboczą do oceny; nie zaakceptowano podobieństwa ani gotowości do druku. Nie wdrażano zmian na Oracle ani na stronie.
