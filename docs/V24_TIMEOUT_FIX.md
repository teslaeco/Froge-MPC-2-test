# FORGE v24 — naprawa timeoutu

FORGE v24 — naprawa timeoutu

Oracle Cloud Shell: Menu > Upload > froge-v24.zip

python3 -m zipfile -e "$HOME/froge-v24.zip" "$HOME/froge-v24"
python3 "$HOME/froge-v24/froge-v24.py"

Poczekaj na FROGE_V24_OK, odswiez strone i sprawdz polaczenie z Oracle.
Instalator zachowuje zapisane klucze, polaczenie, modele i kopie kodu.
Testy instalacji sa bez platnego API. Wersja 24 zawiera cala aktualizacje 23.

NAPRAWA
- Odbior Astry konczy sie na response.completed, nawet gdy polaczenie HTTP
  pozostaje otwarte. Nie czekamy na zamkniecie poprawnie zakonczonego strumienia.
- Planowanie ze zdjec: do 900 s; tekst: do 600 s. Ocena zdjec ma nadal osobne
  240 s. Nie zmieniono limitow tokenow ani liczby prob po timeoutcie.
- Gotowy, sprawdzony GLB jest zachowany, gdy limit przerwie dodatkowy eksport
  albo rendery. Kontrola sumy i nowy znacznik dla kazdej budowy odrzucaja
  pliki niekompletne i pozostalosci starszej proby.
- Timeout wskazuje etap: plan Astry, lokalne AI lub Blender. Zapisuje czasy
  i dostepny szkic odpowiedzi. Szkic nie jest uznawany za gotowy model.
- Ponowienie IDENTYCZNEGO opisu i zdjec po timeoutcie korzysta z poprawnego
  zapisanego planu, jezeli istnieje, bez kolejnego zapytania AI.

PO AKTUALIZACJI
Kliknij Ponow z tymi zdjeciami przy nieudanym zadaniu. Jezeli plan zdazyl sie
poprawnie zapisac, Blender wykona go bez AI. Gdy plan nie istnieje, ponowne
generowanie wymaga nowego zapytania do API i moze kosztowac.

Sprawdzono transport SSE, zachowanie pliku po przerwaniu, odrzucenie starego
znacznika oraz kod i natywny Blender. Nie uruchomiono nowej platnej generacji
i nie potwierdzono jakosci na kazdym zdjeciu. Ze starego ogolnego komunikatu
nie mozna ustalic, ktory etap przekroczyl czas. Nie twierdzimy, ze nowy limit
gwarantuje sukces kazdego zlecenia.
