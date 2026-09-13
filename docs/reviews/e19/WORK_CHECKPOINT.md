# E19 — korekta anatomii i audyt produkcyjny w toku

Użytkownik 2026-09-13 zlecił naprawę uzębienia, oka po stronie czaszki, ciała, włosów, tekstur 8K, audyt wykonania fizycznego i scalenie PR #11 jeśli jest poprawny.

## Krytyczne sprostowanie wydania

Przegląd dokładnego commitu `0d60cf205c1ebf11646b272fc0b2ed02c47f6ddf` wykazał, że `server.py` i `apply_update.py` nadal miały wersję 33. Serwer nie wywoływał zapowiedzianej kontroli przy akceptowaniu wyniku. Stary ZIP nazwany v34 odtwarzał ten kod, mimo zgodności payloadu z CI. **Nie używać wcześniejszej paczki v34; przygotowywana jest poprawiona v35 z testem kodu rzeczywiście zawartego w paczce.** Poprzednie twierdzenia o działającym hostowym gate i poprawnej identyfikacji v34 są skorygowane przez ten audyt. Nie potwierdzono instalacji na Oracle.

## Prace równoległe

- Zęby/oczodół: korekta rzeczywistej geometrii, sprawdzenie uśmiechu od dołu i profilu; znaleziono położenie starszej jamy ustnej około 3 cm powyżej zębów.
- Ciało/skóra: wspólna deformacja torsu, stroju i szwów; rzeczywiste bake map 8192x8192 na UV torsu. Brak deklaracji nowej fotograficznej informacji 8K twarzy.
- Włosy: korekta istniejących długich pasm, zachowanie poprzedniego brązowo-siwego podziału.
- Audyt: osobno topologia wizualnego mastera i profil wykonania fizycznego. Bez deklaracji gotowości do druku na podstawie liczby trójkątów.
- PR #11: aktualna baza 5c02f9ff..., head 0d60cf2; CI head przeszło, lecz wspomniany błąd wydania blokuje merge do naprawy i ponownego sprawdzenia.

Źródłowy E18R pozostaje nienaruszony w `resume-model/FORGE-E18R.glb` i publicznym Site wersji 2. Modele E19, 8K i rendery są w budowie, nie są jeszcze ukończonymi wynikami. Nowe Julia/Atlas z poprzedniego zgłoszenia nadal wymagają swoich eksportów; nie nazywać modelu w sukni poprawioną Julią w bluzie.
