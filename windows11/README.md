# SHK Scout — Windows 11 -porttaus

Käyttää forkissa jo olevia `stronghold_kingdoms_bot/templates/bags/*.png` ja `templates/general/*.png` -kuvia. Alkuperäinen Android/ADB-koodi säilyy ennallaan.

## Käynnistys
1. Lataa `windows11-port`-haara ZIP:nä GitHubista, pura se ja avaa `windows11`-kansio.
2. Avaa Stronghold Kingdoms Windowsissa ja pidä peli samassa resoluutiossa ja zoomissa.
3. Kaksoisklikkaa `KAYNNISTA_WINDOWS11.bat`. Ensimmäinen käynnistys asentaa riippuvuudet. Python 3 vaaditaan.
4. Paina **RAJAA HONOR**, klikkaa kuvasta vähintään kolme rajapistettä ja päätä oikealla hiiren painikkeella.
5. Avaa pelissä scouttausikkuna, valitse **SCOUT-MÄÄRÄN KENTTÄ** ja klikkaa kentän keskustaa esikatselussa.
6. Valitse **SCOUT-MÄÄRÄN OCR** ja klikkaa numeron 1 näyttävän alueen vasen yläkulma ja oikea alakulma.
7. Sulje scouttausikkuna, paina **SKANNAA** ja tarkista tunnistusehdokkaat.
8. **ALOITA** toimii oletuksena testitilassa. Oikeat lähetykset vaativat valintaruudun ja erillisen vahvistuksen.

## Toteutus
- Windowsin ruutukaappaus ja hiiriohjaus ilman ADB:tä
- Alkuperäisen projektin 22 resurssikuvamallin ja Scout/Go/Exit-kuvien käyttö
- Käyttäjän rajaama honor-alue, ehdokkaiden skannaus, jo käytyjen kohteiden välttäminen
- Scout -> määrä 1 -> OCR-vahvistus -> Go -> sulkeminen
- Pysäytys ja PyAutoGUI-hätäpysäytys (hiiri vasempaan yläkulmaan)

## Rajoitukset ja testaus
- Tätä ei ole vielä testattu pelissä. Kuvamallit voivat olla eri kokoisia kuin pelin karttaspritet.
- Honor-alue on ruudun koordinaateissa. Älä vaihda zoomia, resoluutiota tai kartan sijaintia kalibroinnin jälkeen.
- OCR edellyttää erikseen asennettua **Tesseract OCR** -ohjelmaa Windowsissa (Python-paketti yksin ei riitä).
- Ohjelma ei tunnista automaattisesti kylän sijaintia eikä takaa scouttauksen onnistumista.
- Jos Scout-, Go- tai numerokenttää ei tunnisteta varmasti, lähetys pysähtyy. Ei automaattista uudelleenyritystä.
- Tarkista pelin säännöt ennen automaation käyttöä.
