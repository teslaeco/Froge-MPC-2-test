# FORGE — Astra + Blender

## Aktualne polecenie Sebastiana

Porownanie do Meshy oznacza oczekiwana jakosc, NIE integracje z Meshy.
Jedynym modelem AI dla zdjec ma pozostac Astra przez istniejace OpenAI API.
Nie dodawaj kolejnego platnego dostawcy, klucza ani przekazywania mu zdjec.

Astra ma analizowac konkretne przeslane obrazy, ich proporcje, twarz, fryzure,
stroj, dodatki, kolory i materialy. Blender wykonuje sprawdzony plan geometrii,
UV, materialow i tekstur. Zachowuj oryginalna referencje; wyniki pomiarow musza
byc zwiazane z dokladnymi bajtami aktualnego zdjecia. Czesci niewidoczne sa
rekonstrukcja, nie pomiarem. Nie uzywaj punktow innej modelki ani deklaracji
4K/8K jako dowodu zgodnosci. Zachowaj pelne modele, FBX, GLB, OBJ i BLEND.

Uzywaj gpt-6-astra z reasoning.effort=max dla analizy zdjec i renderow.
Oceniaj rzeczywiste widoki przodu, boku, tylu, twarzy i trzy-czwarte. Poprawiaj
plan na podstawie konkretnych wad; zachowuj poprzedni wynik i wspolny limit
czasu. Samo przejscie testow kodu nie potwierdza realistycznego podobienstwa.
Nie oznaczaj pracy jako zakonczonej wizualnie bez faktycznej generacji i oceny.

## Wykonane w v22

- Usunieto integracje zewnetrznego silnika i blokade nowych zdjec bez jego klucza.
- Przywrocono sciezke Astra -> zweryfikowany plan -> Blender -> ocena Astry.
- Przywrocono pomiary 478 punktow zdjecia w przegladarce i wymagania zgodnosci.
- Wysilek dla wejsc obrazowych zmieniono high -> max, limit odpowiedzi 9000 ->
  24000 tokenow, przy zachowaniu lacznego limitu czasu. To nie obietnica jakosci.
- Dodano profil i tyl do rzeczywistych renderow dla oceny. Zachowano eksport FBX.
- Instalator v22 korzysta z istniejacego OpenAI, bez trzeciego polecenia;
  pokazuje postep co 15 s. Stan polaczen i modeli pozostaje zachowany.

W tej sesji nie wykonano platnej generacji postaci ani publikacji strony.
Screenshot uzytkownika potwierdza instalacje v21 na Oracle. V22 wymaga
zainstalowania nowej paczki. Wczesniejszy blad pobierania kodu strony HTTP 500
pozostaje odnotowany; nie deklarowano jego naprawienia.

Oficjalne mozliwosci Astry, sprawdzone 2026-09-11:
https://developers.openai.com/api/docs/models/gpt-6-astra
Model przyjmuje obrazy, zwraca tekst/kod i moze sterowac narzedziami. Nie
traktuj go jako gotowego, wytrenowanego silnika rekonstrukcji siatki 3D.
