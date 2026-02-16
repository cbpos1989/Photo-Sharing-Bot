import os
from dotenv import load_dotenv

load_dotenv()

# Bot/API Keys
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Channel & Role Config
SPINS_CHANNEL_NAME = os.getenv("SPINS_CHANNEL_NAME")
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))
COMMITTEE_CHANNEL_ID = int(os.getenv('COMMITTEE_CHANNEL_ID'))
COMMITTE_ROLE_ID = int(os.getenv('COMMITTE_ROLE_ID'))
MEMBER_ROLE_ID = int(os.getenv("MEMBER_ROLE_ID", 0))
PUBLIC_EVENTS_CHANNEL_ID = 1173658006559408219
PUBLIC_GENERAL_CHANNEL_ID = 1018922510533791868

# Misc
ALBUM_URL = os.getenv('ALBUM_URL')

# Stravaduro Links
# URL for each round (index 0=Jan, 1=Feb, 2=Mar, etc.)
STRAVADURO_SUBMISSION_URLS = [
    "https://docs.google.com/forms/d/e/1FAIpQLSeIVDT6q3lqL8MTj5pi2LpJrKAQyvwYIpXrzDa91C3WOzFvow/viewform",  # Round 1
    "https://docs.google.com/forms/d/e/1FAIpQLSdncnBDFGISePF3uy2YdX4bQR2d-c8DCFTFo4rUQ6vpa-ulpg/viewform",  # Round 2
    "https://docs.google.com/forms/d/e/1FAIpQLSdl1Df_m41OC_oFbQxQfbMpm9CDyOxEPGPLVSbj1FzdGbPZ7Q/viewform"   # Round 3
]
STRAVADURO_LEADERBOARD_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQsPKkqn2z1E9t-0orqTZ6n1p_ZmesLELJYZ0gM9ZnpFvMP_TiQGLRSAqQVOPU15Uo4E5bWJkJaqGt/pubhtml?gid=2015029253&single=true"

# Weather Feature Config
VENUES = {
    "ticknock": {"lat": 53.24, "lon": -6.23},
    "djouce": {"lat": 53.15, "lon": -6.19},
    "carrick": {"lat": 52.97, "lon": -6.17},
    "ballinastoe": {"lat": 53.11, "lon": -6.24},
    "gap": {"lat": 53.23, "lon": -6.23},
    "lead mines": {"lat": 53.22, "lon": -6.16},
    "knockree": {"lat": 53.18, "lon": -6.23},
    "tona": {"lat": 53.16, "lon": -6.43},
    "hush": {"lat": 52.86, "lon": -6.13},
    "slade": {"lat": 53.25, "lon": -6.48},
    "crone": {"lat": 53.16, "lon": -6.23},
    "laragh": {"lat": 53.02, "lon": -6.34},
    "moneystown": {"lat": 53.00, "lon": -6.22},
    "trooperstown": {"lat": 53.00, "lon": -6.22},
}

# Roles to exclude from the self-assignable list
EXCLUDED_ROLES = [
    "@everyone",
    "Admin",
    "MAD Helper Bot",
    "Club Members",
    "Committee",
    "Moderator",
    "Tester Role",
    "Non Members",
    "Server Booster"
]
