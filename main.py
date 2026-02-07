import os
import discord
from discord import app_commands
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ALBUM_URL = os.getenv('ALBUM_URL')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))
COMMITTEE_CHANNEL_ID = int(os.getenv('COMMITTEE_CHANNEL_ID'))
COMMITTE_ROLE_ID = int(os.getenv('COMMITTE_ROLE_ID'))

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

    await interaction.response.send_message(embed=embed, ephemeral=False)

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
    # Case 1: The user tried /verify in the wrong channel
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ **Not here, rider!** The `/verify` command only works in the #welcome channel. Head over there to get your access! 🚵‍♂️",
            ephemeral=True
        )

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
