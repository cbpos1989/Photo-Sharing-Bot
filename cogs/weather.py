import discord
from discord.ext import commands
import asyncio
import aiohttp
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Import config from the root directory
from config import VENUES, SPINS_CHANNEL_NAME, OFFICIAL_SPINS_CHANNEL_NAME, OPENWEATHER_API_KEY

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

    time_keywords = {
        'morning': 10,
        'afternoon': 14,
        'evening': 19,
        'night': 19,
    }

    # --- Time Parsing ---
    # Catches the first time mentioned, e.g., "9:30 meet for 10:00 start" -> 9:30
    time_match = re.search(r'(\d{1,2})[:.](\d{2})', title_lower)
    if time_match:
        spin_hour = int(time_match.group(1))
        spin_minute = int(time_match.group(2))
        print(f"[LOG] Found time in title: {spin_hour:02d}:{spin_minute:02d}")
    else:
        time_found_by_keyword = False
        for keyword, hour in time_keywords.items():
            if keyword in title_lower:
                spin_hour = hour
                print(f"[LOG] '{keyword}' keyword found, defaulting to {spin_hour}:00.")
                time_found_by_keyword = True
                break # Use the first keyword found
        if not time_found_by_keyword:
            print(f"[LOG] No specific time found, defaulting to {spin_hour}:00.")

    # --- Date Parsing ---
    spin_date = None

    # Priority 1: Find a specific date like "15th"
    date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?', title_lower)
    if date_match:
        day = int(day_match.group(1))
        month = now.month
        year = now.year
        if day < now.day:
            month += 1
            if month > 12:
                month = 1
                year += 1
    try:
        spin_date = datetime(year, month, day)
        print(f"[LOG] Found day number only, calculated date: {spin_date.strftime('%Y-%m-%d')}")
    except ValueError:
        spin_date = None

    # Priority 2: If no date, find a weekday like "Tuesday"
    if not spin_date:
        weekdays = {
            'monday': 0, 'mon': 0, 'tuesday': 1, 'tue': 1, 'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thurs': 3, 'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5, 'sunday': 6, 'sun': 6
        }
        weekday_match = re.search(r'\b(' + '|'.join(weekdays.keys()) + r')\b', title_lower)
        if weekday_match:
            target_weekday = weekdays[weekday_match.group(1)]
            days_ahead = (target_weekday - now.weekday() + 7) % 7
            target_date = now.date() + timedelta(days=days_ahead)
            spin_date = datetime(target_date.year, target_date.month, target_date.day)
            print(f"[LOG] Found weekday, calculated next date: {spin_date.strftime('%Y-%m-%d')}")

    # Priority 3: If all else fails, default to the upcoming Saturday
    if not spin_date:
        days_ahead = (5 - now.weekday() + 7) % 7 # 5 = Saturday
        if days_ahead == 0: # If it's Saturday, default to next Saturday
            days_ahead = 7
        target_date = now.date() + timedelta(days=days_ahead)
        spin_date = datetime(target_date.year, target_date.month, target_date.day)
        print(f"[LOG] No date info found. Defaulting to upcoming Saturday: {spin_date.strftime('%Y-%m-%d')}")

    final_spin_time = spin_date.replace(hour=spin_hour, minute=spin_minute, second=0, microsecond=0)
    print(f"[LOG] Final parsed spin time: {final_spin_time.strftime('%Y-%m-%d %H:%M')}")
    return final_spin_time

# The Cog Class
class WeatherCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # The on_thread_create event becomes a Cog listener
    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        """
        When a new thread is created in the SPINS_CHANNEL_NAME,
        get the weather for the specified location.
        """
        if thread.parent.name.lower() == SPINS_CHANNEL_NAME.lower() or thread.parent.name.lower() == OFFICIAL_SPINS_CHANNEL_NAME.lower():
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
                    forecast = await self.get_weather_forecast(session, location=venue_name, lat=lat, lon=lon, spin_time=spin_time)

                await thinking_message.edit(content=forecast)
                print(f"[LOG] Weather check complete for '{thread.name}'.")
            else:
                print("[LOG] No matching venue found in thread title.")

    async def get_weather_forecast(self, session: aiohttp.ClientSession, location: str, lat: float, lon: float, spin_time: datetime) -> str:
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
                utc_forecast_time = datetime.fromtimestamp(spin_timestamp, tz=timezone.utc)
                weather_desc = closest_forecast['weather'][0]['description'].title()
                temp = closest_forecast['main']['temp']
                feels_like = closest_forecast['main']['feels_like']
                wind_speed_ms = closest_forecast['wind']['speed']
                wind_speed_kmh = wind_speed_ms * 3.6  # Convert m/s to km/h
                rain_3h = closest_forecast.get('rain', {}).get('3h', 0)

                irish_time = utc_forecast_time.astimezone(ZoneInfo("Europe/Dublin"))
                forecast_time_str = irish_time.strftime('%a %d, %H:%M')

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
                message = (
                    f"**Weather forecast for {display_name} (around {forecast_time_str})** {emoji}\n"
                    f"> **Forecast:** {weather_desc}\n"
                    f"> **Temp:** {temp:.1f}°C (Feels like {feels_like:.1f}°C)\n"
                    f"> **Wind:** {wind_speed_kmh:.1f} km/h\n"
                    f"> **Rain (over 3h):** {rain_3h} mm\n"
                    f"Disclaimer: This is an automated forecast. Always check a reliable source before heading out!"
                )
                return message

        except aiohttp.ClientError as e:
            print(f"Error fetching weather data: {e}")
            return "🔧 The weather machine seems to be broken. Couldn't fetch the forecast."
        except (KeyError, IndexError):
            return "🤯 My weather sensors are all jumbled. Couldn't parse the forecast data."
        
# This setup function is required for the bot to load the Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(WeatherCog(bot))