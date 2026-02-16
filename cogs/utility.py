import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import STRAVADURO_SUBMISSION_URLS, STRAVADURO_LEADERBOARD_URL

# The Cog Class
class UtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="spin-template", description="Generate a template for posting a new club spin")
    async def spin_template(self, interaction: discord.Interaction):
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

    @app_commands.command(name="stravaduro", description="Get links for Stravaduro submissions and leaderboards.")
    async def stravaduro(self, interaction: discord.Interaction):
        current_month = datetime.now().month
        submission_text = ""
        # The array is 0-indexed, so January (month 1) is index 0.
        # This logic checks if the current month is within the competition's duration.
        if 1 <= current_month <= len(STRAVADURO_SUBMISSION_URLS):
            submission_url = STRAVADURO_SUBMISSION_URLS[current_month - 1]
            submission_text = f"[Click here for Round {current_month} submission form]({submission_url})"
        else:
            submission_text = "Submissions are currently closed. Check back next year when the next edition of the stravaduro starts!"

        embed = discord.Embed(
            title="🏆 Stravaduro Info & Links",
            description="Everything you need for the club's Stravaduro series.",
            color=0xfc4c02  # A Strava-like orange color
        )
        embed.add_field(
            name="🔗 Submit Your Time",
            value=submission_text,
            inline=False
        )
        embed.add_field(
            name="📊 View the Leaderboard",
            value=f"[Click here to see the current standings]({STRAVADURO_LEADERBOARD_URL})",
            inline=False
        )
        embed.set_footer(text="Good luck and may the fastest rider win! 🤘")

        await interaction.response.send_message(embed=embed, ephemeral=True)

# This setup function is required for the bot to load the Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))