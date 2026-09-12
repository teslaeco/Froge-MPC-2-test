# JULIA — 8 Cosmic Keys: zwiastun koncepcyjny

Gotowy plik: `JULIA-teaser-15s-EN-PL.mp4`.

To **15-sekundowy montaż dwóch filmów i plakatu dostarczonych przez użytkownika, uzupełniony rzeczywistym renderem nowego modelu królowej Neptuna**. Jest dodatkiem do pracy nad generatorem, a nie dowodem animowania głównego modelu E17.

## Co wykonano

- Pionowy obraz 720 × 1280, 30 kl./s, H.264 i AAC; plik MP4 przygotowany do odtwarzania w przeglądarce (`faststart`).
- Montaż: meteor i bohaterki → render modelu królowej Neptuna z wachlarzem (3,8–5,4 s) → proca → kosmiczny sześcian → plansza tytułowa na tle plakatu.
- Angielska narracja syntetyczna lokalnym głosem Flite RMS. Nie jest to profesjonalny dubbing ani klon głosu człowieka.
- Własna syntetyczna oprawa dźwiękowa: niski podkład, narastanie napięcia i uderzenia zsynchronizowane z cięciami. Oryginalnych ścieżek audio klipów nie użyto.
- Polskie napisy wypalone w obrazie i osobny plik `JULIA-teaser-PL.srt`.
- Pełne kadry źródłowe pozostawiono widoczne, w tym znaki wodne Sora i drugiego klipu. Rozmyte brzegi dopasowują proporcje do pionowego filmu.

## Granice wykonania

- **Nie powstała nowa animacja wsiadania dziewczyny do kapsuły.** Załączone klipy nie zawierają tego ujęcia, a w tej sesji nie ma narzędzia generacji wideo.
- Ujęcie procy pochodzi z dostarczonego filmu. Widoczne podpory mają formę piramid/brył; ich kilometrowa wysokość nie jest potwierdzona. Nie jest to symulacja fizyczna startu w kosmos.
- Królowa Neptuna jest pokazana jako statyczny render rzeczywistego modelu. Nie animowano jej siatki 3D; twarz pozostaje przybliżeniem.
- Główny model dziewczyny E17 nie występuje w tym montażu. Film nie stanowi demonstracji jakości jego geometrii lub tekstur.
- Oba klipy źródłowe mają szerokość 480 px. Powiększenie do 720 px służy formatowi publikacji i nie odtwarza brakujących szczegółów.

## Narracja i tłumaczenie

| Czas początku | Narracja EN | Napisy PL |
|---|---|---|
| 0,3 s | Eight keys. | Osiem kluczy. |
| 2,7 s | One universe. | Jeden wszechświat. |
| 7,8 s | Launch beyond the edge of our world. | Wyrusz poza granice naszego świata. |
| 12,0 s | Julia. | Julia. |

## Odtworzenie montażu

Wymagania: Python z NumPy, FFmpeg z filtrami Flite/libass i fonty DejaVu. Uruchom `python trailer-e17/build_trailer.py --queen-render queen-e17/upper.png` z katalogu pracy zawierającego oryginalne pliki w `upload/`. Bez argumentu model królowej zastąpi plakat. Proces używa dwóch wątków FFmpeg. `verification.json` zawiera długość, parametry obrazu, kolejność ujęć i sumy SHA-256 źródeł oraz wyniku.

Walidacja: sprawdzenie strumieni audio/wideo i długości przez FFprobe, dekodowanie całych 15 sekund bez błędów oraz oględziny reprezentatywnych kadrów i czytelności napisów. Subiektywna ocena narracji i dramaturgii pozostaje do odsłuchu przez użytkownika.
