@echo off
REM === Moy MTS: Frida restart s nulya + unpin + keystore-spy (Frida 17) ===
REM Frida SAMA perezapuskaet prilozhenie i slushaet s pervoy sekundy -
REM tak lovim zagruzku klientskogo serta (KeyStore.load + parol).
REM Predusloviya: Pixel_6 zapushen, frida-server OT RUTA, Burp 8080 + invisible, Intercept OFF.
REM Kak polzovatsya: zapusti bat, dozhdis [+] strok, NE zakryvay okno, zhmoy VOYTI v prilozhenii.
REM Ishchi v okne stroku: [KEYSTORE] load() password=[...] - prishli ee mne.
REM Vyhod: Ctrl+C v etom okne.
set PKG=ru.mts.mymts
cd /d "%~dp0"
echo [*] Perezapuskayu %PKG% pod Frida...
frida -U -f %PKG% -l soft\frida_unpin.js -l soft\frida_keystore.js
pause
