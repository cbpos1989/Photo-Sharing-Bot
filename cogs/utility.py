import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import STRAVADURO_SUBMISSION_URLS, STRAVADURO_LEADERBOARD_URL, EXCLUDED_ROLES

# --- Role Select View ---
# A Dropdown menu to select roles
class RoleSelect(discord.ui.Select):
    def __init__(self, roles: list[discord.Role], member: discord.Member):
        options = []

        for role in roles:
            # Set the description based on whether the member already has the role
            if role in member.roles:
                description = "You have this role. Click to remove it."
            else:
                description = f"Click to add this role."

            options.append(discord.SelectOption(
                label=role.name,
                description=description,
                value=str(role.id)
            ))
        
        super().__init__(
            placeholder="Choose a role to add or remove...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # Defer the response to prevent timeout
        await interaction.response.defer(ephemeral=True)

        # Get the selected role from the guild
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)
        member = interaction.user

        if role is None:
            await interaction.followup.send("An error occurred: Role not found.", ephemeral=True)
            return

        # Toggle the role for the user
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.followup.send(f"🚫 The **{role.name}** role has been removed.", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.followup.send(f"✅ You have been assigned the **{role.name}** role.", ephemeral=True)

# A View to hold the RoleSelect dropdown
class RoleSelectView(discord.ui.View):
    def __init__(self, roles: list[discord.Role], member: discord.Member):
        super().__init__()
        self.add_item(RoleSelect(roles, member))

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

    @app_commands.command(
        name="roles",
        description="Choose your own roles to get notified for rides you're interested in."
    )
    async def roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        excluded_roles_normalized = {name.lower().strip() for name in EXCLUDED_ROLES}

        # Filter out roles that are managed by integrations (bots), are in the excluded list, or have no name.
        assignable_roles = [
            role for role in interaction.guild.roles
            if (not role.is_integration() and
                not role.is_bot_managed() and
                role.name.lower().strip() not in excluded_roles_normalized)
        ]

        if not assignable_roles:
            await interaction.followup.send("There are no self-assignable roles available right now.", ephemeral=True)
            return

        # Sort roles alphabetically
        assignable_roles.sort(key=lambda r: r.name)

        member = interaction.user

        # Create an embed to list the roles
        embed = discord.Embed(
            title="Self-Assignable Roles",
            description="Select a role from the dropdown menu below to add or remove it.\nThis controls what ride notifications you receive.",
            color=discord.Color.blurple()
        )

        # The view will contain the dropdown menu
        view = RoleSelectView(assignable_roles, member)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

# This setup function is required for the bot to load the Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))