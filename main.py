import discord
from discord.ext import commands
import os
import asyncio
import logging
from datetime import datetime
import json

# Import command modules
from bot.commands.moderation import ModerationCog
from bot.commands.movies import MoviesCog
from bot.commands.anime import AnimeCog
from bot.commands.user_management import UserManagementCog
from bot.utils.database import Database
from keep_alive import keep_alive

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True  # Required for auto-moderation
intents.members = True  # Required for welcome system
intents.guilds = True
intents.voice_states = False  # Voice functionality removed

class ModeratorBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='A comprehensive Discord bot with moderation, movie, and anime features'
        )
        self.db = Database()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Add cogs
        await self.add_cog(ModerationCog(self))
        await self.add_cog(MoviesCog(self))
        await self.add_cog(AnimeCog(self))
        await self.add_cog(UserManagementCog(self))
        
        # Import and add new cogs
        from bot.commands.stats import StatsCog
        from bot.commands.fun import FunCog
        from bot.commands.welcome import WelcomeCog
        from bot.commands.streaming import StreamingCog
        from bot.commands.games import EnhancedStatsCog
        from bot.commands.advanced_games import AdvancedGamesCog
        from bot.commands.profile_badges import ProfileBadgesCog
        from bot.commands.scheduled_messages import ScheduledMessagesCog
        from bot.commands.roblox_integration import RobloxIntegrationCog
        from bot.commands.gaming_platforms import GamingPlatformsCog
        from bot.commands.lookup import LookupCog
        from bot.commands.animated_commands import AnimatedCommandsCog
        from bot.commands.engagement_analytics import EngagementAnalyticsCog
        await self.add_cog(StatsCog(self))
        await self.add_cog(FunCog(self))
        await self.add_cog(WelcomeCog(self))
        await self.add_cog(StreamingCog(self))
        await self.add_cog(EnhancedStatsCog(self))
        await self.add_cog(AdvancedGamesCog(self))
        await self.add_cog(ProfileBadgesCog(self))
        await self.add_cog(ScheduledMessagesCog(self))
        await self.add_cog(RobloxIntegrationCog(self))
        await self.add_cog(GamingPlatformsCog(self))
        await self.add_cog(LookupCog(self))
        await self.add_cog(AnimatedCommandsCog(self))
        await self.add_cog(EngagementAnalyticsCog(self))
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot has finished logging in"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Initialize animated status system
        try:
            from bot.utils.animated_status import setup_animated_status
            self.status_manager = await setup_animated_status(self)
            logger.info("Animated status system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize animated status system: {e}")
            self.status_manager = None
        
        # Load auto-moderation settings for all guilds
        for guild in self.guilds:
            settings = self.db.get_automod_settings(guild.id)
            if settings:
                # Get moderation cog and update its auto-mod settings
                mod_cog = self.get_cog('ModerationCog')
                if mod_cog:
                    mod_cog.auto_mod.update_settings(settings)
    
    async def on_message(self, message):
        """Handle incoming messages for auto-moderation and stats tracking"""
        # Skip if message is from bot or in DMs
        if message.author.bot or not message.guild:
            return
        
        # Track message statistics
        stats_cog = self.get_cog('StatsCog')
        if stats_cog:
            try:
                stats_cog.stats_tracker.track_message(
                    message.author.id, 
                    message.guild.id, 
                    message.channel.id, 
                    len(message.content)
                )
            except Exception as e:
                logger.error(f"Error tracking message stats: {e}")
        
        # Track enhanced statistics
        enhanced_stats_cog = self.get_cog('EnhancedStatsCog')
        if enhanced_stats_cog:
            try:
                await enhanced_stats_cog.track_message(message)
            except Exception as e:
                logger.error(f"Error tracking enhanced stats: {e}")
        
        # Track badge progress
        badges_cog = self.get_cog('ProfileBadgesCog')
        if badges_cog:
            try:
                await badges_cog.track_message_activity(message)
            except Exception as e:
                logger.error(f"Error tracking badge progress: {e}")
        
        # Track engagement analytics
        engagement_cog = self.get_cog('EngagementAnalyticsCog')
        if engagement_cog:
            try:
                await engagement_cog.engagement_tracker.track_message(message)
                await engagement_cog.conversation_mapper.track_message_flow(message)
            except Exception as e:
                logger.error(f"Error tracking engagement: {e}")
        
        # Get moderation cog for auto-moderation
        mod_cog = self.get_cog('ModerationCog')
        if mod_cog and mod_cog.auto_mod:
            try:
                # Check message against auto-moderation rules
                await mod_cog.auto_mod.check_message(message)
            except Exception as e:
                logger.error(f"Error in auto-moderation: {e}")
        
        # Get fun cog for quote collection
        fun_cog = self.get_cog('FunCog')
        if fun_cog:
            try:
                await fun_cog.collect_quote(message)
            except Exception as e:
                logger.error(f"Error collecting quote: {e}")
        
        # Process commands (for prefix commands if any)
        await self.process_commands(message)
    
    async def on_app_command_completion(self, interaction: discord.Interaction, command):
        """Track command usage after successful completion"""
        if interaction.guild:
            stats_cog = self.get_cog('StatsCog')
            if stats_cog:
                try:
                    stats_cog.stats_tracker.track_command_usage(
                        interaction.user.id,
                        interaction.guild.id,
                        command.name
                    )
                except Exception as e:
                    logger.error(f"Error tracking command usage: {e}")
            
            # Track enhanced command statistics
            enhanced_stats_cog = self.get_cog('EnhancedStatsCog')
            if enhanced_stats_cog:
                try:
                    await enhanced_stats_cog.track_command(interaction)
                except Exception as e:
                    logger.error(f"Error tracking enhanced command stats: {e}")
            
            # Track badge progress for commands
            badges_cog = self.get_cog('ProfileBadgesCog')
            if badges_cog:
                try:
                    await badges_cog.track_command_usage(interaction, command.name)
                except Exception as e:
                    logger.error(f"Error tracking badge command progress: {e}")
            
            # Add Jarvis response system
            try:
                from bot.utils.jarvis_responses import JarvisResponses
                jarvis = JarvisResponses()
                
                # Determine command category
                category = None
                if command.name in ['kick', 'ban', 'mute', 'warn', 'clear', 'automod_toggle', 'automod_configure']:
                    category = "moderation"
                elif command.name in ['movie_info', 'anime_search', 'anime_recommend', 'popular_movies', 'upcoming_movies']:
                    category = "entertainment"
                elif command.name in ['stats', 'leaderboard', 'server_stats', 'activity_chart']:
                    category = "stats"
                elif command.name in ['quote', 'meme', 'coinflip', 'dice', 'slots', 'balance']:
                    category = "fun"
                elif command.name in ['play', 'join', 'leave', 'pause', 'resume', 'skip', 'stop', 'queue', 'volume', 'loop', 'shuffle', 'now_playing']:
                    category = "music"
                
                # Get random response
                response = jarvis.get_random_response(category)
                if response:
                    embed = jarvis.create_jarvis_embed(response)
                    # Send as followup message to avoid interfering with the command response
                    await interaction.followup.send(embed=embed, ephemeral=False)
                    
            except Exception as e:
                logger.error(f"Error with Jarvis response: {e}")
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        else:
            logger.error(f"Unhandled error: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")

# Create bot instance
bot = ModeratorBot()

# Add a basic help command
@bot.tree.command(name="help", description="Show available commands")
async def help_command(interaction: discord.Interaction):
    """Display help information for all commands"""
    embed = discord.Embed(
        title="🤖 Bot Commands",
        description="Here are all available commands:",
        color=discord.Color.blue()
    )
    
    # Moderation commands
    embed.add_field(
        name="🛡️ Moderation",
        value="`/kick` - Kick a user\n"
              "`/ban` - Ban a user\n"
              "`/unban` - Unban a user\n"
              "`/mute` - Mute a user\n"
              "`/unmute` - Unmute a user\n"
              "`/warn` - Warn a user\n"
              "`/warnings` - View user warnings\n"
              "`/clear` - Clear messages",
        inline=False
    )
    
    # Auto-moderation commands
    embed.add_field(
        name="🤖 Auto-Moderation",
        value="`/automod_toggle` - Enable/disable auto-moderation\n"
              "`/automod_settings` - View current settings\n"
              "`/automod_configure` - Configure filters\n"
              "`/automod_stats` - View statistics\n"
              "`/automod_violations` - View user violations",
        inline=False
    )
    
    # Statistics commands
    embed.add_field(
        name="📊 Statistics",
        value="`/stats` - View your server statistics\n"
              "`/leaderboard` - View server leaderboards\n"
              "`/server_stats` - View overall server statistics\n"
              "`/activity_chart` - View your activity chart",
        inline=False
    )
    
    # Fun commands
    embed.add_field(
        name="🎮 Fun & Games",
        value="`/quote` - Get a random quote from members\n"
              "`/meme` - Get memes from Reddit or Google\n"
              "`/balance` - Check your gambling balance\n"
              "`/daily` - Claim daily coins\n"
              "`/coinflip` - Flip a coin and bet\n"
              "`/dice` - Roll dice and bet\n"
              "`/slots` - Play slot machine",
        inline=False
    )
    
    # Status commands
    embed.add_field(
        name="🟢 Status & Info",
        value="`/set_status` - Set your server status\n"
              "`/status` - Check someone's status\n"
              "`/server_statuses` - View all server statuses\n"
              "`/timeout_info` - Check timeout information",
        inline=False
    )
    
    # Movie commands
    embed.add_field(
        name="🎬 Movies",
        value="`/movie_info` - Get movie information\n"
              "`/upcoming_movies` - Show upcoming movies\n"
              "`/movie_tickets` - Find movie ticket prices\n"
              "`/popular_movies` - Show popular movies",
        inline=False
    )
    
    # Anime commands
    embed.add_field(
        name="🎌 Anime & Streaming",
        value="`/anime_recommend` - Get anime recommendations\n"
              "`/anime_search` - Search for anime\n"
              "`/anime_popular` - Show popular anime\n"
              "`/anime_streaming` - Find anime by platform\n"
              "`/anime_platforms` - View all platforms\n"
              "`/anime_where_to_watch` - Find where to watch anime",
        inline=False
    )
    
    # User management commands
    embed.add_field(
        name="👥 User Management",
        value="`/set_favorite_character` - Set your favorite character\n"
              "`/get_favorite_character` - Get someone's favorite character\n"
              "`/nickname` - Change user's nickname\n"
              "`/user_info` - Get user information\n"
              "`/avatar` - Get user's avatar",
        inline=False
    )
    
    # Music commands
    embed.add_field(
        name="🎵 Music Player",
        value="`/join` - Join voice channel\n"
              "`/leave` - Leave voice channel\n"
              "`/play` - Play from YouTube/Spotify/Apple Music\n"
              "`/pause` - Pause current song\n"
              "`/resume` - Resume current song\n"
              "`/stop` - Stop and clear queue\n"
              "`/skip` - Skip current song\n"
              "`/queue` - Show music queue\n"
              "`/volume` - Set volume (0-100)\n"
              "`/loop` - Toggle loop mode\n"
              "`/shuffle` - Shuffle queue\n"
              "`/now_playing` - Show current song",
        inline=False
    )
    
    # Music recommendations
    embed.add_field(
        name="🎧 Music Recommendations",
        value="`/music_preferences` - Set your music preferences\n"
              "`/music_recommend` - Get personalized recommendations\n"
              "`/music_mood` - Get mood-based music\n"
              "`/music_discover` - Discover similar artists/songs\n"
              "`/music_profile` - View your music profile",
        inline=False
    )
    
    # Profile & Badges
    embed.add_field(
        name="🏆 Profile & Badges",
        value="`/profile` - View your profile with badges and stats\n"
              "`/badges` - Browse all available badges\n"
              "`/badge_leaderboard` - View server badge rankings\n"
              "`/award_badge` - Award badges (Admin only)",
        inline=False
    )
    
    # Scheduled Messages
    embed.add_field(
        name="📅 Scheduled Messages",
        value="`/schedule_message` - Schedule a message to send later\n"
              "`/list_scheduled` - View all scheduled messages\n"
              "`/setup_farewell` - Setup farewell messages\n"
              "`/test_farewell` - Test farewell system",
        inline=False
    )
    
    # Roblox Integration
    embed.add_field(
        name="🎮 Roblox Integration",
        value="`/roblox_link` - Link your Roblox account\n"
              "`/roblox_profile` - View Roblox profile\n"
              "`/roblox_search` - Search for Roblox users\n"
              "`/roblox_group` - Get group information\n"
              "`/roblox_status` - Check who's playing Roblox",
        inline=False
    )
    
    # Gaming Platforms
    embed.add_field(
        name="🎯 Gaming Platforms",
        value="`/link_gaming_account` - Link Xbox/PS/Steam/etc\n"
              "`/gaming_profile` - View linked gaming accounts\n"
              "`/destiny_stats` - View Destiny 2 stats\n"
              "`/xbox_profile` - View Xbox Live profile\n"
              "`/gaming_leaderboard` - Server gaming leaderboard",
        inline=False
    )
    
    # Welcome system commands
    embed.add_field(
        name="🎉 Welcome System",
        value="`/welcome_test` - Test the welcome system\n"
              "`/welcome_role_info` - View welcome role information",
        inline=False
    )
    
    # Streaming commands
    embed.add_field(
        name="🎯 Streaming Sites",
        value="`/streaming_sites` - Get best streaming sites\n"
              "`/random_streaming` - Random streaming recommendation",
        inline=False
    )
    
    # Enhanced Stats commands
    embed.add_field(
        name="📈 Enhanced Analytics",
        value="`/detailed_stats` - Comprehensive user statistics\n"
              "`/server_analytics` - Server-wide analytics\n"
              "`/compare_stats` - Compare stats with another user",
        inline=False
    )
    
    # RPG Game commands
    embed.add_field(
        name="🎮 RPG Adventures",
        value="`/rpg_start` - Begin your RPG adventure\n"
              "`/rpg_profile` - View character profile\n"
              "`/rpg_quest` - Go on quests and fight monsters\n"
              "`/rpg_shop` - Buy weapons and armor\n"
              "`/rpg_battle` - Challenge players to PvP\n"
              "`/rpg_leaderboard` - View top players",
        inline=False
    )
    
    # Special commands
    embed.add_field(
        name="🤖 Special",
        value="`/jarvis` - Get a random Jarvis response",
        inline=False
    )
    
    embed.set_footer(text="Use /command_name for more details on each command")
    await interaction.response.send_message(embed=embed)

# Add Jarvis command
@bot.tree.command(name="jarvis", description="Get a random Jarvis response")
async def jarvis_command(interaction: discord.Interaction):
    """Get a random Jarvis response"""
    try:
        from bot.utils.jarvis_responses import JarvisResponses
        jarvis = JarvisResponses()
        response = jarvis.get_random_response()
        
        if response:
            embed = jarvis.create_jarvis_embed(response)
            await interaction.response.send_message(embed=embed)
        else:
            # Fallback response
            embed = jarvis.create_jarvis_embed("At your service, sir.")
            await interaction.response.send_message(embed=embed)
            
    except Exception as e:
        logger.error(f"Error in Jarvis command: {e}")
        await interaction.response.send_message("❌ Error accessing Jarvis responses", ephemeral=True)

# Run the bot
if __name__ == "__main__":
    # Start keep-alive system first
    keep_alive()
    logger.info("Keep-alive system activated - Bot will stay active 24/7")
    
    # Get token from environment variable
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        logger.error("Discord token not found. Please set the DISCORD_TOKEN environment variable.")
        exit(1)
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token provided.")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
