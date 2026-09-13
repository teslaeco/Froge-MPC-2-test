# Oracle v35 — aktualizacja istniejącego workera

**Paczka zweryfikowana; instalacji na Oracle nie wykonano w tej sesji. Nie używać wcześniejszej paczki v34.**

Pobierz [froge-v35.zip](../../public/downloads/froge-v35.zip). Prześlij ZIP przez Menu → Upload w swoim Oracle Cloud Shell do katalogu domowego. Skorzystaj z dotychczasowego Cloud Shell z kluczem `$HOME/ssh-key-2026-09-06.key`; klucza nie przesyłaj do czatu.

Uruchom kolejno:

```bash
python3 -m zipfile -e "$HOME/froge-v35.zip" "$HOME/froge-v35"
python3 "$HOME/froge-v35/froge-v35.py"
```

Instalator łączy się z istniejącym workerem `opc@141.148.242.30`, katalog `$HOME/froge-connector` na Oracle. Weryfikuje SHA256 pięciu istniejących dużych zasobów przed zmianą kodu; brakujące lub zmienione zasoby zatrzymują instalację. Zachowuje konfigurację, połączenie i zapisane zlecenia. Gdy trwa generowanie, zatrzymuje aktualizację przed zmianą kodu. Nie uruchamia domyślnie płatnego generowania postaci.

Wykonuje test rzeczywistego Codexa, MCP, Blendera oraz eksportów z kontrolnymi odpowiedziami modelu. Wymaga właściwej wersji i capability działającego workera. Niezgodne health lub nieudane sprawdzenie uruchamia przewidziany rollback. Czekaj na końcowy wynik tej samej instalacji.

Potwierdzenia wymagane po udanej instalacji:

- `CODEX_MCP_BLENDER_BUILD_OK` i końcowe `FROGE_V35_OK`.
- Health po odświeżeniu połączenia Studio: `connectorVersion: 35`, `referenceAcceptanceRevision: 1`, `workerRelease: v35-reference-acceptance`.

Sam ZIP, scalenie PR albo zielone CI nie potwierdzają instalacji. Nie przekazano stąd sesji SSH. Paczka nie zmienia prywatnego kodu strony Studio, nie przebudowuje starych modeli i nie zawiera nowego artystycznego modelu E19 ani jego atlasów 8K.

## Co poprawia wydanie

V35 zachowuje poprawki atlasów przypisanych do głowy, kompilacji edycji przed zużyciem próby i rozróżnienia oka obecnego od celowo pustego oczodołu. Naprawia też niespójność v34: tamten ZIP zawierał kod zgłaszający wersję 33. V35 zgłasza rzeczywistą wersję i capability, sprawdza je podczas instalacji, a komunikat ukończenia zadania stosuje hostową ocenę bieżącego pliku. Surowa akceptacja agenta pozostaje informacją historyczną, nie wystarcza do przyjęcia niepełnego wyniku.

Komplet sześciu widoków i pomiarów referencyjnych nie powstaje jeszcze automatycznie w każdym zleceniu. Brak dowodów pozostawia model jako draft. To kontrola rzetelności statusu, nie gwarancja poprawnej anatomii, podobieństwa ani gotowości do produkcji fizycznej.

## Integralność

| Pozycja | Wartość |
|---|---|
| Testowany commit | `4c6c7fb000a98627264d7c6bcca1f441eb760fe2` |
| CI | [34733597773](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34733597773) |
| Testy | 150 na Pythonie 3.9 i 3.12; rzeczywiste Blender/MCP/GLB/FBX i atlas/szachownice w zadaniu 3.9 |
| ZIP | 394 642 bajty |
| SHA256 ZIP | `913918c69dd44a0579b71819522204d1c31f7d5eb4b38c952659347dd9b11c2a` |
| SHA256 payloadu | `da7bc39d22b829f757c548beea44db3fdffa57e08188df356b3d47a70ced0d23` |
| Merge PR #11 | `23a7b5859f6093073bedeb037b2ba0e75b142c7b` |

Dostarczony ZIP odtworzono deterministycznie z dokładnych źródeł sprawdzonego commitu. Jego payload i rozmiar odpowiadają udanemu CI. Sprawdzono CRC, hashe osadzonych źródeł, kompilację, wersję 35 i wymaganie capability. Nie deklarujemy binarnej identyczności archiwum z oryginalnym wewnętrznym ZIP-em CI, którego niezależny hash nie był dostępny. Nie tworzono zastępczych atlasów; CI zweryfikowało rzeczywiste zasoby repozytorium, a instalator sprawdzi je ponownie na Oracle.

[Raport integralności](e19/froge-v35-verification.json) · [Wybrane dowody CI](e19/froge-v35-ci-evidence.json).
