import os
import discord
from discord import app_commands
from dotenv import load_dotenv
import re
import requests
import datetime

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

@client.tree.command(name="photos", description="Get the link to the MAD MTB Google Photos album")
@is_member()
async def photos(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)

    embed = discord.Embed(
        title="📸 MAD MTB Photo Vault",
        description="Don't let those trail gems sit on your phone! Upload your photos and videos to our shared album.",
        color=0x78be20  # MAD Green
    )
    embed.add_field(name="How to contribute", value=f"Click [HERE]({ALBUM_URL}) to view or upload.")
    embed.set_footer(text="Club culture is built on shared shredding!")

    await interaction.followup.send(embed=embed)

@client.tree.command(name="spin-template", description="Generate a template for posting a new club spin")
async def spin_template(interaction: discord.Interaction):
    # This template is pulled directly from your MAD Committee guidelines
    template = (
        "**MAD MTB Spin Details**\n"
        "```\n"
        "**Date & Time:** \n"
        "**Meeting Point:** \n"
        "**Route Distance (km):** \n"
        "**Elevation:** (e.g., Steep, Medium, Flat etc.) \n"
        "**Technicality:** (e.g., Beginner/Intermediate/Difficult)\n"
        "**Pace:** (e.g., Social/Leisurely/Fast-paced)\n"
        "**Duration:** (Approx hours including breaks)\n"
        "**Required Equipment:** (e.g., Lights for night rides, extra water)\n"
        "```\n"
        "*Tip: Copy the text above and paste it into your new thread in the #spins channel!*"
    )

    await interaction.response.send_message(template, ephemeral=True)

def is_welcome_channel(interaction: discord.Interaction) -> bool:
    return interaction.channel_id == WELCOME_CHANNEL_ID

@client.tree.command(name="verify", description="Start your MAD MTB onboarding")
@app_commands.check(is_welcome_channel)
async def verify(interaction: discord.Interaction):
    # This simulates the message that would be sent to a new joiner
    embed = discord.Embed(
        title=f"Welcome to MAD MTB!, {interaction.user.display_name}! 🚵‍♂️",
        description=(
            "To get you out on the trails with the right access, please select your status:\n\n"
            "**Paid Member:** You've paid your club fees and need full access.\n"
            "**Guest / New Rider:** You're here for social spins or just checking us out."
        ),
        color=0x78be20 # MAD Green
    )
    embed.set_footer(text="If you're stuck, just ask a member of the Committee! 🤘")

    await interaction.response.send_message(
        embed=embed,
        view=OnboardingView(),
        ephemeral=True
    )

def get_weather_forecast(location: str):
    """Fetches a 3-hour forecast for a given location using OpenWeatherMap API."""
    if not OPENWEATHER_API_KEY:
        print("Warning: OPENWEATHER_API_KEY not configured.")
        return "Looks like I left my weather-watching glasses at home! (The OpenWeather API key isn't set up)."

    # Geocoding: Convert location name to coordinates
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={OPENWEATHER_API_KEY}"
    try:
        geo_res = requests.get(geo_url)
        geo_res.raise_for_status()
        geo_data = geo_res.json()
        if not geo_data:
            return f"🤔 Couldn't find a place called '{location}'. Is that on this planet?"

        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        found_location = geo_data[0]['name']

        # Weather Forecast: Get forecast using coordinates
        weather_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        weather_res = requests.get(weather_url)
        weather_res.raise_for_status()
        forecast_data = weather_res.json()

        # Let's use the first forecast interval (usually +3 hours from now)
        first_forecast = forecast_data['list'][0]
        weather = first_forecast['weather'][0]
        main = first_forecast['main']
        wind = first_forecast['wind']
        
        # Get a weather emoji
        icon = weather['icon']
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
            f"**Weather forecast for {found_location} (around {forecast_time})** {emoji}\n"
            f"> **Condition:** {weather['description'].title()}\n"
            f"> **Temp:** {main['temp']:.1f}°C (Feels like: {main['feels_like']:.1f}°C)\n"
            f"> **Wind:** {wind['speed'] * 3.6:.1f} km/h\n"
            f"_{Disclaimer: This is an automated forecast. Always check a reliable source before heading out!_}"
        )
        return message

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return "🔧 The weather machine seems to be broken. Couldn't fetch the forecast."
    except (KeyError, IndexError):
        return "🤯 My weather sensors are all jumbled. Couldn't parse the forecast data."

# --- Discord Event Handlers ---

@client.event
async def on_member_join(member):
    welcome_channel = client.get_channel(WELCOME_CHANNEL_ID)

    if welcome_channel:
        embed = discord.Embed(
            title=f"A new rider has joined! 🚵‍♂️💨",
            description=(
                f"Welcome to the crew, {member.mention}!\n\n"
                "To unlock the club channels and verify your membership, "
                "please type the command below in this channel:\n"
                "### ` /verify `"
            ),
            color=0x78be20 # MAD Green
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # We DON'T send the view here. Just the prompt.
        await welcome_channel.send(content=f"Welcome {member.mention}!", embed=embed)

@client.event
async def on_thread_create(thread: discord.Thread):
    """
    When a new thread is created in the SPINS_CHANNEL_NAME,
    get the weather for the specified location.
    """
    if thread.parent.name.lower() == SPINS_CHANNEL_NAME.lower():
        # Fetch the first message in the thread (the one that created it)
        start_message = await thread.fetch_message(thread.id)
        content = start_message.content

        # Use regex to find the location from the "Meeting Point"
        # This looks for "Meeting Point:" and captures everything until the end of the line
        match = re.search(r"Meeting Point:\s*(.*)", content, re.IGNORECASE)

        if match:
            location = match.group(1).strip()
            if location:
                # Let the user know the bot is working on it
                thinking_message = await thread.send(f"🤔 Checking the weather for **{location}**...")
                forecast = get_weather_forecast(location)
                await thinking_message.edit(content=forecast)
            else:
                await thread.send("Looks like the 'Meeting Point' is empty. I need a location to fetch the weather!")


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
                "Sorry, this command is for members only. Please verify your membership to get access. 🤘",
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
