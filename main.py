import os
import discord
from discord import app_commands
from dotenv import load_dotenv
import aiohttp
import asyncio
import re
from datetime import datetime, timedelta

# Load variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ALBUM_URL = os.getenv('ALBUM_URL')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))
COMMITTEE_CHANNEL_ID = int(os.getenv('COMMITTEE_CHANNEL_ID'))
COMMITTE_ROLE_ID = int(os.getenv('COMMITTE_ROLE_ID'))
MEMBER_ROLE_ID = os.getenv('MEMBER_ROLE_ID')
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
SPINS_CHANNEL_NAME = os.getenv("SPINS_CHANNEL_NAME")

VENUES = {
    "ticknock": {"lat": 53.24, "lon": -6.25},
    "djouce": {"lat": 53.12, "lon": -6.22},
    "carrick": {"lat": 53.15, "lon": -6.27},
    "ballinastoe": {"lat": 53.10, "lon": -6.28},
    "ballyhoura": {"lat": 52.33, "lon": -8.53},
    "lead mines": {"lat": 53.23, "lon": -6.16}, # For "the lead mines" etc.
}

if not TOKEN:
    raise ValueError("ERROR: DISCORD_TOKEN is missing from environment variables!")
if not ALBUM_URL:
    print("WARNING: ALBUM_URL is missing. /photos command might fail.")
if not MEMBER_ROLE_ID:
    print("WARNING: MEMBER_ROLE_ID is missing from environment variables! The /photos command will not be restricted to members.")
    MEMBER_ROLE_ID = 0  # Set to 0 to indicate no restriction
else:
    MEMBER_ROLE_ID = int(MEMBER_ROLE_ID)


class MadBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # Allows the bot to see and manage users
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # 1. Register persistent views (Onboarding Buttons)
        self.add_view(OnboardingView())

        # This syncs the slash commands to the Discord API
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

client = MadBot()

def is_member():
    def predicate(interaction: discord.Interaction) -> bool:
        if MEMBER_ROLE_ID == 0:
            return True  # No role restriction if ID is not set

        member_role = discord.utils.get(interaction.guild.roles, id=MEMBER_ROLE_ID)
        
        if member_role is None:
            # This is a server-side check, so we just log it.
            print(f"Warning: Role with ID {MEMBER_ROLE_ID} not found in guild {interaction.guild.name}.")
            return False

        return member_role in interaction.user.roles
    return app_commands.check(predicate)

# @client.tree.command(name="photos", description="Get the link to the MAD MTB Google Photos album")
# @is_member()
# async def photos(interaction: discord.Interaction):
#     await interaction.response.defer(ephemeral=False)

#     embed = discord.Embed(
#         title="📸 MAD MTB Photo Vault",
#         description="Don't let those trail gems sit on your phone! Upload your photos and videos to our shared album.",
#         color=0x78be20  # MAD Green
#     )
#     embed.add_field(name="How to contribute", value=f"Click [HERE]({ALBUM_URL}) to view or upload.")
#     embed.set_footer(text="Club culture is built on shared shredding!")

#     await interaction.followup.send(embed=embed)

# @client.tree.command(name="spin-template", description="Generate a template for posting a new club spin")
# async def spin_template(interaction: discord.Interaction):
#     # This template is pulled directly from your MAD Committee guidelines
#     template = (
#         "**MAD MTB Spin Details**\n"
#         "```\n"
#         "**Date & Time:** \n"
#         "**Meeting Point:** \n"
#         "**Route Distance (km):** \n"
#         "**Elevation:** (e.g., Steep, Medium, Flat etc.) \n"
#         "**Technicality:** (e.g., Beginner/Intermediate/Difficult)\n"
#         "**Pace:** (e.g., Social/Leisurely/Fast-paced)\n"
#         "**Duration:** (Approx hours including breaks)\n"
#         "**Required Equipment:** (e.g., Lights for night rides, extra water)\n"
#         "```\n"
#         "*Tip: Copy the text above and paste it into your new thread in the #spins channel!*"
#     )

#     await interaction.response.send_message(template, ephemeral=True)

# def is_welcome_channel(interaction: discord.Interaction) -> bool:
#     return interaction.channel_id == WELCOME_CHANNEL_ID

# @client.tree.command(name="verify", description="Start your MAD MTB onboarding")
# @app_commands.check(is_welcome_channel)
# async def verify(interaction: discord.Interaction):
#     # This simulates the message that would be sent to a new joiner
#     embed = discord.Embed(
#         title=f"Welcome to MAD MTB!, {interaction.user.display_name}! 🚵‍♂️",
#         description=(
#             "To get you out on the trails with the right access, please select your status:\n\n"
#             "**Paid Member:** You've paid your club fees and need full access.\n"
#             "**Guest / New Rider:** You're here for social spins or just checking us out."
#         ),
#         color=0x78be20 # MAD Green
#     )
#     embed.set_footer(text="If you're stuck, just ask a member of the Committee! 🤘")

#     await interaction.response.send_message(
#         embed=embed,
#         view=OnboardingView(),
#         ephemeral=True
#     )

def parse_spin_time_from_title(title: str) -> datetime:
    """
    Parses a thread title to extract the date and time for a spin.
    Makes assumptions for missing information.
    """
    print(f"[LOG] Parsing title for time: '{title}'")
    now = datetime.now()
    title_lower = title.lower()

    # Defaults
    spin_hour = 10
    spin_minute = 0
    
    # --- Time Parsing ---
    if 'evening' in title_lower:
        spin_hour = 19
        print(f"[LOG] 'evening' keyword found, defaulting to {spin_hour}:00.")
    else:
        # Catches the first time mentioned, e.g., "9:30 meet for 10:00 start" -> 9:30
        time_match = re.search(r'(\d{1,2})[:.](\d{2})', title_lower)
        if time_match:
            spin_hour = int(time_match.group(1))
            spin_minute = int(time_match.group(2))
            print(f"[LOG] Found time in title: {spin_hour:02d}:{spin_minute:02d}")
        else:
            print(f"[LOG] No specific time found, defaulting to {spin_hour}:00.")
            
    # --- Date Parsing ---
    day = None
    month = None
    
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    # Try to find "DD Month" or "DDth Month"
    date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(' + '|'.join(months.keys()) + ')', title_lower)
    if date_match:
        day = int(date_match.group(1))
        month = months[date_match.group(2)]
        print(f"[LOG] Found day and month: Day {day}, Month {month}")
    else:
        # If no month, find just a day number and assume current month
        day_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?', title_lower)
        if day_match:
            day = int(day_match.group(1))
            month = now.month
            print(f"[LOG] Found day only ({day}), assuming current month ({month}).")

    if day is None:
        # If no date at all is found, default to the upcoming Saturday
        print("[LOG] No date info found. Defaulting to upcoming Saturday.")
        days_ahead = (5 - now.weekday() + 7) % 7 # 5 = Saturday
        if days_ahead == 0 and now.hour > 12: # If it's Saturday afternoon, assume next Saturday
            days_ahead = 7
        target_date = now.date() + timedelta(days=days_ahead)
        spin_date = datetime(target_date.year, target_date.month, target_date.day)
    else:
        year = now.year
        # Handle cases where the spin is next year (e.g., it's Dec, spin is in Jan)
        if month < now.month or (month == now.month and day < now.day):
            year += 1
            print(f"[LOG] Parsed date is in the past, assuming next year ({year}).")
        
        try:
            spin_date = datetime(year, month, day)
        except ValueError:
            print(f"[ERROR] Invalid date created (e.g., 31st Feb). Defaulting to upcoming Saturday.")
            days_ahead = (5 - now.weekday() + 7) % 7
            target_date = now.date() + timedelta(days=days_ahead)
            spin_date = datetime(target_date.year, target_date.month, target_date.day)

    final_spin_time = spin_date.replace(hour=spin_hour, minute=spin_minute, second=0, microsecond=0)
    print(f"[LOG] Final parsed spin time: {final_spin_time.strftime('%Y-%m-%d %H:%M')}")
    return final_spin_time

async def get_weather_forecast(session: aiohttp.ClientSessionlocation, location: str, lat: float, lon: float, spin_time: datetime) -> str:
    """Fetches a 3-hour forecast for a given location using OpenWeatherMap API."""
    if not OPENWEATHER_API_KEY:
        print("Warning: OPENWEATHER_API_KEY not configured.")
        return "⚠️ OpenWeather API key is not configured. Cannot fetch weather."

    display_name = location.title() if location else "the specified location"

    try:
        # --- Step 1: Get coordinates if not provided ---
        if lat is None or lon is None:
            print(f"[LOG] No coords provided. Geocoding location: '{location}'")
            if not location:
                return "❌ No location or coordinates provided."

            GEO_URL = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={OPENWEATHER_API_KEY}"
            async with session.get(GEO_URL) as response:
                response.raise_for_status()
                geo_data = await response.json()
                if not geo_data:
                    return f"❌ Could not find location: **{location}**. Please check the spelling or be more specific."

                lat = geo_data[0]['lat']
                lon = geo_data[0]['lon']
                country = geo_data[0]['country']
                state = geo_data[0].get('state', '')
                display_name = f"{location.title()}, {state}" if state else f"{location.title()}, {country}"
        else:
             print(f"[LOG] Using provided coordinates: Lat={lat}, Lon={lon}")

        # --- Step 2: Get weather forecast using coordinates ---
        print(f"[LOG] Fetching forecast from OpenWeatherMap API for Lat={lat}, Lon={lon}")
        weather_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        async with session.get(weather_url) as response:
            response.raise_for_status()
            forecast_data = await response.json()
            print("[LOG] Successfully parsed weather data.")

            spin_timestamp = spin_time.timestamp()
            closest_forecast = min(forecast_data['list'], key=lambda x: abs(x['dt'] - spin_timestamp))
                
            forecast_time = datetime.fromtimestamp(closest_forecast['dt'])
            weather_desc = closest_forecast['weather'][0]['description'].title()
            temp = closest_forecast['main']['temp']
            feels_like = closest_forecast['main']['feels_like']
            wind_speed_ms = closest_forecast['wind']['speed']
            wind_speed_kmh = wind_speed_ms * 3.6  # Convert m/s to km/h
            rain_3h = closest_forecast.get('rain', {}).get('3h', 0)

            forecast_time_str = forecast_time.strftime('%a %d, %H:%M')

            # Get a weather emoji
            icon = closest_forecast['weather'][0]['icon']
            if '01' in icon: emoji = '☀️' # clear
            elif '02' in icon: emoji = '🌤️' # few clouds
            elif '03' in icon: emoji = '☁️' # scattered clouds
            elif '04' in icon: emoji = '🌥️' # broken clouds
            elif '09' in icon: emoji = '🌧️' # shower rain
            elif '10' in icon: emoji = '🌦️' # rain
            elif '11' in icon: emoji = '⛈️' # thunderstorm
            elif '13' in icon: emoji = '❄️' # snow
            elif '50' in icon: emoji = '🌫️' # mist
            else: emoji = '🚵'

            # Format the output message
            forecast_time = datetime.datetime.fromtimestamp(first_forecast['dt']).strftime('%I:%M %p')
            message = (
                f"**Weather forecast for {display_name} (around {forecast_time_str})** {emoji}\n"
                f"> **Forecast:** {weather_desc}\n"
                f"> **Temp:** {temp:.1f}°C (Feels like {feels_like:.1f}°C)\n"
                f"> **Wind:** {wind_speed_kmh:.1f} km/h\n"
                f"> **Rain (in last 3h):** {rain_3h} mm"
                f"Disclaimer: This is an automated forecast. Always check a reliable source before heading out!"
            )
            return message

    except aiohttp.ClientError as e:
        print(f"Error fetching weather data: {e}")
        return "🔧 The weather machine seems to be broken. Couldn't fetch the forecast."
    except (KeyError, IndexError):
        return "🤯 My weather sensors are all jumbled. Couldn't parse the forecast data."

# --- Discord Event Handlers ---

# @client.event
# async def on_member_join(member):
#     welcome_channel = client.get_channel(WELCOME_CHANNEL_ID)

#     if welcome_channel:
#         embed = discord.Embed(
#             title=f"A new rider has joined! 🚵‍♂️💨",
#             description=(
#                 f"Welcome to the crew, {member.mention}!\n\n"
#                 "To unlock the club channels and verify your membership, "
#                 "please type the command below in this channel:\n"
#                 "### ` /verify `"
#             ),
#             color=0x78be20 # MAD Green
#         )
#         embed.set_thumbnail(url=member.display_avatar.url)

#         # We DON'T send the view here. Just the prompt.
#         await welcome_channel.send(content=f"Welcome {member.mention}!", embed=embed)

@client.event
async def on_thread_create(thread: discord.Thread):
    """
    When a new thread is created in the SPINS_CHANNEL_NAME,
    get the weather for the specified location.
    """
    if thread.parent.name.lower() == SPINS_CHANNEL_NAME.lower():
        print(f"[LOG] New thread detected in '{thread.parent.name}': '{thread.name}'")
        thread_title_lower = thread.name.lower()
        found_venue_coords = None
        venue_name = None

        for name, coords in VENUES.items():
            if name in thread_title_lower:
                found_venue_coords = coords
                venue_name = name.title()
                print(f"[LOG] Found venue '{venue_name}' in thread title.")
                break  # Stop after finding the first match

        if found_venue_coords:
            spin_time = parse_spin_time_from_title(thread.name)

            lat = found_venue_coords["lat"]
            lon = found_venue_coords["lon"]

            thinking_message = await thread.send(f"🤔 Checking the weather for **{venue_name}**...")
            
            print(f"[LOG] Fetching weather for {venue_name}...")
            async with aiohttp.ClientSession() as session:
                forecast = await get_weather_forecast(session, location=venue_name, lat=lat, lon=lon, spin_time=spin_time)

            await thinking_message.edit(content=forecast)
            print(f"[LOG] Weather check complete for '{thread.name}'.")
        else:
            print("[LOG] No matching venue found in thread title.")


class OnboardingView(discord.ui.View):
    def __init__(self):
        # timeout=None is key for persistence!
        super().__init__(timeout=None)

    async def assign_basic_role(self, interaction: discord.Interaction):
        NON_MEMBER_ROLE_ID = 1098262331823231007
        role = interaction.guild.get_role(NON_MEMBER_ROLE_ID)

        if role:
            await interaction.user.add_roles(role)
        else:
            print(f"Error: Role ID {NON_MEMBER_ROLE_ID} not found!")

    @discord.ui.button(
        label="I'm a paid MAD Member",
        style=discord.ButtonStyle.green,
        custom_id="mad_paid_member"
    )
    async def paid_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        await self.assign_basic_role(interaction)

        admin_channel = interaction.client.get_channel(COMMITTEE_CHANNEL_ID)
        if admin_channel:
            await admin_channel.send(
                f"🔔 **Verification Needed:**\n"
                f"User: {interaction.user.mention} ({interaction.user.display_name})\n"
                f"Hey <@&{COMMITTE_ROLE_ID}>, please verify this member against the CI Active Members list!‍"
            )

        await interaction.followup.send(
            "Got it! I've pinged the committee. We'll verify your membership and get you sorted shortly. 🤘",
            ephemeral=True
        )

    @discord.ui.button(
        label="I'm a Guest / New Rider",
        style=discord.ButtonStyle.blurple,
        custom_id="mad_guest"
    )
    async def guest_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        await self.assign_basic_role(interaction)

        await interaction.followup.send(
            f"Welcome to MAD! 🚵‍♂️ Feel free to browse <#{1173658006559408219}> channel in the Public Section or check out <#{1018922510533791868}> and join us for a ride soon!",
            ephemeral=True
        )

@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        if interaction.command.name == 'photos':
            await interaction.response.send_message(
                "Sorry, this for members only. Please verify your membership to get access. 🤘",
                ephemeral=True
            )
        elif interaction.command.name == 'verify':
             await interaction.response.send_message(
            "❌ **Not here, rider!** The `/verify` command only works in the #welcome channel. Head over there to get your access! 🚵‍♂️",
            ephemeral=True
            )
        else:
            # Generic message for any other CheckFailure
            await interaction.response.send_message("You don't have the required permissions for this command.", ephemeral=True)

    # Case 2: The command is on cooldown (prevents spamming)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏳ Whoa there! Slow down a second. Try again in {error.retry_after:.1f}s.",
            ephemeral=True
        )

    # Case 3: The generic "Catch All" for anything else
    else:
        print(f"Unhandled Error: {error}") # This still goes to Railway logs for you
        await interaction.response.send_message(
            "🔧 **Trail Maintenance!** Something went wrong on my end. Please try again or ping a Committee member if it keeps happening.",
            ephemeral=True
        )

if __name__ == "__main__":
    client.run(TOKEN)
