import discord
from discord.ext import commands, tasks
from datetime import timedelta

# Import config from the root directory
from config import GUILD_ID, COMMITTEE_CHANNEL_ID

class ModerationCog(commands.Cog, name="Moderation"):
    """Cog for moderation tasks like auto-kicking inactive members."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cleanup_unverified_members.start()

    def cog_unload(self) -> None:
        self.cleanup_unverified_members.cancel()

    @tasks.loop(minutes=1)
    async def cleanup_unverified_members(self) -> None:
        """
        Periodically scans the server for users who have not completed verification
        and have been on the server for more than 14 days.
        """
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            print(f"Error: Guild with ID {GUILD_ID} not found for cleanup task.")
            return

        log_channel = guild.get_channel(COMMITTEE_CHANNEL_ID)
        if not log_channel:
            print(f"Error: Log channel with ID {COMMITTEE_CHANNEL_ID} not found.")
            # Silently fail if logging channel isn't found, but log to console.
            # The main task should still proceed.

        # Calculate the point in time 14 days ago from now
        kick_threshold = discord.utils.utcnow() - timedelta(days=14)
        kicked_count = 0
        
        # We build a list of members to kick first to avoid issues with modifying the member list while iterating.
        members_to_kick: list[Unknown] = []
        for member in guild.members:
            # Task Requirement: Ignore bots
            if member.bot:
                continue

            # Task Requirement: User has no roles other than @everyone
            # len(member.roles) == 1 means they only have @everyone
            if len(member.roles) > 1:
                continue

            # Task Requirement: Joined more than 14 days ago
            if member.joined_at and member.joined_at < kick_threshold:
                members_to_kick.append(member)

        if not members_to_kick:
            print("Auto-cleanup run: No unverified members older than 14 days found.")
            return

        for member in members_to_kick:
            try:
                # await member.kick(reason="Automatic cleanup: Unverified for > 14 days.")
                kicked_count += 1
                # Optional: Log each kick to the console for debugging
                print(f"Kicked {member} (ID: {member.id}). Reason: Unverified for > 14 days.")
            except discord.Forbidden:
                print(f"Failed to kick {member} (ID: {member.id}). Reason: Missing Permissions.")
            except discord.HTTPException as e:
                print(f"Failed to kick {member} (ID: {member.id}) due to an HTTP error: {e}")

        # Task Requirement: Send a summary message to the admin/committee channel
        if kicked_count > 0 and log_channel:
            summary_embed = discord.Embed(
                title="🧹 Automatic Cleanup Complete",
                description=f"Kicked **{kicked_count}** unverified members who were in the server for over 14 days.",
                color=discord.Color.orange()
            )
            await log_channel.send(embed=summary_embed)
        
        print(f"Auto-cleanup finished. Kicked {kicked_count} members.")


    @cleanup_unverified_members.before_loop
    async def before_cleanup(self) -> None:
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """Sets up the ModerationCog."""
    await bot.add_cog(ModerationCog(bot))