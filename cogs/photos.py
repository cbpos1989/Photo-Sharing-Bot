import discord
from discord.ext import commands

# Import config from the root directory
from config import MEMBER_ROLE_ID, ALBUM_URL

def is_member():
    def predicate(interaction: discord.Interaction) -> bool:
        if MEMBER_ROLE_ID == 0:
            return True  # No role restriction if ID is not set

        member_role = discord.utils.get(interaction.guild.roles, id=MEMBER_ROLE_ID)
        
        if member_role is None:
            # This is a server-side check, so we just log it.
            print(f"Warning: Role with ID {MEMBER_ROLE_ID} not found in guild {interaction.guild.name}.")
            return False

        return member_role in interaction.user.roles
    return app_commands.check(predicate)

# The Cog Class
class PhotosCog(commands.Cog):
    if not ALBUM_URL:
        print("WARNING: ALBUM_URL is missing. /photos command might fail.")
    if not MEMBER_ROLE_ID:
        print("WARNING: MEMBER_ROLE_ID is missing from environment variables! The /photos command will not be restricted to members.")
        MEMBER_ROLE_ID = 0  # Set to 0 to indicate no restriction
    else:
        MEMBER_ROLE_ID = int(MEMBER_ROLE_ID)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="photos", description="Get the link to the MAD MTB Google Photos album")
    @is_member()
    async def photos(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        embed = discord.Embed(
            title="📸 MAD MTB Photo Vault",
            description="Don't let those trail gems sit on your phone! Upload your photos and videos to our shared album.",
            color=0x78be20  # MAD Green
        )
        embed.add_field(name="How to contribute", value=f"Click [HERE]({ALBUM_URL}) to view or upload.")
        embed.set_footer(text="Club culture is built on shared shredding!")

        await interaction.followup.send(embed=embed)

# This setup function is required for the bot to load the Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(PhotosCog(bot))