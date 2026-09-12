# V30: źródło podglądu, zakończenie zleceń i korekty Blendera

Potwierdzone błędy: MCP odrzucało odczyt po finish_model; CLI mogło dalej
pracować i zgłaszać błąd mimo finału; marker starego wykonania nie był związany
z nowym uruchomieniem. Edycja radii= nie pasowała do sygnatury ellipsoid.
make_material blokowało korekty legalnej postaci z 16 materiałami. SyntaxError
mógł zakończyć MCP. Formularz zachowywał stary running, a stary model nie miał
wyraźnego oznaczenia źródła. Stary lazy chunk po publikacji zwracał 404.

Zmiany: odczyt/idempotentny finał, zakończenie po integralnym wyniku, execution_id
+ rewizja + SHA256, osiem nowych materiałów korekty, zgodne helpery i końcowy
wyjątek. Szkice pozostają w prywatnej historii; tylko zweryfikowana oceniona
rewizja automatycznie wchodzi do podglądu. Zapis do katalogu jest ręczny po
ocenie wyglądu. Przycisk nowego zadania resetuje stan wykonania i instrukcje.
Anulowanie nie może zostać cofnięte przez spóźnioną odpowiedź. Widoczny jest
numer i źródło modelu; stare przykłady nie są wynikiem nowego zadania.

Astra pozostaje jedynym modelem AI. Codex jest wykonawcą wywołań MCP;
Blender buduje rzeczywistą geometrię, materiały, rendery i eksporty.
Budżet 32 zapytań / 96000 tokenów / 5 budów / 1800 sekund pozostaje bez zmian.
To górny limit, nie gwarancja czasu ani jakości. Niewidoczne części referencji
są rekonstruowane. Sam plik ani verdict Astry nie gwarantują podobieństwa.

## Instalacja na istniejącym Oracle

Pobierz froge-v30.zip ze strony, prześlij do swojego Cloud Shell i wykonaj:

```bash
python3 -m zipfile -e "$HOME/froge-v30.zip" "$HOME/froge-v30"
python3 "$HOME/froge-v30/froge-v30.py"
```

Wymagane FROGE_V30_OK. Instalator zachowuje modele, klucz i połączenie.
Sprawdza rzeczywisty Codex/MCP oraz Blender/GLB/FBX z odpowiedziami testowymi,
bez płatnego modelu. Aktywne zlecenie blokuje aktualizację do zakończenia lub
anulowania, by nie przerwać generowania w połowie.

Po odświeżeniu sprawdź Oracle v30; nowy opis i zdjęcie wysyłane są razem
z automatycznie przygotowanym, edytowalnym poleceniem jednym przyciskiem.

## Polecenie do Codex i kryteria odbioru

Odtwórz dwa kolejne zadania z różnymi opisami i referencjami. Astra ma
wywołać rzeczywistą budowę, obejrzeć bieżące rendery i poprawić konkretne
wady. Sprawdź, że finalny model, rewizja, ocena i numer zadania są zgodne.
Zakończ natychmiast po finish_model. Błąd kolejnej korekty może zachować
bieżący szkic, ale nie może podstawić innego zlecenia ani starego przykładu.
Nie publikuj szkicu jako zaakceptowanego modelu. Nowe zadanie ma resetować
blokadę i nie może zostać nadpisane przez poll poprzedniego zadania.
Zapisz raport realnego czasu, geometrii, tekstur, renderów i wad podobieństwa.
Nie dodawaj zewnętrznego generatora. Zachowaj konfigurację i wcześniejsze pliki.

## Stan weryfikacji

UI/API: 83 testy oraz typecheck. Python: 39 regresji, w tym lifecycle i rollback.
Native Blender: fixture 16 materiałów + 8 materiałów korekty oraz zapisany
rzeczywisty model, GLB i FBX po ponownym imporcie. Testy UI i pełne CI są
opisywane w verification.json. Model Responses w CI są zaprogramowane;
nie są rzeczywistą płatną generacją ani oceną podobieństwa nowej postaci.
Tutaj nie ma dostępu SSH/API/autoryzowanej przeglądarki do prywatnego Oracle.

Źródło instrukcji przeglądu Copilot: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review/use-code-review
Złożono żądanie przeglądu PR10 do copilot-pull-request-reviewer[bot].
Nie potwierdzono jeszcze ukończonej recenzji ani jej wyniku.

Frontend ma osobne źródło Sites; łatka docs/reviews/v30/site.patch jest względem
Site source16ff84334e26466f44240836e1d9a18db432eddd, nie względem starszego
frontendu GitHub. Nie stosuj jej ślepo do innej bazy. Bieżące źródło Sites
jest podstawą publikacji; PR zawiera wykonywalny worker Oracle i łatkę UI do audytu.
