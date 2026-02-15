# MAD Helper Bot

A custom Discord bot built with Python and `discord.py` to automate tasks and provide helpful utilities for the MAD MTB (Mountain Biking) club's Discord server.

## Features

This bot is built on a modular, cog-based architecture to easily manage and add new features.

### 🚵‍♂️ Automatic Weather Forecasts

- **On-Demand Weather:** When a new thread is created in the `#spins` channel, the bot automatically detects the venue name (e.g., "Ticknock", "Djouce") from the thread title.
- **Intelligent Time Parsing:** It parses the title for times (e.g., "19:30"), dates ("15th Feb"), and weekdays ("Tuesday") to determine the time of the spin.
- **Accurate Forecasts:** It fetches a 5-day/3-hour forecast from the OpenWeatherMap API and posts the weather conditions closest to the planned spin time, ensuring riders know what to expect.

### 👋 New Member Onboarding

- **Welcome Message:** Automatically greets new members when they join the server and directs them to the `#welcome` channel to start the verification process.
- **/verify Command:** A simple, interactive command for new users to self-identify as either a paid club member or a guest.
  - **Paid Members:** The bot notifies the club committee via a private channel to verify the user's membership status against the official list.
  - **Guests/New Riders:** The bot grants a basic role and directs them to public channels to join social spins.

### 🛠️ Utility Commands

- **/spin-template:** Generates a pre-formatted template for posting a new club spin. This ensures all necessary details like time, location, distance, and difficulty are included, promoting consistency.
- **/photos:** Provides a quick and easy link to the club's shared photo album, encouraging members to upload and share their ride photos and videos.

## Project Structure

The bot uses a clean, cog-based structure:

- **`main.py`**: The main entry point. Initializes the bot, loads cogs, and handles global events like error handling.
- **`config.py`**: A centralized configuration file for storing static data like channel IDs, role IDs, and API keys.
- **`.env`**: Used for storing sensitive credentials and environment-specific variables.
- **`cogs/`**: A directory containing all the bot's features, separated into logical modules (Cogs):
  - `weather.py`: Handles weather forecasting.
  - `onboarding.py`: Manages the new member verification flow.
  - `utility.py`: Contains simple helper commands.
  - `photos.py`: Manages the photo album command.

## Setup and Installation

Follow these steps to run the bot locally or prepare it for deployment.

### 1. Clone the Repository

git clone <your-repository-url>
cd <your-repository-directory>

### 2. Install Dependencies

**Create a virtual environment**
python -m venv venv

**Activate it (Windows)**
.\venv\Scripts\activate
**Activate it (macOS/Linux)**
source venv/bin/activate

**Install required packages**
pip install -r requirements.txt

### 3. Configure Environment Variables

Create a file named .env in the root directory and add the following variables. These are your secret keys and should not be committed to version control.

DISCORD_TOKEN="your_discord_bot_token_here"
OPENWEATHER_API_KEY="your_openweathermap_api_key_here"
MEMBER_ROLE_ID="id_of_your_verified_member_role"
COMMITTE_ROLE_ID="id_of_your_committee_role_to_be_pinged"

### 4. Configure Bot Settings

Open config.py and update the channel IDs and other settings to match your Discord server's setup.

- SPINS_CHANNEL_NAME: The name of the channel where spin threads are created.
- WELCOME_CHANNEL_ID: The ID of the channel for new members.
- COMMITTEE_CHANNEL_ID: The ID of the private channel for verification requests.
- PUBLIC_EVENTS_CHANNEL_ID & PUBLIC_GENERAL_CHANNEL_ID: IDs for public channels.
- ALBUM_URL: The URL for the /photos command.
- VENUES: The dictionary of venue names and their GPS coordinates.

### 5. Deployment

The bot is configured for easy deployment on platforms like Railway or Heroku. Ensure all environment variables from your .env file are correctly set in the deployment environment's secrets management.