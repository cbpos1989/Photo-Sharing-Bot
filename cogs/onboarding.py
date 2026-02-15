import discord
from discord import app_commands
from discord.ext import commands

# Import config from the root directory
from config import WELCOME_CHANNEL_ID, COMMITTEE_CHANNEL_ID, COMMITTE_ROLE_ID

def is_welcome_channel(interaction: discord.Interaction) -> bool:
    return interaction.channel_id == WELCOME_CHANNEL_ID

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

        admin_channel = interaction.guild.get_channel(COMMITTEE_CHANNEL_ID)
        if admin_channel:
            await admin_channel.send(
                f"🔔 **Verification Needed:**\n"
                f"User: {interaction.user.mention} ({interaction.user.display_name})\n"
                f"Hey <@&{COMMITTE_ROLE_ID}>, please verify this member against the CI Active Members list!‍"
            )
        else:
             # This will help debug if the ID is wrong or the bot lacks permissions
            print(f"[ERROR] Could not find or access COMMITTEE_CHANNEL_ID: {COMMITTEE_CHANNEL_ID}")

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

# The Cog Class
class OnboardingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
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
    async def verify(self, interaction: discord.Interaction):
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
async def setup(bot: commands.Bot):
    await bot.add_cog(OnboardingCog(bot))