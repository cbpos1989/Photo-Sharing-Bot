import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.members = True
intents.message_content = True # Important for some commands

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

async def load_cogs():
    """Finds and loads all cogs in the 'cogs' directory."""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"Successfully loaded cog: {filename}")
            except Exception as e:
                print(f"Failed to load cog {filename}: {e}")


@bot.tree.error
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

async def main():
    if not DISCORD_TOKEN:
        raise ValueError("ERROR: DISCORD_TOKEN is missing from environment variables!")
        
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
