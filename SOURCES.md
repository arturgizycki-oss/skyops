# Źródła

Bibliografia i źródła danych do prezentacji SkyOps
(Dual Use Hackathon, Carpathian Drone Summit, Jasionka, 29–30.09.2026).

## Literatura

1. **Gromek P.**, *Nowe technologie w ochronie ludności w Polsce. Rozwiązania
   dotyczące projektu SILVANUS. Część 2 – twarde technologie i rozwiązania
   służące angażowaniu społecznemu*, Zeszyty Naukowe Pro Publico Bono 2024,
   nr 1 (1), s. 177–192. Akademia Pożarnicza.
   DOI: [10.5604/01.3001.0054.8780](https://doi.org/10.5604/01.3001.0054.8780).
   Licencja CC BY 4.0.
   *W prezentacji:* rozszerzanie zastosowań BSP w ochronie ludności (s. 180),
   technologie detekcji i systemy wspomagania decyzji jako wsparcie służb.

2. **Depczyński R.P.**, *Wybrane aspekty praktycznego wykorzystania ustawy
   o ochronie ludności i obronie cywilnej*, Kwartalnik Bellona 2024 (3),
   s. 11–26. Wojskowy Instytut Wydawniczy.
   DOI: [10.5604/01.3001.0054.9912](https://doi.org/10.5604/01.3001.0054.9912).
   Licencja CC BY-NC-ND 4.0.
   *W prezentacji:* ramy prawne ochrony ludności i obrony cywilnej, zadania
   gminy i powiatu, gotowość społeczeństwa.

## Akty prawne

3. Ustawa z dnia 5 grudnia 2024 r. o ochronie ludności i obronie cywilnej
   (Dz.U. 2024 poz. 1907).
4. Rozporządzenie wykonawcze Komisji (UE) 2019/947 w sprawie przepisów
   i procedur dotyczących eksploatacji bezzałogowych statków powietrznych.

## Dane publiczne używane przez platformę

| Dane | Dostawca | Użycie w SkyOps |
|---|---|---|
| Stany wód i progi ostrzegawcze / alarmowe | IMGW-PIB, [danepubliczne.imgw.pl](https://danepubliczne.imgw.pl/api/data/hydro) | panel wodowskazów, krok 1 procesu |
| Sieć dróg (7 197 odcinków, okolice Jasionki) | © OpenStreetMap contributors, licencja ODbL | ocena przejezdności dróg |
| Podkład mapy | © OpenStreetMap contributors | mapa operatora, praca offline z pamięci |

Pełny katalog danych publicznych (GUGiK, IMGW-PIB, Copernicus, dane.gov.pl)
przekazali organizatorzy. BDOT10k i ortofotomapa GUGiK są w planie
rozwoju, nie w obecnej wersji.

## Modele i oprogramowanie

| Element | Źródło | Licencja |
|---|---|---|
| Detekcja osób i pojazdów, YOLOv8n | [Ultralytics](https://github.com/ultralytics/ultralytics) | AGPL-3.0 |
| Detekcja ognia i dymu | [SHOU-ISD/fire-and-smoke](https://huggingface.co/SHOU-ISD/fire-and-smoke), Hugging Face | wg repozytorium autora |
| Mapa w przeglądarce | [Leaflet](https://leafletjs.com) | BSD-2-Clause |
| Backend | FastAPI, OpenCV, ReportLab | MIT / Apache-2.0 / BSD |

Pomiar zalania (% powierzchni wody) to własna metoda zespołu: segmentacja
koloru i faktury, bez uczenia maszynowego.

## Materiał wideo i grafiki

- Nagrania testowe z drona: [Mixkit](https://mixkit.co), licencja Mixkit
  Free License. Powódź: klip #9953. Pożar: klip #11028.
  Obraz powodzi to materiał przykładowy, nie nagranie z Podkarpacia.
- Piktogramy do prezentacji (osoba, osoba ze znakiem obrony cywilnej, dron,
  dłoń z monetą, budynek, sygnał) oraz kod QR (getskyops.com):
  materiał własny, autor Jan Pieprzycki. Pliki: [hackathon/grafiki/](hackathon/grafiki/).
- Zrzuty ekranu platformy: materiał własny.
- Znak Państwowej Straży Pożarnej: użyty wyłącznie, aby wskazać docelowego
  użytkownika. SkyOps nie jest produktem PSP ani przez nią rekomendowany.
- LoRa® jest znakiem towarowym Semtech Corporation. Zdjęcie modułu SX1276
  ilustruje kanał łączności z planu rozwoju. Obu nie publikujemy
  w repozytorium, bo nie są naszym materiałem.
