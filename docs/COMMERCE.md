# Froge — katalog i przygotowanie sprzedaży

Panel `/shop` rozszerza istniejące studio. Studio pozostaje na `/`, a wcześniejsze laboratorium i fundament konkursowy zachowano.

## Zaimplementowane

- Prywatny katalog w D1, przypisany do uwierzytelnionego użytkownika Sites. Brak tożsamości oznacza HTTP 401. Każdy odczyt/zapis jest ograniczony kluczem właściciela.
- Zapis i edycja szkiców, status do sprawdzenia i archiwizacja. Rewizja produktu chroni przed nadpisaniem zmian z innej karty. Błąd nie czyści formularza.
- GLB 2.0 i Froge JSON do 12 MB przechowywane w prywatnym R2. Odczyt tylko dla właściciela. Upload sprawdza nagłówek GLB lub schemat sceny JSON; nie zastępuje kontroli drukowalności.
- Ze studia można zapisać widoczny model jako produkt: GLB uwzględnia skalę i obrót. Katalog otwiera zapisany produkt.
- Cena, wykonanie, dostawa, opakowanie, procent opłat i kwota na cel społeczny. Saldo przed podatkami, kosztami stałymi i zwrotami. Wszystkie kwoty trzeba podać na spójnej podstawie. Brak automatycznie założonych stawek podatków/prowizji.
- Oznaczenie non-profit bez automatycznych płatności lub darowizn.
- Shopify CSV z aktualnymi nagłówkami, stabilnymi unikalnymi handle/SKU, poprawnym quotingiem i statusem draft / published false. Eksportuje tylko zapisane, niearchiwalne produkty w wybranej walucie. Waluta sklepu musi zgadzać się z wybraną: CSV nie koduje waluty ani nie przelicza kwot. Nie przenosi załączników 3D ani stanów magazynowych. Dostarczenie plików cyfrowych klientom wymaga dodatkowej konfiguracji Shopify.
- Tekstowy szkic TikTok oraz niewysłane zapytanie B2B. Nie są to importy ani wysłane oferty.
- WebMCP: `list_froge_products`, `save_froge_product`, `prepare_froge_offer`. Funkcje dotyczą katalogu Froge, nie wykonują operacji w sklepach zewnętrznych.

## Granice aktualnego wdrożenia

- Brak aktywnego backendu Blender/Ollama na Oracle. Konto chmurowe użytkownika aktywne, lecz nie potwierdzono dostępu wykonawczego do serwera. Przycisk przygotowania polecenia nie uruchamia zdalnego agenta.
- Integracja Shopify dostępna w rozmowie nie jest automatyczną integracją Worker → Shopify. Konkretny sklep wymaga osobnej autoryzacji. Nie zapisujemy kluczy API w przeglądarce ani Git.
- Brak automatycznej synchronizacji Shopify/TikTok, pobierania zamówień, płatności i wysyłek. Operacje te wykonuje się w autoryzowanym sklepie. W panelu nie ma fikcyjnych zamówień, przychodów lub podłączonych kanałów.
- Kanał TikTok Shop w Shopify wymaga kwalifikującego się kraju sklepu. W sprawdzonej dokumentacji z 06.09.2026 Polska i Holandia nie są wymienione. Nie zmieniamy ani nie wymyślamy adresu rejestracji.
- Panel pozostaje prywatny. Nie stanowi publicznej kasy sklepowej.
- Limit katalogu 500 produktów; modele maksymalnie 12 MB. Pliki przesłane i następnie porzucone nie są automatycznie usuwane. Potrzebna późniejsza polityka retencji przed dużą skalą.

## Weryfikacja

Testy obejmują obliczenia, format bezpiecznych szkiców, odmowę dostępu bez zalogowania, kontrolę Origin, limit żądania, scope właściciela, rewizje oraz zachowanie formularza po błędzie. Migracja Drizzle jest schema-only. Produkcyjny build wymaga skopiowania `drizzle` do `dist/.openai/drizzle`.

Źródła:
- https://help.shopify.com/en/manual/products/import-export/using-csv
- https://help.shopify.com/en/manual/products/import-export/import-products
- https://help.shopify.com/en/manual/online-sales-channels/social-commerce/tiktok/setup
