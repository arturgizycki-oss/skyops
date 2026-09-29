# PREZENTACJA - 10 slajdow, PDF, po polsku

Wszystko czego zazadal organizator, w jednym miejscu.
Limit z regulaminu: **max 10 slajdow, PDF, po polsku.** Tu jest dokladnie 10.
Czas: **5 minut + 2 minuty pytan.** Cwicz z zegarkiem.

Na slajdzie max 30 slow. Reszta to co mowisz.

---

## SLAJD 1 - Tytul (WYMAGANY PRZEZ REGULAMIN)

# SkyOps
### Od problemu do informacji w dzialaniu

**Nazwa zespolu:** SkyOps
**Sklad zespolu:** [DO USTALENIA - patrz uwaga na koncu]

*Mowisz:* "Jestesmy zespol SkyOps. To nie jest makieta - platforma
dziala, mozecie ja otworzyc na telefonie w trakcie mojej prezentacji."

(QR do getskyops.com - zostaw na ekranie do konca)

---

## SLAJD 2 - Problem, ich wlasnymi slowami

### Za malo informacji. Zly dostep. Zla dystrybucja.

*Mowisz:* "Panstwo nazwali problem dzis rano. Dodam tylko, jak on
wyglada o trzeciej w nocy podczas powodzi: oficer dyzurny dzwoni do
soltysow, zeby dowiedziec sie ktora droga jest przejezdna. Zanim
dostanie odpowiedz, jest juz nieaktualna."

---

## SLAJD 3 - Dla kogo (WYMAGANE)

**Uzytkownik:** oficer dyzurny na stanowisku kierowania PSP, poziom powiatu
**Odbiorca decyzji:** komendant powiatowy PSP + Powiatowe Centrum Zarzadzania Kryzysowego

| Jego potrzeba | Dzis | U nas |
|---|---|---|
| Ktore drogi przejezdne | telefony, godziny | mapa, 20 minut |
| Kogo ewakuowac pierwszego | niepelne zgloszenia | miejsca ze wspolrzednymi |
| Czy ktos odciety | nie wie | wykrycia z GPS i pewnoscia |
| Uzasadnienie decyzji | notatka z pamieci | raport z suma kontrolna |

*Mowisz:* "Straz, nie policja - to PSP prowadzi dzialania powodziowe w KSRG."

---

## SLAJD 4 - Konkretny problem operacyjny

### Powodz. Rzeka Wislok wystepuje z brzegow.

Trzy pytania, na ktore centrum kryzysowe nie ma odpowiedzi:
1. Ktore drogi sa jeszcze przejezdne?
2. Gdzie woda przybiera najszybciej?
3. Czy ktos zostal odciety?

*Mowisz:* "Bierzemy jeden konkretny problem i prowadzimy go do konca."

---

## SLAJD 5 - Proces: 10 krokow

```
1 zgloszenie -> 2 ocena floty -> 3 zaznaczenie obszaru ->
4 SYSTEM dzieli obszar -> 5 kontrola stref -> 6 LOT ->
7 AI analizuje -> 8 alert + potwierdzenie -> 9 RAPORT -> 10 DZIALANIE
```

**Calosc: okolo 30 minut od zgloszenia do decyzji.**

*Mowisz:* "Dron to krok szosty z dziesieciu. Cala reszta to system,
ktory zamienia to co on widzi w decyzje."

---

## SLAJD 6 - Niepewnosc danych (ICH PYTANIE)

### System nigdy nie twierdzi, ze jest pewny

- kazde wykrycie ma **poziom pewnosci AI**, nie tylko ramke
- operator klika **POTWIERDZONE** albo **ODRZUCONE**
- raport ma dwie sekcje: **potwierdzone przez czlowieka** i **niepotwierdzone - AI**
- kazda obserwacja ma **wiek**: "sprzed 4 minut"

*Mowisz:* "Pytali Panstwo, co sie dzieje z niepewnymi danymi z drona.
U nas niepewnosc jest widoczna, a nie ukryta. Dowodzacy nigdy nie
dziala na liczbie, nie wiedzac skad ona pochodzi."

---

## SLAJD 7 - DEMO NA ZYWO (przelacz na platforme)

**1.** Zaznaczam obszar -> flota dzieli go miedzy siebie
**2.** Przelaczam na tryb Powodz -> AI mierzy procent wody
**3.** Otwieram Raport Sytuacyjny -> rozdaje wydruki Jury

**I najwazniejsze:** podaj telefon komus z Jury z linkiem `/share`.
Widzi ten sam zywy obraz. Bez instalacji, bez konta.

*Mowisz:* "To jest odpowiedz na "zly dostep". Nie da sie tego pokazac
slajdem."

---

## SLAJD 8 - Etyka i zgodnosc z prawem (WYMAGANE)

### Rozwiazanie wylacznie cywilne, z czlowiekiem w petli

| Zasada | Jak jest zrealizowana |
|---|---|
| **Czlowiek decyduje, nie AI** | operator potwierdza kazde wykrycie; system nigdy nie dziala sam |
| **Brak efektorow** | swiadoma decyzja: budujemy warstwe decyzyjna, nie bron |
| **Prywatnosc** | AI dziala lokalnie, obraz nie opuszcza maszyny ani kraju |
| **Zgodnosc z przepisami lotniczymi** | misja w strefe zakazana jest odrzucana; dron w niej sam zawraca |
| **Rozliczalnosc** | suma kontrolna SHA-256 - mozna udowodnic, ze raportu nie zmieniono |
| **Tylko zastosowania cywilne** | pozar, powodz, poszukiwanie ludzi |

*Mowisz:* "Panstwo powiedzieli: etycznie i legalnie, tylko cywilnie,
tylko defensywnie. My trzymamy sie tego od poczatku, nie od dzis rano.
Nie budujemy efektorow. AI niczego nie rozstrzyga sama. Obraz nie
opuszcza maszyny. A suma kontrolna chroni i obywatela, i sluzbe -
bo pozniej widac, na jakiej podstawie zapadla decyzja."

---

## SLAJD 9 - Co dziala dzis, a czego nie mamy

| DZIALA DZIS | NIE MAMY |
|---|---|
| mapa floty, telemetria | nie lecielismy prawdziwym dronem - zlacze gotowe, nie testowane |
| podzial obszaru | integracja PansaUTM jest symulowana |
| AI: ludzie, pozar, powodz | roj 200 dronow to koncepcja |
| strefy zakazu lotow | **nie mamy jeszcze zadnego klienta** |
| Raport Sytuacyjny PDF | |

*Mowisz:* "Mowimy to sami, zanim ktos zapyta."

---

## SLAJD 10 - Czego szukamy

### Jednego wdrozenia pilotazowego

Nie sprzedazy. Jednego cwiczenia z prawdziwa sluzba.

**Zespol SkyOps** - getskyops.com

*Mowisz:* "Jestesmy dwie osoby z dzialajacym systemem i bez ani jednego
klienta. Szukamy jednej komendy powiatowej, ktora uzyje tego na
cwiczeniu i powie nam, co jest zle."

---
---

# PYTANIA OD JURY - 2 minuty

**"Ile z tego zbudowaliscie w 24 godziny?"**
> "Platforma istniala wczesniej - przyszlismy z dzialajacym systemem.
> W ciagu tych 24 godzin zbudowalismy [X]. Mowimy to sami."

**"Czy to lata prawdziwym dronem?"**
> "Zlacze MAVLink jest napisane, ten sam ekran steruje maszyna PX4.
> To co widzicie to nasz symulator, bo jestesmy w budynku. Nie
> testowalismy tego w powietrzu."

**"Gdzie tu dual use?"** (organizator powiedzial: tylko cywilne)
> "Zostajemy po stronie cywilnej - tak brzmi zadanie. Budujemy warstwe
> decyzyjna dla sluzb ratowniczych. Efektorow nie budujemy w ogole,
> i to nie jest decyzja na dzis, tylko od poczatku projektu."

**"Kto tego uzywa?"**
> "Nikt. Dlatego tu jestesmy."

**"Ile Was jest?"**
> "Dwie osoby. Ja biznes i prezentacja, moj partner techniczny buduje."

---

# UWAGA: SKLAD ZESPOLU - USTAL PRZED ZLOZENIEM

Regulamin wymaga podania skladu. Jack nie jest zarejestrowany i nie ma
go na miejscu, ale praca techniczna jest jego. Uczciwie: podac oba
nazwiska z adnotacja, ze partner techniczny pracowal zdalnie.

**Nie zmyslaj skladu.** To jedyna rzecz, ktora moze uniewaznic
wszystko inne.
