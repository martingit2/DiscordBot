# bot.py (tilpasset for discord.py)

import discord
from discord.ext import commands  # <--- ENDRING 1: Importer 'commands'
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080/api/v1")

intents = discord.Intents.default()
intents.message_content = True

# --- ENDRING 2: Bruk commands.Bot i stedet for discord.Bot ---
bot = commands.Bot(command_prefix="/", intents=intents)  # command_prefix er nødvendig, selv for slash-kommandoer


@bot.event
async def on_ready():
    print(f"{bot.user} er nå online!")
    print("Synkroniserer slash-kommandoer...")
    try:
        synced = await bot.tree.sync()  # Synkroniserer kommandoene med Discord
        print(f"Synkroniserte {len(synced)} kommando(er).")
    except Exception as e:
        print(f"Kunne ikke synkronisere kommandoer: {e}")
    print("-" * 20)


# --- ENDRING 3: Bruk @bot.tree.command() for slash-kommandoer ---
@bot.tree.command(name="ping", description="Sjekker om boten er online.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@bot.tree.command(name="stats", description="Hent siste tabellstatistikk for et lag.")
async def stats(interaction: discord.Interaction, lagnavn: str):
    await interaction.response.defer()  # Fortell Discord at vi jobber med saken
    try:
        # Dummy-data forblir den samme
        team_data = {
            "teamName": lagnavn.title(), "winsTotal": 10, "drawsTotal": 5, "lossesTotal": 3,
            "points": 35, "goalDifference": 15
        }

        embed = discord.Embed(
            title=f"Statistikk for {team_data['teamName']}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Poeng", value=team_data['points'], inline=True)
        embed.add_field(name="Målforskjell", value=f"+{team_data['goalDifference']}", inline=True)
        embed.add_field(name="Resultat (V-U-T)",
                        value=f"{team_data['winsTotal']}-{team_data['drawsTotal']}-{team_data['lossesTotal']}",
                        inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"En uventet feil oppstod: {e}")


bot.run(BOT_TOKEN)