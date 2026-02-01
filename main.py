import os
import discord
from discord import app_commands
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ALBUM_URL = os.getenv('ALBUM_URL')

if not TOKEN:
    raise ValueError("ERROR: DISCORD_TOKEN is missing from environment variables!")
if not ALBUM_URL:
    print("WARNING: ALBUM_URL is missing. /photos command might fail.")

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

@client.tree.command(name="photos", description="Get the link to the MAD MTB Google Photos album")
async def photos(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📸 MAD MTB Photo Vault",
        description="Don't let those trail gems sit on your phone! Upload your photos and videos to our shared album.",
        color=0x78be20  # MAD Green
    )
    embed.add_field(name="How to contribute", value=f"Click [HERE]({ALBUM_URL}) to view or upload.")
    embed.set_footer(text="Club culture is built on shared shredding!")

    await interaction.response.send_message(embed=embed, ephemeral=True)

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

@client.tree.command(name="test-onboarding", description="Test the onboarding message and buttons")
async def test_onboarding(interaction: discord.Interaction):
    # This simulates the message that would be sent to a new joiner
    embed = discord.Embed(
        title=f"Welcome to MAD MTB! 🚵‍♂️",
        description=(
            "We're stoked to have you. To get you to the right trails, "
            "please select your status below:"
        ),
        color=0x78be20 # MAD Green
    )

    # We send it ephemerally so only you see the test, or normally if you want to show other admins
    await interaction.response.send_message(
        content=f"Hey {interaction.user.mention}, this is a test of the onboarding system!",
        embed=embed,
        view=OnboardingView(),
        ephemeral=True
    )

# @client.event
# async def on_member_join(member):
#     welcome_channel = client.get_channel(1018922510533791867)
#
#     embed = discord.Embed(
#         title=f"Welcome to MAD MTB, {member.display_name}! 🌲",
#         description=(
#             "We're glad to have you here. To get you to the right trails, "
#             "please select your role below:"
#         ),
#         color=0x78be20
#     )
#
#     # This attaches the buttons we created above to the welcome message
#     await welcome_channel.send(content=f"Hey {member.mention}!", embed=embed, view=OnboardingView())

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

        admin_channel = interaction.client.get_channel(1467562740238389471)

        await admin_channel.send(
            f"🔔 **Verification Needed:**\n"
            f"User: {interaction.user.mention} ({interaction.user.display_name})\n"
            # f"Hey <@&{1098261430647660624}>, please verify this member against the CI Active Members list!‍"
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

if __name__ == "__main__":
    client.run(TOKEN)
