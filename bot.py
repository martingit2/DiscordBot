# bot.py

import discord
from discord.ext import commands, tasks
import os
import requests
from dotenv import load_dotenv
from datetime import datetime  # Importerer standard datetime-bibliotek

# --- Konfigurasjon ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080/api/v1")

# Leser kanal-ID fra .env og konverterer til integer.
SUMMARY_CHANNEL_ID_STR = os.getenv("SUMMARY_CHANNEL_ID")
SUMMARY_CHANNEL_ID = int(SUMMARY_CHANNEL_ID_STR) if SUMMARY_CHANNEL_ID_STR else None

# Leser Test Server ID fra .env for umiddelbar kommando-synkronisering.
TEST_GUILD_ID_STR = os.getenv("TEST_GUILD_ID")
GUILDS_FOR_DEBUG = [int(TEST_GUILD_ID_STR)] if TEST_GUILD_ID_STR else None

# --- Oppsett av Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents, debug_guilds=GUILDS_FOR_DEBUG)


# --- Hjelpefunksjoner for API-kall ---
def get_portfolios():
    """Henter alle porteføljer fra backend."""
    response = requests.get(f"{API_BASE_URL}/portfolios")
    response.raise_for_status()
    return response.json()


def get_bets_for_portfolio(portfolio_id):
    """Henter alle bets for en gitt portefølje-ID."""
    response = requests.get(f"{API_BASE_URL}/portfolios/{portfolio_id}/bets")
    response.raise_for_status()
    return response.json()


def get_upcoming_fixtures_with_odds():
    """Henter kommende kamper med odds."""
    response = requests.get(f"{API_BASE_URL}/fixtures/upcoming-with-odds")
    response.raise_for_status()
    return response.json()


def count_pending_bets(portfolio_id):
    """Henter kun antallet ventende bets for en portefølje."""
    response = requests.get(f"{API_BASE_URL}/portfolios/{portfolio_id}/bets/count-pending")
    response.raise_for_status()
    return response.json()


# --- Bot Events ---
@bot.event
async def on_ready():
    print(f"{bot.user} er nå online!")
    print("Synkroniserer slash-kommandoer...")
    try:
        synced = await bot.tree.sync()
        if GUILDS_FOR_DEBUG:
            print(f"Synkroniserte {len(synced)} kommando(er) til test-server.")
        else:
            print(f"Synkroniserte {len(synced)} kommando(er) globalt.")
    except Exception as e:
        print(f"Kunne ikke synkronisere kommandoer: {e}")
    print("-" * 20)
    if SUMMARY_CHANNEL_ID:
        if not summary_task.is_running():
            summary_task.start()
            print(f"Startet proaktiv oppsummeringstask for kanal-ID: {SUMMARY_CHANNEL_ID}")
    else:
        print("ADVARSEL: SUMMARY_CHANNEL_ID er ikke satt i .env. Proaktiv oppsummering er deaktivert.")


# --- Proaktiv Oppsummering (Task) ---
@tasks.loop(hours=3)
async def summary_task():
    if not SUMMARY_CHANNEL_ID:
        return

    channel = bot.get_channel(SUMMARY_CHANNEL_ID)
    if not channel:
        print(f"ADVARSEL: Fant ikke kanalen med ID {SUMMARY_CHANNEL_ID}. Oppsummering blir ikke sendt.")
        return

    print("Kjører planlagt oppsummering...")
    try:
        all_portfolios = get_portfolios()
        if not all_portfolios:
            return

        embed = discord.Embed(
            title="Aracanix | Periodisk Porteføljeoppsummering",
            description=f"Statusoppdatering per {discord.utils.format_dt(discord.utils.utcnow(), style='F')}",
            color=discord.Color.dark_blue()
        )

        total_balance = 0
        total_bets = 0

        for p in all_portfolios:
            if not p.get('isActive'): continue

            total_balance += p.get('currentBalance', 0)
            total_bets += p.get('totalBets', 0)
            roi = ((p.get('currentBalance', 0) - p.get('startingBalance', 1)) / p.get('startingBalance', 1)) * 100

            pending_count = count_pending_bets(p['id'])

            value = (
                f"**Saldo:** `{p.get('currentBalance', 0):,.2f} kr`\n"
                f"**ROI:** `{roi:.1f}%`\n"
                f"**Ventende Spill:** `{pending_count}`"
            )
            embed.add_field(name=f"📈 {p.get('name')}", value=value, inline=True)

        embed.set_footer(text=f"Total saldo: {total_balance:,.2f} kr | Totalt {total_bets} bets plassert.")
        await channel.send(embed=embed)

    except Exception as e:
        print(f"FEIL under kjøring av summary_task: {e}")
        try:
            await channel.send(f"🚨 Kunne ikke generere porteføljeoppsummering. Feil: `{e}`")
        except Exception as discord_e:
            print(f"Kunne ikke sende feilmelding til Discord heller: {discord_e}")


# --- Slash-kommandoer ---
@bot.tree.command(name="ping", description="Sjekker om boten er online.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@bot.tree.command(name="portfolios", description="Viser en oversikt over alle dine porteføljer.")
async def portfolios(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        portfolios_data = get_portfolios()
        if not portfolios_data:
            await interaction.followup.send("Fant ingen porteføljer.")
            return
        embed = discord.Embed(title="Porteføljeoversikt", color=discord.Color.purple())
        for p in portfolios_data:
            status_emoji = "🟢 Aktiv" if p.get('isActive') else "🔴 Inaktiv"
            roi = ((p.get('currentBalance', 0) - p.get('startingBalance', 1)) / p.get('startingBalance', 1)) * 100
            field_value = (
                f"**Saldo:** {p.get('currentBalance', 0):,.2f} kr\n"
                f"**ROI:** `{roi:.1f}%`\n"
                f"**Modell:** `{p.get('model', {}).get('modelName', 'N/A')}`"
            )
            embed.add_field(name=f"{p.get('name')}  {status_emoji}", value=field_value, inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Feil i /portfolios: {e}")
        await interaction.followup.send(f"Kunne ikke hente porteføljer. Sjekk om backenden kjører.")


@bot.tree.command(name="bets", description="Viser nylige spill for en spesifikk portefølje.")
async def bets(interaction: discord.Interaction, porteføljenavn: str):
    await interaction.response.defer()
    try:
        all_portfolios = get_portfolios()
        target_portfolio = next((p for p in all_portfolios if p['name'].lower() == porteføljenavn.lower()), None)
        if not target_portfolio:
            await interaction.followup.send(f"Fant ingen portefølje med navnet '{porteføljenavn}'.")
            return
        bets_data = get_bets_for_portfolio(target_portfolio['id'])
        if not bets_data:
            await interaction.followup.send(f"Porteføljen '{porteføljenavn}' har ingen plasserte spill.")
            return
        embed = discord.Embed(title=f"Nylige Spill for {target_portfolio['name']}", color=discord.Color.gold())
        for bet in bets_data[:10]:
            status_map = {"PENDING": "⏳", "WON": "✅", "LOST": "❌", "PUSH": "⚪️"}
            status_emoji = status_map.get(bet.get('status'), '❔')
            resultat = f"{bet.get('profit', 0):+.2f} kr" if bet.get('profit') is not None else "---"
            field_name = f"{status_emoji} {bet.get('homeTeamName')} vs {bet.get('awayTeamName')}"
            field_value = (
                f"**Spill:** {bet.get('selection')} ({bet.get('market')})\n"
                f"**Innsats:** {bet.get('stake'):.2f} kr @ {bet.get('odds'):.2f}\n"
                f"**Resultat:** `{resultat}`"
            )
            embed.add_field(name=field_name, value=field_value, inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Feil i /bets: {e}")
        await interaction.followup.send(f"Kunne ikke hente spill. Sjekk om backenden kjører.")


@bot.tree.command(name="upcoming", description="Viser de neste kommende kampene med odds.")
async def upcoming(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        fixtures_data = get_upcoming_fixtures_with_odds()
        if not fixtures_data:
            await interaction.followup.send("Fant ingen kommende kamper med odds.")
            return
        embed = discord.Embed(title="Kommende Kamper med Odds", description="Viser de første 10 kampene i systemet.",
                              color=discord.Color.teal())
        for fixture in fixtures_data[:10]:
            odds_str = "Odds mangler"
            match_winner_odds = next((o for o in fixture.get('odds', []) if o.get('betName') == 'Match Winner'), None)
            if match_winner_odds:
                home = next((d['odds'] for d in match_winner_odds['odds'] if d['name'] == 'Home'), 'N/A')
                draw = next((d['odds'] for d in match_winner_odds['odds'] if d['name'] == 'Draw'), 'N/A')
                away = next((d['odds'] for d in match_winner_odds['odds'] if d['name'] == 'Away'), 'N/A')
                odds_str = f"H: {home} | U: {draw} | B: {away}"

            kamp_navn = f"{fixture.get('homeTeamName')} vs {fixture.get('awayTeamName')}"

            # Bruker datetime.fromisoformat for å parse dato-strengen
            tidspunkt = datetime.fromisoformat(fixture.get('date'))

            liga_og_tid = f"{fixture.get('leagueName')} - {discord.utils.format_dt(tidspunkt, style='f')}"

            embed.add_field(name=kamp_navn, value=f"{liga_og_tid}\n`{odds_str}`", inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Feil i /upcoming: {e}")
        await interaction.followup.send(f"Kunne ikke hente kommende kamper.")


# --- Start boten ---
if __name__ == '__main__':
    if not BOT_TOKEN:
        print("FEIL: BOT_TOKEN er ikke satt i .env-filen.")
    else:
        if not GUILDS_FOR_DEBUG:
            print(
                "INFO: Ingen TEST_GUILD_ID satt i .env. Kommandoer vil synkroniseres globalt (kan ta opptil en time).")
        bot.run(BOT_TOKEN)