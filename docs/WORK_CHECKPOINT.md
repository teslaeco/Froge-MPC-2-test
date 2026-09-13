## Oracle — odzyskanie plików i gotowa paczka, 2026-09-13

Odzyskano froge-v19.zip i FORGE-modelka-4K.zip z MCP2 oraz froge-v33.zip; v34 pobrano z public/downloads w repo. Hash ZIP i payloadu v34 zgodny z wcześniejszym raportem. GLB i BLEND wcześniejszej modelki zgodne z oryginalnym manifestem. Nie pomylono ich z bieżącymi zleceniami Julia/Queen.

Nowy tools/oracle-recovery/forge-oracle.py uruchamia niezmienione v34 tylko na starszej bezczynnej instalacji, zachowuje v34/nowsze, sprawdza health i eksportuje dokładne dwa zlecenia z Oracle do Cloud Shell. 7 testów lokalnych przeszło; nie uruchomiono nowego skryptu na Oracle. To etap instalacji/odzyskania plików, NIE nowa generacja ani naprawa geometrii. Prywatna/publiczna strona nie została zmieniona w tym etapie. Dalsze instrukcje: docs/reviews/oracle-recovery-20260913.md. Paczka użytkownika: FORGE-Oracle-aktualizacja.zip. Zgoda na publikację i Oracle jest udzielona; brak aktywnego SSH w sesji, instalacja czeka na polecenie w Cloud Shell.

---

## Stan końcowy wznowienia — 2026-09-13

Aktualny raport: [DELIVERY-2026-09-13.md](reviews/resume-2026-09-13/DELIVERY-2026-09-13.md).

- Kod v34 zweryfikowany w CI na commit `ad8844cd8d350c0af6939e1a0cda847dd87e3f9b`: 146 testów na każdej z wersji Python 3.9 i 3.12, rzeczywisty Blender/MCP/GLB/FBX, atlas i szachownice. [Run 34730631366](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34730631366) zakończony sukcesem.
- Wykonano rzeczywistą lokalną korektę E18R (nasada włosów i sheen czarnej sukni), ponowny import GLB i kontrolowane rendery przed/po. 6 354 061 trójkątów. Nie przebudowano twarzy, oczu, szyi ani sylwetki.
- Publiczny Site wersja 2 opublikowany: https://forge-studio-public.terraformingplanet.chatgpt.site . Commit źródeł `8d716ebcccc107b5c542ffac03d2c417d62e3f35`; deployment `appgdep_6aa5fd40babc8191a8ad6efe181a99a3` potwierdzony jako succeeded. Źródłowy E18 GLB oraz nowy E18R GLB są zachowane w Git i Site.
- **Nie zainstalowano v34 na Oracle** — brak aktywnej uwierzytelnionej sesji SSH. Przekazano paczkę i polecenie Cloud Shell; nie twierdzić, że serwer został zaktualizowany bez odczytu jego FROGE_V34_OK i health.
- **Nowe Julia/Atlas nie zostały przebudowane** — dostępne są zrzuty, referencja i rekord zlecenia; eksport aplikacji wymaga tożsamości właściciela (401). Do kontynuacji potrzebne są GLB/BLEND tych zleceń. Julia w bluzie nie jest E18 w sukni.
- Prywatny Site nadal wersja 47, klon HTTP500; nie zastąpiono go publicznym pokazem. Gate hosta odrzuca niekompletne dowody, ale cały komplet widoków/pomiarów nie powstaje jeszcze automatycznie.
- Nie uruchomiono L4, treningu wag ani płatnej nowej generacji. Wcześniejszy master/4K usunięty przez porządkowanie środowiska nie został odzyskany; wcześniejsze wzmianki o osobno dostępnych ciężkich masterach są historyczne.
- PR #11 pozostaje draft. Zachować wcześniejsze porównania Meshy jako ocenę ze screenów, nie nowy kontrolowany benchmark. Zachować notatki naukowe i ChessArena jako pamięć/testy projektu.


---

## Historyczne checkpointy

# E18 delivery checkpoint — 2026-09-12

Main candidate E18: 6,315,947 FBX triangles; 369/369 UV mesh objects; source SHA 28673fc400228a756d80128b89885ff7f0a017d857f517058cfb1bc689b7ffb6. Six actual reimport views and HQ 2048x2560 produced. Web GLB 23,161,896 bytes, 6,315,623 triangles; texture downsizing and export triangulation documented. Preserve E15/E16/E17 originals. Local model edits are separate from the generator runtime patch.

16 CPU regression tests passed. Blender 4.3.0 tests measured tagged 64/512-cell positive and negative fixtures. Actual runtime invokes evidence and board review; new module included in updater file allow-list. No new weights, L4 job, Oracle installation or full host acceptance integration. Visual likeness remains unfinished, including lower nose, eyelids and regular hair grouping.

Public showcase published: https://forge-studio-public.terraformingplanet.chatgpt.site . Canonical Site source aed971eae22d1c98f9ce061fd1d9a0522c875fe4. Contains public preview, optional 3D rotation, local brief/quote downloads, Queen model and 15s EN/PL trailer. No live supplier dispatch/payment. The existing private operator Studio was not modified.

PR #11 codex/e17-reference-fidelity-public-studio targets codex/v27-mcp-startup-audit. Keep as draft pending visual improvements and production host integration. Reports, comparisons and technical error memory in docs/reviews/e17; private ChessArena evidence in docs/training/e17.

A 646 MB local master archive exists. An attempted extra Google Drive backup was rejected by automatic approval review because the user did not specify that destination/payload; do not retry without explicit authorization. Public web copies and Git-backed source/comparisons are saved. Complete delivery coverage: docs/reviews/e17/TASK-COVERAGE.md.

## Prior checkpoint

# E17 active checkpoint

Main task: improve actual E16 hair/teeth/anatomy from supplied reference; model build pending from dedicated agent. Secondary Queen/fan rebuilt; video 15s produced and validated. Generator runtime changes pending integration, source literature and curated error catalog complete. Sources in docs/reviews/e17 and docs/training/e17; no full L4 training or Astra weights claimed. Private ChessArena PR115 provides QA training source but weights/results not recovered in reviewed tree. User's requested public client site is separate from operator studio; static source prepared under public-studio, Site ID appgprj_6aa5c12d4f4c81919545504d438b3ff3. Not deployed yet. Existing Sites clone failed with server HTTP500 three bounded attempts; private studio unchanged. No Oracle worker deployment. Artifact saving via Library unavailable this turn. Models/renders remain local until final handoff.


## Wznowienie 2026-09-13

Nowe zgłoszenia Julii w bluzie i figurki Atlas oraz stan wznowienia opisano w [checkpoint](reviews/resume-2026-09-13/RESUME-CHECKPOINT.md) i [analizie porównawczej](reviews/resume-2026-09-13/REFERENCE-CASES-2026-09-13.md). Ten etap nie potwierdza jeszcze instalacji na Oracle ani poprawienia nowych eksportów.
