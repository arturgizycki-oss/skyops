# Jak SkyOps spełnia wymagania — punkt po punkcie

Mapowanie oficjalnego briefu na to, co faktycznie mamy.
Kolumna DOWÓD to coś, co można pokazać na ekranie albo wydrukować.
Jeśli czegoś nie mamy — jest napisane wprost.

---

## 1. Przepływ informacji (sekcja 3 briefu)

Brief wymaga pokazania tej ścieżki:

> potrzeba operacyjna → użycie technologii dronowej → zbieranie danych →
> przetwarzanie i analiza → uporządkowanie informacji → dostarczenie
> użytkownikowi → decyzja lub działanie

Nasze 10 kroków pokrywa ją w całości:

| Etap z briefu | Nasz krok | Dowód |
|---|---|---|
| potrzeba operacyjna | 1 — wodowskaz IMGW przekracza stan alarmowy | panel "Wodowskazy IMGW", dane publiczne na żywo |
| użycie technologii dronowej | 2–3 — operator ocenia flotę, zaznacza obszar | mapa floty, rysowanie obszaru |
| zbieranie danych | 4–6 — system dzieli obszar, flota leci | podział serpentynowy, telemetria 5 Hz |
| przetwarzanie i analiza | 7 — AI czyta obraz | YOLOv8 lokalnie, procent zalania |
| uporządkowanie informacji | 8 — alert z czasem, GPS i pewnością | lista alertów z poziomem pewności |
| dostarczenie użytkownikowi | 9 — Raport Sytuacyjny PDF + link /share | wydrukowany raport, telefon z podglądem |
| decyzja lub działanie | 10 — zamknięcie drogi, skierowanie sił | raport jako podstawa i zapis decyzji |

---

## 2. Siedem elementów spójnej koncepcji (sekcja 4 briefu)

Brief: *"Nie musicie budować w pełni działającego systemu. Najważniejsza
jest spójna koncepcja, która pokazuje:"*

| Wymaganie | Nasza odpowiedź | Dowód |
|---|---|---|
| **jaki problem jest rozwiązywany** | Powódź: które drogi są jeszcze przejezdne, gdzie woda przybiera, czy ktoś jest odcięty | slajd 4 |
| **kto używa rozwiązania** | Oficer dyżurny stanowiska kierowania PSP, poziom powiatu. Odbiorca decyzji: komendant powiatowy + PCZK | slajd 3 |
| **jak używana jest technologia dronowa** | Dron jest źródłem danych — krok 6 z 10. AI czyta jego obraz na żywo | slajd 5, demo |
| **jakie informacje są zbierane i przetwarzane** | Wideo → wykrycia (ludzie, ogień, woda) z czasem, współrzędnymi i poziomem pewności | panel alertów |
| **jak informacja przepływa przez system** | 10 kroków, ok. 30 minut od zgłoszenia do decyzji | slajd 5 |
| **jak rozwiązanie wspiera decyzję lub działanie** | Raport Sytuacyjny: jedna strona, ustalenia potwierdzone i niepotwierdzone, suma kontrolna | wydruk dla Jury |
| **jakie są ograniczenia i warunki użycia** | Wypisane wprost: lot symulowany, UTM symulowany, brak klienta, rój to koncepcja | slajd 9 |

**Ostatni wiersz jest tym, który większość zespołów pominie.**
Brief wymaga ograniczeń. My mamy z nich osobny slajd.

---

## 3. Czego wymaga rozwiązanie (sekcja 5 briefu)

| Wymaganie | Spełnione? | Jak |
|---|---|---|
| używa danych lub możliwości technologii dronowej | TAK | całość opiera się na obrazie z drona |
| dotyczy realnego problemu operacyjnego | TAK | przejezdność dróg — wymieniona w samym briefie |
| zaprojektowane z myślą o konkretnym użytkowniku | TAK | oficer dyżurny PSP, z opisem jego potrzeb |
| wspiera podejmowanie decyzji lub działanie | TAK | Raport Sytuacyjny → zamknięcie drogi |
| poprawia szybkość, jakość lub bezpieczeństwo procesu | TAK | ~30 min zamiast godzin telefonów; strefy zakazu; auto-powrót |
| uwzględnia ograniczenia organizacyjne, prawne i etyczne | TAK | slajd 8 — człowiek w pętli, dane lokalnie, rozliczalność |
| mieści się w bezpiecznym, defensywnym rozumieniu dual use | TAK | brak efektorów — decyzja od początku projektu |

---

## 4. Czego brief zakazuje (sekcja 10) — jesteśmy czyści

| Zakazane | My |
|---|---|
| uzbrajanie dronów | nie budujemy efektorów |
| działania ofensywne | nie |
| zagłuszanie łączności/nawigacji | nie |
| przejmowanie cudzych dronów | nie |
| omijanie zabezpieczeń w systemach lotniczych | odwrotnie — respektujemy strefy zakazu lotów |
| działania szkodzące infrastrukturze | nie |
| nieuzasadniona ingerencja w prywatność | obraz nie opuszcza maszyny; AI lokalnie |

---

## 5. Kryteria oceny — gdzie zdobywamy punkty

| Kryterium | 20% | Skąd punkty | Ryzyko |
|---|---|---|---|
| Użyteczność operacyjna | | Raport Sytuacyjny; nie zmieniamy procedur służby | — |
| Rola technologii dronowych | | dron jest głównym elementem, nie dodatkiem; AI na obrazie z drona | — |
| Innowacyjność | | weryfikacja niepewności: dwa źródła, człowiek rozstrzyga; raport dzieli ustalenia | **nasze najsłabsze** — mamy gotowy produkt, a Jury może nagradzać świeży pomysł |
| **Realność i wykonalność** | | **platforma działa i jest online — otwórzcie na telefonie** | **nasza najmocniejsza karta** |
| Prezentacja | | polski, 10 slajdów, demo na żywo, wydrukowane raporty | zależy wyłącznie od ćwiczeń |

Minimum 50% punktów, żeby dostać jakąkolwiek nagrodę.

---

## 6. Gdzie jesteśmy słabi — powiedz to sam

**Innowacyjność.** Przychodzimy z gotową platformą. Jury może uznać, że
to mniej innowacyjne niż pomysł wymyślony tej nocy.

Odpowiedź: *"Platforma istniała. Nowa jest warstwa weryfikacji
niepewności — wodowskaz zna poziom, dron zna zasięg, człowiek
rozstrzyga, a raport zapisuje, co potwierdził człowiek, a co tylko AI.
Tego nie robi żadne znane nam narzędzie, łącznie z TAK."*

**Prezentacja.** Nigdy tego nie robiłeś i masz 5 minut po polsku.
Odpowiedź: ćwicz z zegarkiem, dwa razy, na głos.

---

## 7. Jedno zdanie, gdyby zapytali "dlaczego wy"

> "Bo nasze rozwiązanie działa dzisiaj, mówi wprost czego nie potrafi,
> i nie każe strażakowi zmieniać sposobu pracy — dokłada tylko brakującą
> informację między zgłoszeniem a decyzją."
