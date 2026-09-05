# Plan pracy: TikTok Shop i modele 3D na zamówienie

## Uzgodniony cel

Rozwijamy ForgeMCP w kierunku sprzedaży gotowych produktów i produktów wykonywanych na zamówienie. Klient ma tworzyć figurki lub inne części za pomocą AI, oglądać i zatwierdzać model, a wykonawca B2B ma produkować i wysyłać produkt. Agenci mają pomagać przygotowywać oferty, organizować zamówienia, produkcję, wysyłkę i obsługę klienta.

Docelowo cały świat. Dostępność TikTok Shop, warunki sklepu, dozwolone kategorie i obsługiwane kierunki dostawy trzeba sprawdzić dla konkretnego konta i rynku przed włączeniem sprzedaży. Ten dokument określa wymagania projektu; nie stanowi potwierdzenia bieżących uprawnień TikToka ani gotowości sklepu.

## Trzy rodzaje produktów

| Rodzaj | Dane wejściowe | Wynik |
| --- | --- | --- |
| Figurka personalizowana | Opis/referencja, styl, wielkość, kolor | Podgląd i plik modelu, zaakceptowana wersja do wykonania |
| Część użytkowa | Wymiary, jednostki, dopasowanie, materiał, zastosowanie | Model o kontrolowanych wymiarach i dokumentacja dla wykonawcy |
| Gotowy produkt w dropshippingu | Zweryfikowany katalog dostawcy, SKU, cena i dostępność | Oferta i zamówienie powiązane z dostawcą |

„Codex Micro” jest wcześniejszym pomysłem produktu do sprawdzenia, a nie potwierdzoną umową z producentem.

## Co mamy, czego brakuje

**Baza z konkursu:** React/TypeScript/Vite, proceduralna geometria, podgląd dokładnie generowanej siatki, eksport glTF i tekstury PNG, manifest QA, specyfikacja modelu, szkice produktu i zapytania B2B, koordynator, WebMCP i rejestr zdarzeń.

**Do wykonania:** podłączenie generatywnego modelowania AI, trwałe przechowywanie modeli i zamówień, logowanie klientów, adapter TikTok Shop, katalog wykonawców, rzeczywiste wyceny i dostawy, obsługa płatności właściwa dla kanału. Obecne szkice Shopify nie są integracją TikTok. Wynik dotychczasowego QA nie dowodzi drukowalności.

## Etapy z warunkiem ukończenia

1. **Podstawa sklepu i decyzje integracyjne.** Ustalić konto sprzedawcy i pierwszy rynek, wymagane uprawnienia TikTok, sposób personalizacji, pierwszy produkt, dostawcę generowania 3D i wykonawcę. Zweryfikować je w aktualnej dokumentacji i panelu usług. Gotowe, gdy znamy dostępny zakres integracji i testowy produkt; brak połączenia jest widoczny jako `NOT_CONNECTED`.
2. **Studio modelu.** Formularz opisu/referencji, wymiarów w mm, materiału i koloru; zlecenie generowania, postęp, obracany podgląd, wersje i pobranie plików. Presety lokalne oznaczone jako proceduralne; generowanie AI tylko po rzeczywistym wywołaniu podłączonej usługi. Gotowe, gdy podgląd, eksport i identyfikator wersji dotyczą tej samej geometrii.
3. **Przygotowanie do wykonania.** Kontrola skali, wymiarów, zamknięcia siatki, przecinania powierzchni, grubości ścian i możliwości procesu. Dla części funkcjonalnych wymagane tolerancje, materiał i uzgodnienie z wykonawcą; estetyczny render nie zastępuje modelu wymiarowego. Format produkcyjny, np. STL/3MF/STEP, dobierany do procesu i rzeczywistego eksportera. Gotowe po akceptacji wykonawcy i ocenie próbnego wydruku/wykonania.
4. **Oferta i wycena.** Agent przygotowuje tytuł, opis, warianty, wizualizacje, cenę i termin. Wizualizacje oznaczamy jako render, a zdjęcia próbki jako zdjęcia produktu. Wycena zapisuje walutę, koszt produkcji, dostawy, opłaty kanału, podatki według ustalonej konfiguracji i marżę; nieznanych składników nie podstawiamy jako zero. Gotowe, gdy rzeczywista wycena dotyczy zatwierdzonej wersji i ma termin ważności.
5. **TikTok Shop.** Implementacja adaptera według dostępnych operacji oficjalnej integracji, autoryzacja po stronie serwera, mapowanie SKU/wariantów, publikacja zaakceptowanej oferty i odbiór zamówień. Dane dostępowe poza repo i przeglądarkowym pakietem. Gotowe po potwierdzeniu zapisanej oferty i odczycie prawdziwego zamówienia testowego, jeśli dany kanał umożliwia test.
6. **Produkcja i wysyłka.** Przekazanie potwierdzonej wersji do wybranego wykonawcy, potwierdzenie przyjęcia, status produkcji, numer przesyłki i aktualizacje. Zapisywać identyfikatory kanału, zamówienia, modelu, wyceny i wykonawcy. Obsługiwać ponowione zdarzenia bez podwójnego zamówienia; stan płatności ma wynikać z potwierdzenia usługodawcy. Gotowe, gdy jeden produkt przejdzie pełny przebieg do potwierdzonego doręczenia.
7. **Kolejne rynki.** Rozszerzać po zweryfikowaniu jakości próbki, realnych kosztów, terminów, reklamacji i obsługi danego kraju. Dobierać wykonawcę według możliwości, jakości, kraju realizacji, kosztu i terminu.

## Podział pracy agentów — projekt docelowy

| Agent | Odpowiedzialność |
| --- | --- |
| Koordynator | Prowadzi zlecenie, statusy, zależności i wyjątki |
| Modelowanie 3D | Specyfikacja, generowanie, wersje i pliki |
| Kontrola modelu | Raport geometrii i wymagania wykonania |
| Oferty | Opis, warianty i propozycja ceny |
| Wykonawcy | Porównanie potwierdzonych możliwości i wycen |
| Zamówienia i wysyłka | Synchronizacja zamówienia, produkcji i przesyłki |
| Obsługa klienta | Przygotowanie odpowiedzi i obsługa wyjątków |

Publikowanie, zlecanie produkcji i przekazywanie danych wymagają zakresu upoważnienia właściciela i rzeczywiście podłączonej usługi. Kontrole mają odpowiadać konkretnym działaniom; decyzji o zatwierdzeniu projektu nie należy traktować jako dowodu zapłaty lub automatycznego zamówienia produkcji.

## Pierwszy cel wykonawczy

**Jedna personalizowana figurka:** opis → model → podgląd → akceptacja → wycena wykonawcy → próbny wydruk → oferta → zamówienie → wysyłka. Najpierw uzyskać ten działający przebieg, następnie dodawać kolejne figurki, części i kraje.

## Status po imporcie

Fundament i plan zapisane. Konta TikTok, dostawca generowania AI, produkcja, płatności i wysyłki nie są jeszcze podłączone. Nie opublikowano ofert ani nie wysłano zamówień do wykonawców.
