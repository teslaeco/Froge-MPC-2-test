# V31: uwagi Copilota i kontrola instalacji

V30 (publikacja46) naprawia formularz, źródło modelu, finisz MCP i materiały.
Po jego publikacji dotarła recenzja Copilota do wcześniejszego kodu PR10.
V31 dodatkowo rozwiązuje wskazane, potwierdzone problemy:

- Instalacja CLI/hosta w osobnym katalogu. Pełny rollback kodu, plików
  wykonywalnych, potwierdzeń i uprawnień. Pobieranie nie blokuje kolejki.
- Świeża instalacja sprawdza rzeczywistą budowę w Blenderze, nie tylko transport.
- Gotowość wymaga zgodności hashy CLI i osobnego Code Mode hosta. Sam napis
  --version nie jest dowodem integralności. Brak plików blokuje płatne zlecenie.
- OpenAI nie przechodzi po cichu do generatora bez Codexa. Zapisany plan nadal
  można wykonać bez AI; tekstowa ścieżka lokalnego Ollama pozostaje dostępna.
- Ponawianie scen używa zgodnego limitu256kB, przy osobnym limicie kodu60kB.
- Receipt płatnej próby publikuje kompletny JSON atomowo; równoległe wywołania
  widzą ten sam identyfikator, bez tworzenia drugiego zamówienia.

Mała paczka v31 zawiera wszystkie aktualne pliki programu i pomija pięć
niezmienionych, dużych zasobów. Kopiuje je z bieżącej instalacji do katalogu
przygotowawczego wyłącznie po zgodności z przypiętym manifestem SHA256.
Niekompletne zasoby zatrzymują aktualizację przed zmianą działającego kodu.
Poprzednie ZIP-y zachowują identyczne bajty. Obrazy w dawnym raporciev26
przeniesiono z base64 do osobnych plików bez zmiany ich bajtów, by zachować
rozmiar publikacji w limicie bez usuwania modeli i wcześniejszych instalatorów.

```bash
python3 -m zipfile -e "$HOME/froge-v31.zip" "$HOME/froge-v31"
python3 "$HOME/froge-v31/froge-v31.py"
```

Po FROGE_V31_OK odśwież Studio i sprawdź Oracle. Jeśli wymagane zasoby są
uszkodzone, komunikat wskaże pełne froge-v30.zip do odtworzenia zasobów.
Instalacja sama nie uruchamia płatnego AI. Nie używano tutaj dostępu do
prywatnego Oracle, klucza API ani autoryzowanej przeglądarki; nowa płatna
generacja i podobieństwo do referencji pozostają do sprawdzenia na Oracle.

Audyt Copilot: recenzja PRR_kwDOUPle3M8AAAABNQ9DPQ z2026-09-12T04:18:26Z.
Wyniki testów i finalnej publikacji są w docs/reviews/v31/verification.json.
Nie utożsamiaj testów z zaprogramowanymi odpowiedziami z jakością Astry.
