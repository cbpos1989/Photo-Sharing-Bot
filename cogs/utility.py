import discord
from discord.ext import commands

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

# This setup function is required for the bot to load the Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))