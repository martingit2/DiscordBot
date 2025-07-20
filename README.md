# Aracanix Discord Bot

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![discord.py](https://img.shields.io/badge/discord.py-v2.5.2-7289DA.svg)
![Status](https://img.shields.io/badge/status-under%20development-orange.svg)

Dette repositoryet inneholder koden for den interaktive Discord-boten til **Aracanix Analyseplattform**. Boten fungerer som en dedikert mikrotjeneste som gir brukere en "on-demand" tilgang til data og analyser fra hovedplattformen, direkte via et chat-grensesnitt i Discord.

## Arkitektur

Boten er bygget i Python ved hjelp av `discord.py`-biblioteket. Den er designet for å være en **klient** av den sentrale **Aracanix Java Backend**. All logikk og databehandling skjer i backenden; denne boten er utelukkende ansvarlig for:

1.  Å lytte etter slash-kommandoer i en Discord-server.
2.  Parse brukerens input.
3.  Gjøre REST API-kall til den relevante endepunktet på Java-backenden.
4.  Motta JSON-data tilbake.
5.  Formatere dataen til pene, lesbare "embed"-meldinger og poste dem som svar i Discord.

## Funksjoner

### Nåværende Funksjonalitet
*   **Tilkobling:** Boten kan koble seg til Discord og vise en "online" status.
*   **/ping:** En enkel kommando for å verifisere at boten er responsiv.
*   **/stats `[lagnavn]`:** Henter statistikk for et spesifikt lag (bruker foreløpig dummy-data).

### Planlagte Funksjoner (To-Do)
*   Integrere `/stats`-kommandoen med det ekte backend-API-et.
*   Implementere `/bets [porteføljenavn]` for å vise nylige spill fra en portefølje.
*   Implementere `/upcoming_games [liga]` for å vise kommende kamper.
*   Sikre kommunikasjonen med backenden via en hemmelig API-nøkkel.

## Kom i gang (Oppsett for utvikling)

Følg disse stegene for å kjøre boten lokalt.

### Forutsetninger
*   Python 3.11 eller nyere.
*   En kjørende instans av [Aracanix Backend](https://github.com/ditt-brukernavn/aracanix-backend) (link til ditt backend-repo).
*   En Discord Bot Token.

### 1. Klon Repositoryet
```bash
git clone https://github.com/martingit2/DiscordBot.git
cd DiscordBot
```

### 2. Sett opp Virtuelt Miljø
Det anbefales på det sterkeste å bruke et virtuelt miljø for å isolere prosjektets avhengigheter.

```bash
# Opprett miljøet
python -m venv .venv

# Aktiver miljøet
# På Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# På macOS/Linux:
# source .venv/bin/activate
```
Du vil se `(.venv)` i starten av terminal-prompten din når miljøet er aktivt.

### 3. Installer Avhengigheter
Opprett først en `requirements.txt`-fil hvis den ikke finnes:
```bash
pip freeze > requirements.txt
```
Installer deretter alle nødvendige pakker:
```bash
pip install -r requirements.txt
```
Hvis `requirements.txt` er tom, kjør:
```bash
pip install discord.py requests python-dotenv
```

### 4. Konfigurer Miljøvariabler
Boten trenger en hemmelig token for å logge inn.

1.  Opprett en fil som heter `.env` i rotmappen av prosjektet.
2.  Kopier innholdet fra malen under og lim det inn i din `.env`-fil.
3.  Erstatt `din_hemmelige_bot_token_her` med din faktiske token fra Discord Developer Portal.

**.env.example** (dette er en mal, ikke endre denne filen)
```
# Discord Bot Token fra https://discord.com/developers/applications
BOT_TOKEN="din_hemmelige_bot_token_her"

# URL til den lokale Aracanix backend-tjenesten
API_BASE_URL="http://localhost:8080/api/v1"
```

**Viktig:** `.env`-filen er ignorert av Git og skal aldri lastes opp.

### 5. Kjør Boten
Sørg for at ditt virtuelle miljø er aktivert, og kjør deretter:
```bash
python bot.py
```
Du skal se en melding i terminalen som bekrefter at boten er online.