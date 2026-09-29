# Odporność systemu — co się dzieje, gdy coś przestaje działać

Brief wymaga wprost (sekcja 4): *"jakie są ograniczenia i warunki
użycia"*. Większość zespołów to pominie. My mamy z tego drabinę
degradacji — co system nadal potrafi, gdy kolejne rzeczy zawodzą.

**Ważne rozróżnienie prawne.** Sekcja 10 briefu zakazuje *zagłuszania
łączności i nawigacji* oraz *omijania zabezpieczeń*. My nie zagłuszamy
niczego. Projektujemy działanie **mimo** zakłóceń — to jest odporność,
czyli dokładnie to, czego brief oczekuje (sekcja 11: rozwiązania
"defensywne, ratownicze, monitorujące").

Legenda: **[DZIAŁA]** — zaimplementowane i przetestowane.
**[KONCEPCJA]** — zaprojektowane, nieзbudowane.

---

## Drabina degradacji

| Poziom | Co zawiodło | Co system nadal robi | Status |
|---|---|---|---|
| **0** | nic | pełna funkcjonalność | **[DZIAŁA]** |
| **1** | brak internetu | mapy z pamięci lokalnej, AI lokalnie, dane dróg lokalnie — operator pracuje bez żadnej sieci zewnętrznej | **[DZIAŁA]** |
| **2** | brak prądu sieciowego | całość to jeden laptop — bateria, potem agregat gminy. Nie potrzebujemy serwerowni | **[DZIAŁA]** |
| **3** | zerwana łączność z dronem | dron sam wraca do bazy (failsafe PX4). Operator pracuje na ostatnim obrazie, wyraźnie oznaczonym jako nieaktualny | **[CZĘŚCIOWO]** — wiek obserwacji pokazujemy; failsafe jest po stronie autopilota |
| **4** | brak GNSS (zakłócenia) | **tu tracimy najwięcej** — patrz niżej | **[KONCEPCJA]** |
| **5** | brak wszystkiego | procedura papierowa: wydrukowany ostatni Raport Sytuacyjny zachowuje ważność, bo ma czas, współrzędne i sumę kontrolną | **[DZIAŁA]** |

---

## Poziom 4 — brak GNSS. Powiedzmy wprost, co tracimy

To jest realne zagrożenie w Polsce wschodniej, nie teoria. Zakłócenia
sygnału GNSS przy wschodniej granicy są udokumentowane.

**Co przestaje działać u nas:**

Nasza wartość to zdanie *"zalanie drogi, 92% pewności, **pozycja
50.11440, 22.02710**, godzina 14:32"*. Bez GNSS zostaje *"gdzieś tam
jest zalanie"* — a to jest bezużyteczne dla dysponenta sił.

**Nie udawajmy, że mamy na to gotowe rozwiązanie.** Mamy trzy kierunki:

**A. Punkty odniesienia w terenie [KONCEPCJA]**
Operator wskazuje na obrazie obiekt o znanych współrzędnych — most,
skrzyżowanie, wieża. System liczy pozycję wykrycia względem niego.
Dokładność gorsza, ale wystarczająca do decyzji "ta droga czy tamta".
Dane BDOT10k i tak mamy offline.

**B. Triangulacja z anten naziemnych [KONCEPCJA — pomysł Artura]**
Trzy lub więcej anten o znanej pozycji mierzy kierunek albo różnicę
czasu przyjścia sygnału z drona. Technika znana (TDOA/AOA).
*Uczciwie:* wymaga rozstawienia i zmierzenia anten wcześniej, daje
dokładność rzędu dziesiątek metrów, i nie zbudujemy tego w 24 godziny.
Do wpisania w roadmapę, nie do obiecania Jury jako gotowe.

**C. Degradacja świadoma [KONCEPCJA, najprostsza]**
System wie, że nie ma GNSS, i **sam obniża status wszystkich ustaleń**
do "pozycja niepewna". Raport to odnotowuje. Dowodzący widzi, że
dostał obraz bez wiarygodnych współrzędnych, i nie wysyła sił w ciemno.

To ostatnie jest spójne z całą naszą filozofią: **system nigdy nie
udaje, że wie więcej, niż wie.** Utrata GNSS nie może po cichu
zamienić się w złe współrzędne w raporcie.

---

## Co z tego jest naszą przewagą

Poziomy 1, 2 i 5 **naprawdę działają** i są rzadkie:

- **Brak internetu nie zatrzymuje nas.** AI działa lokalnie, kafle mapy
  są w pamięci, dane dróg też. Można wyciągnąć kabel sieciowy.
- **Nie potrzebujemy serwerowni ani chmury.** Jeden laptop i agregat.
- **Papierowy raport zachowuje ważność.** Ma czas, współrzędne i sumę
  kontrolną — działa, gdy nie działa nic innego.

Rozwiązanie chmurowe traci wszystko na poziomie 1. My tracimy dopiero
na poziomie 4, i mówimy o tym otwarcie.

---

## Zdanie dla Jury

> "Zapytaliście o ograniczenia. Nasz system pracuje bez internetu i bez
> serwerowni — AI liczy się na tym laptopie. Tracimy najwięcej przy
> zakłóceniach GNSS, bo nasza wartość to współrzędne. Wtedy system sam
> obniża status ustaleń do 'pozycja niepewna' zamiast podawać złe
> liczby. Triangulacja z anten naziemnych to kierunek, który
> rozważamy — ale nie mamy jej zbudowanej i nie będziemy udawać, że
> mamy."
