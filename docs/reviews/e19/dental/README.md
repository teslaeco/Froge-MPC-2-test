# E19 — zęby, wnętrze ust i oko szkieletowej połowy

Skrypt `apply_dental.py` udostępnia `apply()` i działa na otwartej kopii E18R. Nie zapisuje źródła i odmawia ponownego zastosowania do tej samej sceny. Uruchomienie jako główny skrypt zapisuje izolowany `dental-test.blend`.

## Wykonane zmiany

- Zastąpiono 18 starych obiektów zębowych 24 zamkniętymi koronami: po 12 w łuku górnym i dolnym. Siekacze centralne są szersze, boczne mniejsze, kły mają łagodny pojedynczy guzek; boczne korony cofają się po łuku. To zestaw do tej widocznej rekonstrukcji, nie pełne 32-zębowe uzębienie anatomiczne.
- Dodano cztery ciągłe łoża korzeni (dwie połowy szczęki i żuchwy), o barwie dziąsła na żywej stronie i ciemnej kości na szkieletowej. Korzenie przecinają objętość łoża, co sprawdzono geometrycznie. Końce łuków zakrzywiają się przyśrodkowo (X 43→16 mm) i w głąb szczęki/żuchwy, aby nie wystawały jako poziome pręciki.
- Usunięto źle umieszczoną dawną `Recessed oral cavity`: jej środek Z wynosił 1.484, podczas gdy zęby mieściły się około 1.45–1.46. Nowa zamknięta głębia ust jest przy Z 1.453 i cofnięta za łuki, aby nie zasłaniać bocznych zębów.
- Oko po szkieletowej stronie jest obecne, ciemne i cofnięte, o średnicy 24 mm w skali źródła; ma osobną ciemną tęczówkę i źrenicę. Nie dodano białej wystającej gałki.
- Lokalnie zmniejszono pionowe rozwarcie obręczy oczodołu (maksymalny współczynnik przemieszczenia 10,5%), zachowując niezmieniony obrys głowy. Zlikwidowano szarą płaską barwę wnętrza oczodołu.

## Weryfikacja

`verify.py` sprawdza zamknięcie nowo dodanych siatek i położenie końcowego pierścienia każdego korzenia względem odpowiadającego mu łoża. Wszystkie dodane siatki mają zero krawędzi brzegowych/non-manifold; w każdym zębie 10–40 spośród 40 próbek pierścienia korzenia leży wewnątrz łoża. To świadczy o osadzeniu geometrycznym, nie o wykonaniu unii boolowskiej.

Minimalne i maksymalne współrzędne całej głowy są identyczne z E18R. Render `render-test.py` wykonuje przód, skos od strony czaszki i widok od dołu, w Cycles z tą samą konfiguracją światła.

## Ograniczenia

Cała twarz nadal jest przybliżeniem, a nie dokładną kopią osoby z referencji. Profil czaszki, okolica nosa, żywe oko i przejście żuchwa–szyja nadal wymagają pracy. Nie wykonano unii całej postaci, analizy minimalnej grubości ani certyfikacji druku. Struktury kości nie odpowiadają kompletnej czaszce medycznej. Referencja frontalna nie ustala anatomii powierzchni niewidocznych.

Podstawa rozróżnienia typów koron: OpenStax Anatomy and Physiology 2e, 23.3, https://openstax.org/books/anatomy-and-physiology-2e/pages/23-3-the-mouth-pharynx-and-esophagus . Źródło opisuje typy zębów i osadzenie w wyrostkach zębodołowych; nie zatwierdza tego modelu.
