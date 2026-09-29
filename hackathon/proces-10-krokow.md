# Proces: od katastrofy do dzialania (10 krokow)

## KONKRETNY SCENARIUSZ: powodz i przejezdnosc drog

Organizator prosi o konkretny problem, nie ogolne rozwiazanie.
Bierzemy jeden i prowadzimy go przez caly proces.

**Sytuacja (cwiczenie):** Po trzech dobach opadow rzeka Wislok wystepuje
z brzegow. Woda wchodzi do zabudowan w gminie pod Rzeszowem. Centrum
zarzadzania kryzysowego ma trzy pytania i nie ma na nie odpowiedzi:

1. **Ktore drogi sa jeszcze przejezdne?** - karetka i wozy strazy musza
   dojechac, a droga wojewodzka moze byc juz pod woda.
2. **Gdzie woda podnosi sie najszybciej?** - kogo ewakuowac najpierw.
3. **Czy ktos zostal odciety?** - ludzie na dachach, na wyspach gruntu.

Dzis odpowiedzi szuka sie telefonami do soltysow i wysylaniem patroli.
To trwa godziny i dane szybko sie dezaktualizuja.

**Dlaczego ten scenariusz:** przejezdnosc drog jest wymieniona wprost w
opisie zadania ("road accessibility checks"), a nasza analiza wody daje
liczbe - procent pokrycia terenu - a nie tylko opis slowny.

---

To jest wlasciwy produkt dla Jury. Nie narzedzie - **proces**.
Dron jest jednym elementem lancucha. Kazdy krok ma: kto, co, ile czasu,
i czym to jest zrobione w naszej platformie.

Czasy sa szacunkowe dla zdarzenia w promieniu 2 km od miejsca startu.

---

## DLA KOGO projektujemy - uzytkownik koncowy

Organizator pyta wprost: dla kogo? Odpowiadamy konkretnie, nie "dla
sluzb".

**Uzytkownik glowny (obsluguje system):**
Oficer dyzurny / operator na stanowisku kierowania **Panstwowej Strazy
Pozarnej** na poziomie powiatu. To on przyjmuje zgloszenie, dysponuje
sily i musi wiedziec, ktoredy one dojada.

**Odbiorca decyzji (dostaje raport):**
Komendant powiatowy PSP oraz **Powiatowe Centrum Zarzadzania
Kryzysowego** - to oni zamykaja droge, ogaszaja ewakuacje i odpowiadaja
za te decyzje pozniej.

**Dlaczego PSP, a nie policja:** w Polsce to straz pozarna prowadzi
dzialania w czasie powodzi w ramach KSRG. Policja zabezpiecza teren, ale
decyzja o kierunku dzialan ratowniczych jest po stronie strazy.

---

### Czego ten uzytkownik naprawde potrzebuje

| Potrzeba oficera dyzurnego | Co dostaje dzis | Co dostaje od nas |
|---|---|---|
| Ktoredy przejada wozy i karetki | Telefony do soltysow, patrole - godziny | Mapa z odcinkami drog pod woda, procent pokrycia, wiek danych |
| Kogo ewakuowac najpierw | Zgloszenia mieszkancow, niepelne | Miejsca gdzie woda przybiera najszybciej, ze wspolrzednymi |
| Czy ktos jest odciety | Nie wie, dopoki ktos nie zadzwoni | Wykrycia ludzi z pozycja GPS i poziomem pewnosci |
| Uzasadnienie decyzji po fakcie | Notatki sluzbowe pisane z pamieci | Raport Sytuacyjny z suma kontrolna, wygenerowany automatycznie |

---

### Jak to wchodzi w jego proces - bez zmiany procedur

To jest wazne: **nie zmieniamy sposobu pracy strazy.** System wchodzi
miedzy zgloszenie a dysponowanie sil, czyli w miejsce gdzie dzis jest
luka informacyjna.

```
DZIS:    zgloszenie -> [ luka: nie wiemy co sie dzieje ] -> dysponowanie sil
NASZ:    zgloszenie -> [ SkyOps: 20 minut, raport ] -> dysponowanie sil
```

Oficer dyzurny nie uczy sie nowego zawodu. Uczy sie jednego ekranu:
zaznacz obszar, poczekaj, przeczytaj raport. Reszta jego procedur zostaje
bez zmian.

---

## Tabela procesu

| # | Krok | Kto | Czas | Czym w SkyOps |
|---|---|---|---|---|
| 1 | **Zdarzenie** - zgloszenie o podtopieniach trafia do centrum zarzadzania kryzysowego | Dyspozytor | 0 min | - |
| 2 | **Decyzja o uzyciu dronow** - operator widzi stan floty: baterie, gotowosc, warunki | Operator | +2 min | Panel floty, telemetria na zywo |
| 3 | **Wyznaczenie obszaru** - operator rysuje obszar zainteresowania na mapie | Operator | +3 min | Rysowanie obszaru na mapie |
| 4 | **Automatyczny podzial zadania** - system dzieli obszar na pasy i przydziela je maszynom | **System** | +3 min | `areamission.py` - podzial serpentynowy |
| 5 | **Kontrola bezpieczenstwa** - misja w strefe zakazana jest odrzucana, zgloszenie do UTM | **System** | +3 min | Geofencing, symulowany check-in UTM |
| 6 | **Lot i zbieranie danych** - flota leci rownolegle, telemetria 5 Hz, wideo na zywo | Flota | +5 do +25 min | Symulator lotu / lacze MAVLink |
| 7 | **Analiza w czasie rzeczywistym** - AI czyta obraz: ludzie, ogien i dym, woda | **AI** | rownolegle | YOLOv8 lokalnie, segmentacja wody |
| 8 | **Alert do operatora** - kazde wykrycie z czasem i GPS; operator potwierdza lub odrzuca | **AI sugeruje, czlowiek decyduje** | +1 min od wykrycia | Lista alertow z pozycja |
| 9 | **Raport Sytuacyjny** - jedna strona: co znaleziono, gdzie, kiedy, trasa, suma kontrolna | **System** | +2 min po locie | `render_sitrep()` - PDF + SHA-256 |
| 10 | **Decyzja i dzialanie** - dowodzacy zamyka droge wojewodzka, kieruje karetki objazdem, wysyla lodz do odcietych | Dowodzacy | +30 min od zgloszenia | Raport jako podstawa decyzji i jej zapis |

---

## Trzy problemy, ktore wymienil organizator

Organizator nazwal problem dokladnie: **za malo informacji, zly dostep,
zla dystrybucja danych.** Mamy odpowiedz na kazdy z nich. To powinien
byc osobny slajd.

| Problem organizatora | Nasza odpowiedz | Krok |
|---|---|---|
| **Za malo informacji** | AI czyta kazda klatke obrazu. Czlowiek ogladajacy wideo po 3 godzinach przegapia rzeczy - system nie. Kazde wykrycie ma czas i wspolrzedne. | 7, 8 |
| **Zly dostep** | Link `/share` - kazdy kogo dopuscisz otwiera zywy obraz na telefonie. Bez instalacji, bez konta, bez logowania. Tylko podglad, nic nie moze zepsuc. | 2-8 |
| **Zla dystrybucja** | Raport Sytuacyjny PDF - jedna strona, dwujezyczny PL/EN, z suma kontrolna. Zaprojektowany do przekazywania dalej: mailem, wydrukiem, do innej sluzby. | 9 |

*Mowisz:* "Panstwo powiedzieli: za malo informacji, zly dostep, zla
dystrybucja. Mamy trzy konkretne odpowiedzi. Na informacje - AI czyta
kazda klatke. Na dostep - jeden link, kazdy otwiera na telefonie, bez
instalacji. Na dystrybucje - jedna strona PDF, ktora mozna przeslac
dalej i udowodnic, ze jej nie zmieniono."

**Uwaga: pokaz link /share na zywo.** Daj telefon komus z Jury i niech
sam otworzy. To jest odpowiedz na "zly dostep", ktorej nie da sie
pokazac slajdem.


---

## Dlaczego ten proces jest SZYBKI, DOKLADNY i BEZPIECZNY

Organizator poprosil dokladnie o te trzy rzeczy.

**SZYBKI** - waskim gardlem nie jest lot, tylko planowanie i przegladanie
materialu. Oba usuwamy:
- krok 4: nikt nie planuje tras recznie, system dzieli obszar sam
- krok 7: nikt nie oglada godzin nagran, AI czyta obraz w locie
- krok 9: raport powstaje sam, nie pisze go czlowiek w nocy

**DOKLADNY** - kazde wykrycie ma czas i wspolrzedne, a nie opis slowny.
Krok 8 jest celowo z czlowiekiem w petli: AI sugeruje, operator
potwierdza. System nigdy nie twierdzi, ze jest pewny.

**BEZPIECZNY** - krok 5 odrzuca misje w strefy zakazane, dron ktory w
nia wleci sam zawraca, a przy 25% baterii wraca bez polecenia. Krok 9
daje sume kontrolna - pozniej mozna udowodnic, ze raportu nie zmieniono.

---

## Gdzie dron jest tylko elementem systemu

To jest zdanie organizatora i warto je pokazac na schemacie:

```
ZGLOSZENIE  ->  OPERATOR  ->  [ DRON = CZUJNIK ]  ->  AI  ->  RAPORT  ->  DOWODZACY
   krok 1       kroki 2-5         krok 6           krok 7   krok 9      krok 10
                                    |
                            to jest maly fragment
```

*Mowisz:* "Dron zajmuje jeden krok z dziesieciu. Cala reszta to system,
ktory zamienia to co widzi w decyzje. Dlatego mowimy, ze dron jest
zrodlem danych, a nie produktem."

---

## Czego w tym procesie jeszcze nie mamy (mow uczciwie)

- krok 6: lot jest symulowany; zlacze do prawdziwego PX4 jest napisane,
  ale nie testowane w powietrzu
- krok 5: zgloszenie do UTM jest symulowane, nie ma prawdziwego API
- krok 10: nie mamy jeszcze zadnej sluzby, ktora przeszla ten proces
  naprawde - szukamy pierwszego wdrozenia pilotazowego
