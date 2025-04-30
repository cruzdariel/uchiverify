import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
import csv
import random
import pytz
import urllib.parse
import re
from datetime import datetime, timedelta
import requests
load_dotenv()

CSV_PATH = "shadydealer.csv"
SCAV_PATH = "scav.csv"

def get_random_article():
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        article = random.choice(reader)
        title = article.get("Title", "Untitled").strip()
        url = article.get("URL", "").strip()
        author = article.get("Author", "Unknown").strip()
        return title, url, author

def get_random_scav():
    with open(SCAV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        item = random.choice(reader)
        number = item.get("Item", "UNK ITEM.").strip()
        description = item.get("Description", "").strip()
        pointvalue = item.get("Points", "[UNK POINTS]").strip()
        return number, description, pointvalue

# Logging configuration: logs to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)

# Discord intents (require members intent for role management)
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)  # prefix not used for slash, but required by Bot

# Define a View with a Button for verification
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view (no timeout)
        self.add_item(discord.ui.Button(
            label="Privacy Policy",
            style=discord.ButtonStyle.secondary,  # Grey button
            url="https://github.com/cruzdariel/uchiverify/blob/main/README.md#privacy-policy"
        ))
    @discord.ui.button(label="Verify Now", style=discord.ButtonStyle.primary, custom_id="verify_now_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle button clicks by sending the user their unique verification link."""
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        # Construct the external verification URL with query parameters
        verify_url = f"https://vps.dariel.us/uchiverify/auth/start?guild_id={guild_id}&user_id={user_id}"
        # Send an ephemeral message to the user with the link (only the user can see this)
        await interaction.response.send_message(
            f"Please **[click here]({verify_url})** to verify your UChicago affiliation  via Okta.",
            ephemeral=True
        )
        logging.info(f"Sent verification link to user {user_id} in guild {guild_id}")

@bot.tree.command(name="setchannel", description="Post UChicago verification message in this channel (admins only)")
async def setchannel(interaction: discord.Interaction):
    """Slash command to initialize verification in the current channel (admin only)."""
    # Check that the user has administrator permission
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need to be a server admin to use this command.", ephemeral=True)
        return
    # Create the embed message
    embed = discord.Embed(
        title="Verify your UChicago Affiliation",
        description="Click the button below to verify your UChicago email and get access.",
        colour=0x800000)
    embed.set_author(
        name="UChiVerify",
        url="https://discord.gg/syNk2wNp2x",
        icon_url="https://camo.githubusercontent.com/a56e4acafe0c671c795cd5b1d86c7262514a99408d5a81d040dc45db8456bf6c/68747470733a2f2f692e696d6775722e636f6d2f74614967354b622e706e67")
    view = VerifyView()
    # Send the embed with the Verify button
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ Verification prompt posted in this channel.", ephemeral=True)
    logging.info(f"/setchannel used by {interaction.user.id} in guild {interaction.guild.id} (channel {interaction.channel.id})")

@bot.tree.command(name="gethelp", description="Get a link to the support Discord server.")
async def support(interaction: discord.Interaction):
    """Slash command to send a private message with the support server link."""
    support_link = "https://discord.gg/syNk2wNp2x" 

    embed = discord.Embed(
        title="Need Help?",
        description=f"If you need assistance, join our support server here: [Support Server]({support_link})",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)
    logging.info(f"/gethelp used by {interaction.user.id} in guild {interaction.guild.id} (channel {interaction.channel.id})")

@bot.tree.command(name="shadydealer", description="Get a random article title from the Shady Dealer")
async def random_article(interaction: discord.Interaction):
    title, url, author = get_random_article()

    # Disable embed preview
    await interaction.response.send_message(
        content=f"**[{title}]({url})**\n*by {author}*",
        allowed_mentions=discord.AllowedMentions.none()
    )
    logging.info(f"/randomarticle used by {interaction.user.id} in guild {interaction.guild.id} (channel {interaction.channel.id})")

@bot.tree.command(name="scav", description="Get a random item from a Scav list (1998-2024)")
async def random_scav(interaction: discord.Interaction):
    number, description, pointvalue = get_random_scav()

    # Disable embed preview
    await interaction.response.send_message(
        content=(f"{number}. {description} [{pointvalue}]\n"
        f"-# Is this item weirdly formatted? Let the bot developer know."),
        allowed_mentions=discord.AllowedMentions.none()
    )
    logging.info(f"/scav used by {interaction.user.id} in guild {interaction.guild.id} (channel {interaction.channel.id})")

@bot.tree.command(name="thingstodo", description="Returns a random RSO event from UChicago Blueprint or events.uchicago.edu")
async def thingstodo(interaction: discord.Interaction):
    await interaction.response.defer()

    events_combined = {}
    now = datetime.now().astimezone()
    cst = pytz.timezone("US/Central")
    encoded_time = urllib.parse.quote(now.isoformat(), safe='')

    # === Source 1: Blueprint ===
    try:
        url1 = (
            f"https://blueprint.uchicago.edu/api/discovery/event/search?"
            f"endsAfter={encoded_time}&orderByField=endsOn&orderByDirection=ascending&"
            f"status=Approved&take=25&query="
        )
        r1 = requests.get(url1)
        r1.raise_for_status()
        data1 = r1.json()["value"]

        for i, event in enumerate(data1):
            name = event["name"]
            event_url = f"https://blueprint.uchicago.edu/event/{event['id']}"
            date = datetime.fromisoformat(event["startsOn"])
            date_str = date.strftime("%A, %B %-d, %Y at %-I:%M %p")
            desc = re.sub('<[^<]+?>', '', event["description"])[:150]
            location = event["location"] or "TBA"

            events_combined[f"bp_{i}"] = {
                "name": name,
                "url": event_url,
                "date": date_str,
                "location": location,
                "desc": desc,
                "source": "Blueprint"
            }
    except Exception as e:
        print("Blueprint error:", e)

    # === Source 2: UChicago Events ===
    try:
        url2 = "https://events.uchicago.edu/live/json/events"
        r2 = requests.get(url2)
        r2.raise_for_status()
        data2 = r2.json()["data"]

        for i, event in enumerate(data2):
            name = event["title"]
            event_url = event["url"]
            date_utc = datetime.strptime(event["date_utc"], "%Y-%m-%d %H:%M:%S")
            date = date_utc.astimezone(cst)
            date_str = date.strftime("%A, %B %-d, %Y at %-I:%M %p")
            location = "Online" if event["is_online"] == 1 else "In-Person"

            events_combined[f"uc_{i}"] = {
                "name": name,
                "url": event_url,
                "date": date_str,
                "location": location,
                "desc": "No description",  # description just repeats the URL
                "source": "UChicago Events"
            }
    except Exception as e:
        print("UChicago Events error:", e)

    if not events_combined:
        await interaction.followup.send("❌ No events found at the moment.")
        return

    # === Pick One and Format ===
    event = random.choice(list(events_combined.values()))
    message = (
        f"[**{event['name']}**]({event['url']})\n"
        f"*{event['date']} | {event['location']}*\n"
        f"{event['desc']}\n"
        f"-# Source: {event['source']}"
    )

    await interaction.followup.send(message)

@bot.event
async def on_ready():
    # Sync slash commands with Discord (register globally)
    try:
        await bot.tree.sync()
        bot.add_view(VerifyView())
        logging.info(f"Logged in as {bot.user}. Slash commands synced.")
    except Exception as e:
        logging.error(f"Failed to sync commands: {e}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        logging.error("Discord bot token not set. Please export DISCORD_BOT_TOKEN.")
        exit(1)
    bot.run(TOKEN)