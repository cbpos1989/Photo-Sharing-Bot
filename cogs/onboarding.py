import discord
from discord import app_commands
from discord.ext import commands

# Import config from the root directory
from config import (
    WELCOME_CHANNEL_ID,
    COMMITTEE_CHANNEL_ID,
    COMMITTE_ROLE_ID,
    RULES_CHANNEL_ID,
    PUBLIC_EVENTS_CHANNEL_ID,
    PUBLIC_GENERAL_CHANNEL_ID
)

def is_welcome_channel(interaction: discord.Interaction) -> bool:
    return interaction.channel_id == WELCOME_CHANNEL_ID

class MemberVerificationModal(discord.ui.Modal, title="Paid Member Verification"):
    """A modal to capture Full Name and Email for verification."""
    full_name = discord.ui.TextInput(
        label="Full Name",
        placeholder="e.g., John Smith",
        required=True,
        style=discord.TextStyle.short,
        max_length=50,
    )

    email = discord.ui.TextInput(
        label="Email Address",
        placeholder="Used for committee verification only",
        required=True,
        style=discord.TextStyle.short,
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle the modal submission logic."""
        # 1. Log the captured data to the private committee channel.
        admin_channel = interaction.guild.get_channel(COMMITTEE_CHANNEL_ID)
        if admin_channel:
            await admin_channel.send(
                f"🔔 **New Paid Member Verification:**\n"
                f"**Discord User:** {interaction.user.mention} ({interaction.user.display_name})\n"
                f"**Full Name:** `{self.full_name.value}`\n"
                f"**Email:** `{self.email.value}`\n\n"
                f"Hey <@&{COMMITTE_ROLE_ID}>, please verify this member against the CI Active Members list and assign the correct role.‍"
            )
        else:
            print(f"[ERROR] Could not find or access COMMITTEE_CHANNEL_ID: {COMMITTEE_CHANNEL_ID}")

        # 2. Send the final ephemeral instructions to the user.
        await OnboardingView._send_rules_briefing(interaction, is_modal_response=True)

class OnboardingView(discord.ui.View):
    def __init__(self) -> None:
        # timeout=None is key for persistence!
        super().__init__(timeout=None)

    async def _send_rules_briefing(interaction: discord.Interaction, is_modal_response: bool = False) -> None:
        """A helper to send a consistent ephemeral message to the user."""
        print(f"_send_rules_briefing( {is_modal_response} )")
        rules_channel = interaction.guild.get_channel(RULES_CHANNEL_ID)
        rules_mention = rules_channel.mention if rules_channel else "`#rules`"

        if is_modal_response:
            message_content: str = (
                f"Got it! I've pinged the committee. We'll verify your membership and get you sorted shortly. 🤘\n\n"
                f"**Just one last thing...** \n\n"
                f"1. **Set Your Nickname:** Please change your server nickname to your **Full Name**. This is mandatory for all members to help us identify you on rides. "
                f"*(Right-click your profile > Edit Server Profile)* \n\n"
                f"2. **Read the Rules:** Please read the server rules in the {rules_mention} channel.\n\n"
                f"Use the `/help` command to see what the bot can do!"
            ) 
        else: 
            message_content: str = (
                f"Welcome to MAD! 🚵‍♂️ Feel free to browse the <#{PUBLIC_EVENTS_CHANNEL_ID}> channel "
                f"in the Public Section or check out <#{PUBLIC_GENERAL_CHANNEL_ID}> and join us for a ride soon!\n"
                f"Just one last thing...**\n\n"
                f"**Read the Rules:** Please read the server rules in the {rules_mention} channel.\n\n"
                f"Use the `/help` command to see what else the bot can do!"
            )

        # A modal submission requires a new response. A button click uses a followup.
        if is_modal_response:
            await interaction.response.send_message(message_content, ephemeral=True)
        else:
            print(f"sending followup")
            await interaction.followup.send(message_content, ephemeral=True)

    async def assign_basic_role(self, interaction: discord.Interaction) -> None:
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
    async def paid_member(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.assign_basic_role(interaction)

        await interaction.response.send_modal(MemberVerificationModal())


    @discord.ui.button(
        label="I'm a Guest / New Rider",
        style=discord.ButtonStyle.blurple,
        custom_id="mad_guest"
    )
    async def guest_member(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)

        await self.assign_basic_role(interaction)

        await self._send_rules_briefing(interaction)

# The Cog Class
class OnboardingCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.add_view(OnboardingView())

    @commands.Cog.listener()
    async def on_member_join(self, member) -> None:
        # Ignore bots joining
        if member.bot:
            return

        # Fetch the channel from the config ID
        welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

        # If the bot is on a server without that channel, do nothing.
        if not welcome_channel:
            print(f"[ERROR] on_member_join: Could not find channel with ID {WELCOME_CHANNEL_ID}")
            return

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

    @app_commands.command(name="verify", description="Start your MAD MTB onboarding")
    @app_commands.check(is_welcome_channel)
    async def verify(self, interaction: discord.Interaction) -> None:
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

# This setup function is required for the bot to load the Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OnboardingCog(bot))