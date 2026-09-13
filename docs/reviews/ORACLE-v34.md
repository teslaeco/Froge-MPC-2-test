# Oracle v34 — wydanie wycofane

**Nie instalować wcześniejszego `froge-v34.zip`. Użyj [Oracle v35](ORACLE-v35.md).**

Audyt kodu i zawartości paczki wykazał, że archiwum v34 zawierało serwer oraz instalator deklarujące wersję 33. Stare CI potwierdzało funkcje i zgodność payloadu ze źródłem, ale nie wykrywało błędnej identyfikacji wydania. Wcześniejsza instrukcja, która przedstawiała `FROGE_V34_OK` i pola health v34 jako dostępne potwierdzenie, była nieprawidłowa.

Host gate był już używany w API jakości. Osobny błąd dotyczył komunikatu zakończenia zadania, który opierał się na deklaracji agenta i mógł przeczyć statusowi draft. V35 naprawia oba problemy i dodaje ich regresje.

Nie potwierdzono instalacji starego v34 na Oracle. Jeśli zostało uruchomione przez właściciela, potrzebny jest odczyt rzeczywistego health; nie wolno wnioskować wersji z nazwy pobranego ZIP-u. Dokumenty wcześniejszego wznowienia zachowują wartość historyczną, a ich twierdzenia o poprawnym wydaniu v34 zastępuje niniejsze sprostowanie.
