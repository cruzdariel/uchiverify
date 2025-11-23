import os
import logging
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import csv
import random
import pytz
import urllib.parse
import re
from datetime import datetime, timedelta
import requests
import aiohttp
from aiohttp import web, ClientTimeout
import asyncio
import io
import json
import base64
from pathlib import Path
load_dotenv()

CSV_PATH = "shadydealer.csv"
SCAV_PATH = "scav.csv"
STATS_PATH = "command_stats.json"

# Initialize or load command statistics
def load_stats():
    """Load command statistics from JSON file."""
    if Path(STATS_PATH).exists():
        try:
            with open(STATS_PATH, 'r') as f:
                return json.load(f)
        except:
            return {"commands": {}}
    return {"commands": {}}

def save_stats(stats):
    """Save command statistics to JSON file."""
    try:
        with open(STATS_PATH, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save stats: {e}")

def track_command(command_name: str):
    """Track command usage statistics (anonymized - no user data collected)."""
    stats = load_stats()

    # Track command counts only
    if command_name not in stats["commands"]:
        stats["commands"][command_name] = 0
    stats["commands"][command_name] += 1

    save_stats(stats)

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

def get_safe_username(user):
    """
    Returns the appropriate username for display.
    If the display name contains special characters, returns the username instead.
    Special characters are anything that's not alphanumeric, space, underscore, or hyphen.
    """
    display_name = user.display_name
    # Check if display name contains any special characters
    if re.search(r'[^a-zA-Z0-9\s_-]', display_name):
        return user.name
    return display_name

def days_in_quarter(year_start, month_start, day_start, year, month, day, quarter_name, tz_name='America/Chicago'):
    # set up timezone and "now"
    tz  = pytz.timezone(tz_name)
    now = datetime.now(tz)

    # your manually chosen target date at midnight
    target = tz.localize(datetime(year, month, day, 0, 0, 0))

    # compute the difference
    delta       = target - now
    days        = delta.days
    rem_seconds = delta.seconds
    hours = rem_seconds // 3600
    rem_seconds %= 3600
    minutes     = rem_seconds // 60
    seconds     = rem_seconds % 60

    start_date = tz.localize(datetime(year_start, month_start, day_start, 0, 0, 0))
    daysspent = (now - start_date).days

    message = f"**DAY NUMBER {daysspent} OF {quarter_name.upper()}!! 🔔** There are {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds remaining in {quarter_name}. \n\n https://vps.dariel.us/uchiverify/images/{daysspent}.png"
    return message


#async def search_course(query: str):
#    """
#    Returns (coursenum, coursename, reviewurl)
#    or raises aiohttp.ClientError on network/API failures,
#    or returns ("", "", error_message) if the API returned no data.
#    """
#    base = "https://api.uofcourses.com"
#    timeout = ClientTimeout(total=5)
#    async with aiohttp.ClientSession(timeout=timeout) as session:
#        # 1) Search endpoint
#        url_search = f"{base}/Courses/Search?queryString={query}&page=0&pageSize=1"
#        async with session.get(url_search) as resp:
#            if resp.status != 200:
#                return "", "", f"Search failed [{resp.status}] for `{query}`"
#            data = await resp.json()
#
#        courses = data.get("courses", [])
#        if not courses:
#            return "", "", f"No course found for `{query}`."
#
#        course = courses[0]
#        # Check the query against normalized courseNumbers
#        if not any(query.lower() in cn.lower() for cn in course.get("courseNumbers", [])):
#            suggestion = course["courseNumbers"][0]
#            return "", "", f"No course found for `{query}` (did you mean `{suggestion}`?)"
#
#        # 2) Fetch the review link
#        course_id = course["id"]
#        url_detail = f"{base}/Courses/Course/{course_id}"
#        async with session.get(url_detail) as resp2:
#            if resp2.status != 200:
#                review_url = ""
#            else:
#                detail = await resp2.json()
#               try:
#                    review_url = detail["sections"][0]["url"]
#                except (KeyError, IndexError):
#                    review_url = ""
#
#        return course["courseNumbers"][0], course["title"], review_url
#
#    course = courses[0]
#    # see if the user’s query actually matches one of the courseNumbers
#    if any(query.lower() in cn.lower() for cn in course.get("courseNumbers", [])):
#        # exact-ish match → fetch the review URL
#        def get_latest_review_link(num):
#            ci = requests.get(f"https://api.uofcourses.com/Courses/Course/{num}")
#            data_ci = ci.json()
#            try:
#                return data_ci["sections"][0]["url"]
#            except (IndexError, KeyError):
#                return ""
#        return (
#            course["courseNumbers"][0],
#            course["title"],
#            get_latest_review_link(course["id"])
#        )
#    else:
#        # found something, but query didn’t match the normalized courseNumbers
#        suggestion = course["courseNumbers"][0]
#        return "", "", f"No course found for `{query}` (did you mean `{suggestion}`?)"

# ── Health endpoint ───────────────────────────────────────────────────────────
routes = web.RouteTableDef()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

def check_admin_password(request):
    """Check if the provided password matches the admin password."""
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Basic '):
        try:
            decoded = base64.b64decode(auth[6:]).decode('utf-8')
            username, password = decoded.split(':', 1)
            return password == ADMIN_PASSWORD
        except:
            return False
    return False

@routes.get("/bothealth")
async def health(request):
    # you could add deeper checks here if you like
    return web.json_response({"status": "ok"}, status=200)

@routes.get("/admin")
async def admin_servers(request):
    """Password-protected page showing all servers the bot is in and usage stats."""
    # Check authentication
    if not check_admin_password(request):
        return web.Response(
            text="Access denied",
            status=401,
            headers={'WWW-Authenticate': 'Basic realm="UChiVerify Admin"'}
        )

    # Get all guilds the bot is in
    guilds_info = []
    for guild in bot.guilds:
        try:
            owner = await guild.fetch_member(guild.owner_id) if guild.owner_id else None
            if owner:
                # Get the username (not display_name)
                owner_name = f"@{owner.name}"
                if owner.discriminator != "0":  # Legacy username
                    owner_name = f"{owner.name}#{owner.discriminator}"
            else:
                owner_name = "Unknown"
        except:
            owner_name = f"Unknown (ID: {guild.owner_id})"

        guilds_info.append({
            'name': guild.name,
            'id': guild.id,
            'owner': owner_name,
            'member_count': guild.member_count
        })

    # Sort by member count descending
    guilds_info.sort(key=lambda x: x['member_count'], reverse=True)

    # Load command statistics
    stats = load_stats()
    total_commands = sum(stats["commands"].values())

    # Generate HTML
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Server List | UChiVerify Admin</title>
        <style>
            @font-face {
                font-family: 'Gotham';
                src: url("https://vps.dariel.us/uchiverify/static/fonts/Gotham/Gotham-Book.otf") format("opentype");
                font-weight: normal;
                font-style: normal;
            }
            @font-face {
                font-family: 'Gotham Bold';
                src: url("https://vps.dariel.us/uchiverify/static/fonts/Gotham/Gotham-Bold.otf") format("opentype");
                font-weight: bold;
                font-style: normal;
            }
            body {
                font-family: 'Gotham', Arial, sans-serif;
                background-color: #1a1a1a;
                color: #e0e0e0;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: #2a2a2a;
                border: 1px solid #444;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 6px 10px rgba(0,0,0,0.6);
            }
            h1 {
                font-family: 'Gotham Bold', Arial, sans-serif;
                color: #800000;
                margin-bottom: 10px;
                font-size: 2rem;
            }
            .stats {
                font-size: 1rem;
                color: #999;
                margin-bottom: 30px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th {
                background-color: #800000;
                color: white;
                padding: 12px;
                text-align: left;
                font-family: 'Gotham Bold', Arial, sans-serif;
            }
            td {
                padding: 12px;
                border-bottom: 1px solid #444;
            }
            tr:hover {
                background-color: #333;
            }
            .server-name {
                font-weight: bold;
                color: #fff;
            }
            .server-id {
                color: #999;
                font-size: 0.9em;
            }
            .member-count {
                color: #4CAF50;
                font-weight: bold;
            }
            h2 {
                font-family: 'Gotham Bold', Arial, sans-serif;
                color: #800000;
                margin-top: 40px;
                margin-bottom: 15px;
                font-size: 1.5rem;
                border-bottom: 2px solid #800000;
                padding-bottom: 10px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            .stat-box {
                background-color: #333;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #800000;
            }
            .stat-label {
                color: #999;
                font-size: 0.9em;
                margin-bottom: 5px;
            }
            .stat-value {
                color: #fff;
                font-size: 1.5em;
                font-weight: bold;
            }
            .command-name {
                color: #4CAF50;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>UChiVerify Admin Dashboard</h1>

            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-label">Total Servers</div>
                    <div class="stat-value">""" + str(len(guilds_info)) + """</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Total Members</div>
                    <div class="stat-value">""" + f"{sum(g['member_count'] for g in guilds_info):,}" + """</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Commands Executed</div>
                    <div class="stat-value">""" + f"{total_commands:,}" + """</div>
                </div>
            </div>

            <h2>Top Commands</h2>
            <table>
                <thead>
                    <tr>
                        <th>Command</th>
                        <th>Usage Count</th>
                    </tr>
                </thead>
                <tbody>
    """

    # Add top commands
    sorted_commands = sorted(stats["commands"].items(), key=lambda x: x[1], reverse=True)[:10]
    for cmd_name, count in sorted_commands:
        html += f"""
                    <tr>
                        <td class="command-name">/{cmd_name}</td>
                        <td class="member-count">{count:,}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>

            <h2>Server List</h2>
            <table>
                <thead>
                    <tr>
                        <th>Server Name</th>
                        <th>Server ID</th>
                        <th>Owner</th>
                        <th>Members</th>
                    </tr>
                </thead>
                <tbody>
    """

    for guild in guilds_info:
        html += f"""
                    <tr>
                        <td class="server-name">{guild['name']}</td>
                        <td class="server-id">{guild['id']}</td>
                        <td>{guild['owner']}</td>
                        <td class="member-count">{guild['member_count']:,}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    return web.Response(text=html, content_type='text/html')

async def start_health_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8765)
    await site.start()
    print("🌐 Web server running at http://0.0.0.0:8765/")
    print("   - Health endpoint: http://0.0.0.0:8765/bothealth")
    print("   - Admin panel: http://0.0.0.0:8765/admin")

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
            url="https://uchiverify.dariel.us/privacy.html"
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
    track_command("setchannel")

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
    track_command("gethelp")

@bot.tree.command(name="shadydealer", description="Get a random article title from the Shady Dealer.")
async def random_article(interaction: discord.Interaction):
    title, url, author = get_random_article()

    embed = discord.Embed(
        title=title,
        url=url,
        description=f"*by {author}*",
        color=0x800000
    )

    await interaction.response.send_message(
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none()
    )
    logging.info(f"/shadydealer used by {interaction.user.id} in guild {interaction.guild.id} (channel {interaction.channel.id})")
    track_command("shadydealer")

@bot.tree.command(name="daysinquarter", description="Use this command if you're wondering how long the rest of your journey will be this quarter.")
async def daysinquarter(interaction: discord.Interaction):
    tz = pytz.timezone('America/Chicago')
    now = datetime.now(tz)

    year_start, month_start, day_start = 2025, 9, 29
    year, month, day = 2025, 12, 13
    quarter_name = "Autumn quarter"

    target = tz.localize(datetime(year, month, day, 0, 0, 0))
    delta = target - now
    days = delta.days
    rem_seconds = delta.seconds
    hours = rem_seconds // 3600
    rem_seconds %= 3600
    minutes = rem_seconds // 60
    seconds = rem_seconds % 60

    start_date = tz.localize(datetime(year_start, month_start, day_start, 0, 0, 0))
    daysspent = (now - start_date).days

    embed = discord.Embed(
        title=f"DAY NUMBER {daysspent} OF {quarter_name.upper()}! 🔔",
        description=f"There are **{days} days, {hours} hours, {minutes} minutes, and {seconds} seconds** remaining in {quarter_name}.",
        color=0x800000
    )
    embed.set_image(url=f"https://vps.dariel.us/uchiverify/images/{daysspent}.png")

    await interaction.response.send_message(
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none()
    )
    logging.info(f"/daysinquarter used by {interaction.user.id} in guild {interaction.guild.id} (channel {interaction.channel.id})")
    track_command("daysinquarter")

@bot.tree.command(name="scav", description="Get a random item from a Scav list (1998-2024)")
async def random_scav(interaction: discord.Interaction):
    number, description, pointvalue = get_random_scav()

    embed = discord.Embed(
        title=f"Item {number}",
        description=f"{description}\n\n**Points:** {pointvalue}",
        color=0x800000
    )
    embed.set_footer(text="SCAV SCAV SCAV! Is this item weirdly formatted? Let the bot developer know.")

    await interaction.response.send_message(
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none()
    )
    logging.info(f"/scav used by {interaction.user.id} in guild {interaction.guild.id} (channel {interaction.channel.id})")
    track_command("scav")

@bot.tree.command(name="finalsmotivation", description="Get some finals motivation with a cute cat gif")
async def finals_motivation(interaction: discord.Interaction):
    await interaction.response.defer()

    username = get_safe_username(interaction.user)

    messages = [
        f"YOU GOT THIS {username.upper()}!",
        f"lock in {username}",
        f"ur gonna kill the final {username}",
        f"{username}, manifesting this curve works for you",
        f"6...7 REASONS TO LOCK TF IN, {username}!",
        f"you don't go to harvard. stop slacking like you do, {username}",
        f"{username}, that econ final isn't gonna pass itself",
        f"touch grass after finals, {username}",
        f"im so hungry i could eat a {username}",
        f"stop doomscrolling, {username}!",
        f"{username}, the curve gods are watching... 👀",
        f"POV: {username} is about to absolutely demolish this exam",
        f"Time to channel that 3am crisis energy, {username}!",
        f"{username}, C's get degrees but A's get internships",
        f"ur parents didn't pay tuition for you to flop, {username}!",
        f"{username}, even the Reg believes in you rn",
        f"{username}, go to reg ex lib needs ur business",
        f"psets psets psets, {username}",
        f"{username}, be the curve breaker not the curve victim"
    ]

    message_text = random.choice(messages)

    # URL encode the message for the cat image
    encoded_text = urllib.parse.quote(message_text)
    cat_url = f"https://cataas.com/cat/cute/says/{encoded_text}"

    # Download the image
    response = requests.get(cat_url)
    image_data = response.content

    # Create a Discord file from the image data
    file = discord.File(fp=io.BytesIO(image_data), filename="motivation.png")

    # Create embed with the uploaded image and motivational text as title
    embed = discord.Embed(title=message_text, color=0x800000)
    embed.set_image(url="attachment://motivation.png")

    # Ping the user above the embed
    await interaction.followup.send(
        content=f"{interaction.user.mention}",
        embed=embed,
        file=file
    )
    logging.info(f"/finalsmotivation used by {interaction.user.id} in guild {interaction.guild.id} (channel {interaction.channel.id})")
    track_command("finalsmotivation")

#@bot.tree.command(name="coursereview", description="Find reviews for a course code")
#@app_commands.describe(query="Course code to search, e.g. DATA 11800")
#async def get_course_url(interaction: discord.Interaction, query: str):
#    # 1) Acknowledge immediately so Discord doesn’t auto‐cancel after 3 s
#    await interaction.response.defer(ephemeral=True)
#
#    # 2) Call our non-blocking search, catching network/API errors
#    try:
#        coursenum, coursename, reviewurl = await search_course(query)
#    except aiohttp.ClientError as e:
#        return await interaction.followup.send(
#            f"🚨 Could not contact course API: {e}"
#        )
#
#    # 3) Format the three possible outcomes
#    if coursename and reviewurl:
#        payload = f"[{coursenum} – {coursename}]({reviewurl})"
#    elif coursename:
#        payload = f"{coursenum} – {coursename} has no course review."
#    else:
#        payload = reviewurl  # holds our error or suggestion message
#
#    # 4) Send the follow-up reply
#    await interaction.followup.send(
#        content=f"{payload}\n-# Data Source: UofCourses",
#        allowed_mentions=discord.AllowedMentions.none()
#    )
#    logging.info(f"/coursereview used by {interaction.user.id} in {interaction.guild.id}")

class EventView(discord.ui.View):
    def __init__(self, event_url: str):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="View Event Details",
            style=discord.ButtonStyle.link,
            url=event_url
        ))

@bot.tree.command(name="thingstodo", description="Returns a random RSO event from UChicago Blueprint, events.uchicago.edu, or Hyde Park")
@app_commands.describe(timeframe="Filter events within the next 1, 3, or 7 days")
@app_commands.choices(timeframe=[
    app_commands.Choice(name="Next 1 Day", value="1"),
    app_commands.Choice(name="Next 3 Days", value="3"),
    app_commands.Choice(name="Next 7 Days", value="7"),
])
async def thingstodo(interaction: discord.Interaction, timeframe: app_commands.Choice[str] = None):
    await interaction.response.defer()

    events_combined = {}
    now = datetime.now().astimezone()
    cst = pytz.timezone("US/Central")
    encoded_time = urllib.parse.quote(now.isoformat(), safe='')

    # Determine cutoff time based on timeframe
    if timeframe:
        days = int(timeframe.value)
        cutoff = now + timedelta(days=days)
    else:
        cutoff = None

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

            # Filter by timeframe if specified
            if cutoff and date > cutoff:
                continue

            date_str = date.strftime("%A, %B %-d, %Y at %-I:%M %p")
            desc = re.sub('<[^<]+?>', '', event["description"])[:150]
            location = event["location"] or "TBA"

            events_combined[f"bp_{i}"] = {
                "name": name,
                "url": event_url,
                "date": date_str,
                "date_obj": date,
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

            # Filter by timeframe if specified
            if cutoff and date > cutoff:
                continue

            date_str = date.strftime("%A, %B %-d, %Y at %-I:%M %p")
            location = "Online" if event["is_online"] == 1 else "In-Person"

            events_combined[f"uc_{i}"] = {
                "name": name,
                "url": event_url,
                "date": date_str,
                "date_obj": date,
                "location": location,
                "desc": "No description",  # description just repeats the URL
                "source": "UChicago Events"
            }
    except Exception as e:
        print("UChicago Events error:", e)

    # === Source 3: Hyde Park (.ics) ===
    try:
        url3 = "https://welcometohydepark.com/events/list/?ical=1"
        r3 = requests.get(url3)
        r3.raise_for_status()

        # Simple .ics parser (looking for VEVENT blocks)
        ics_data = r3.text
        events_text = ics_data.split("BEGIN:VEVENT")

        for i, event_block in enumerate(events_text[1:]):  # Skip first split (header)
            try:
                # Extract fields
                summary_match = re.search(r'SUMMARY:(.*?)(?:\r?\n)', event_block)
                dtstart_match = re.search(r'DTSTART(?:;[^:]*)?:(.*?)(?:\r?\n)', event_block)
                url_match = re.search(r'URL:(.*?)(?:\r?\n)', event_block)
                location_match = re.search(r'LOCATION:(.*?)(?:\r?\n)', event_block)
                description_match = re.search(r'DESCRIPTION:(.*?)(?:\r?\n)', event_block)

                if not summary_match or not dtstart_match:
                    continue

                name = summary_match.group(1).strip()
                dtstart_str = dtstart_match.group(1).strip()
                event_url = url_match.group(1).strip() if url_match else "https://welcometohydepark.com/events/list/"
                location = location_match.group(1).strip() if location_match else "TBA"
                desc = description_match.group(1).strip()[:150] if description_match else "No description"

                # Parse datetime (handle both formats: YYYYMMDD and YYYYMMDDTHHMMSS)
                if 'T' in dtstart_str:
                    date = datetime.strptime(dtstart_str.replace('Z', ''), "%Y%m%dT%H%M%S")
                else:
                    date = datetime.strptime(dtstart_str, "%Y%m%d")

                # Localize to CST if naive
                if date.tzinfo is None:
                    date = cst.localize(date)
                else:
                    date = date.astimezone(cst)

                # Skip past events
                if date < now:
                    continue

                # Filter by timeframe if specified
                if cutoff and date > cutoff:
                    continue

                date_str = date.strftime("%A, %B %-d, %Y at %-I:%M %p")

                events_combined[f"hp_{i}"] = {
                    "name": name,
                    "url": event_url,
                    "date": date_str,
                    "date_obj": date,
                    "location": location,
                    "desc": desc,
                    "source": "Hyde Park"
                }
            except Exception as event_error:
                print(f"Hyde Park event parse error: {event_error}")
                continue

    except Exception as e:
        print("Hyde Park error:", e)

    if not events_combined:
        await interaction.followup.send("❌ No events found at the moment.")
        return

    # === Pick One and Format ===
    event = random.choice(list(events_combined.values()))

    embed = discord.Embed(
        title=event['name'],
        description=event['desc'],
        color=0x800000
    )
    embed.add_field(name="Date & Time", value=event['date'], inline=False)
    embed.add_field(name="Location", value=event['location'], inline=False)
    embed.set_footer(text=f"Source: {event['source']}")

    view = EventView(event['url'])
    await interaction.followup.send(embed=embed, view=view)
    logging.info(f"/thingstodo used by {interaction.user.id} in guild {interaction.guild.id} (channel {interaction.channel.id})")
    track_command("thingstodo")

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

    async def main():
        # 1) spin up health server
        await start_health_server()
        # 2) then start Discord bot (this will block until shutdown)
        await bot.start(TOKEN)

    asyncio.run(main())