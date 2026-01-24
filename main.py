import os
import discord
from discord import app_commands
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class MadBot(discord.Client):
    def __init__(self):
        # Default intents are fine for a basic slash command bot
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This syncs the slash commands to the Discord API
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

client = MadBot()

@client.tree.command(name="photos", description="Get the link to the MAD MTB Google Photos album")
async def photos(interaction: discord.Interaction):
    album_url = os.getenv('ALBUM_URL')

    embed = discord.Embed(
        title="📸 MAD MTB Photo Vault",
        description="Don't let those trail gems sit on your phone! Upload your photos and videos to our shared album.",
        color=0x78be20  # MAD Green
    )
    embed.add_field(name="How to contribute", value=f"Click [HERE]({album_url}) to view or upload.")
    embed.set_footer(text="Club culture is built on shared shredding!")

    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    client.run(TOKEN)
