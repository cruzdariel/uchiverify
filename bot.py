import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()

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
    @discord.ui.button(label="Verify Now", style=discord.ButtonStyle.primary)
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
        title="Verify your UChicago affiliation",
        description="Click the button below to verify your UChicago email and get access.",
        color=discord.Color.from_rgb(128, 0, 0)  # Maroon color
    )
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

@bot.event
async def on_ready():
    # Sync slash commands with Discord (register globally)
    try:
        await bot.tree.sync()
        logging.info(f"Logged in as {bot.user}. Slash commands synced.")
    except Exception as e:
        logging.error(f"Failed to sync commands: {e}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        logging.error("Discord bot token not set. Please export DISCORD_BOT_TOKEN.")
        exit(1)
    bot.run(TOKEN)