import asyncio
import discord
from discord.ext import tasks
import random
import logging

logger = logging.getLogger(__name__)

class AnimatedStatusManager:
    def __init__(self, bot):
        self.bot = bot
        self.current_status_index = 0
        self.is_running = False
        
        # Define animated status sequences
        self.status_sequences = {
            'default': [
                {"name": "🔍 Looking up songs", "type": discord.ActivityType.watching},
                {"name": "📚 Searching books", "type": discord.ActivityType.watching},
                {"name": "📖 Finding manga", "type": discord.ActivityType.watching},
                {"name": "🎵 Music discovery", "type": discord.ActivityType.listening},
                {"name": "💬 Server activity", "type": discord.ActivityType.watching},
                {"name": "🎮 Gaming stats", "type": discord.ActivityType.watching},
                {"name": "🤖 AI assistance", "type": discord.ActivityType.playing},
                {"name": "📊 Analytics", "type": discord.ActivityType.watching},
            ],
            'search': [
                {"name": "🔍 Searching...", "type": discord.ActivityType.playing},
                {"name": "📡 Fetching data...", "type": discord.ActivityType.playing},
                {"name": "⚡ Processing...", "type": discord.ActivityType.playing},
                {"name": "✅ Results ready!", "type": discord.ActivityType.watching},
            ],
            'loading': [
                {"name": "⏳ Loading", "type": discord.ActivityType.playing},
                {"name": "⏳ Loading.", "type": discord.ActivityType.playing},
                {"name": "⏳ Loading..", "type": discord.ActivityType.playing},
                {"name": "⏳ Loading...", "type": discord.ActivityType.playing},
            ],
            'music': [
                {"name": "🎵 Song lookup active", "type": discord.ActivityType.listening},
                {"name": "🎶 Music discovery", "type": discord.ActivityType.listening},
                {"name": "🎸 Artist information", "type": discord.ActivityType.listening},
                {"name": "💿 Album details", "type": discord.ActivityType.listening},
            ],
            'books': [
                {"name": "📚 Book searching", "type": discord.ActivityType.watching},
                {"name": "📖 Reading database", "type": discord.ActivityType.watching},
                {"name": "📝 Author lookup", "type": discord.ActivityType.watching},
                {"name": "🏛️ Library access", "type": discord.ActivityType.watching},
            ],
            'manga': [
                {"name": "📖 Manga search", "type": discord.ActivityType.watching},
                {"name": "🇯🇵 Anime database", "type": discord.ActivityType.watching},
                {"name": "👑 Top manga", "type": discord.ActivityType.watching},
                {"name": "✨ New chapters", "type": discord.ActivityType.watching},
            ],
            'gaming': [
                {"name": "🎮 Gaming stats", "type": discord.ActivityType.playing},
                {"name": "🏆 RPG adventures", "type": discord.ActivityType.playing},
                {"name": "⚔️ Battle system", "type": discord.ActivityType.competing},
                {"name": "🎯 Achievements", "type": discord.ActivityType.playing},
            ],
            'idle': [
                {"name": "😴 Resting...", "type": discord.ActivityType.watching},
                {"name": "🌙 Night mode", "type": discord.ActivityType.watching},
                {"name": "💤 Sleeping", "type": discord.ActivityType.watching},
                {"name": "🔋 Charging", "type": discord.ActivityType.watching},
            ],
            'celebration': [
                {"name": "🎉 Celebrating!", "type": discord.ActivityType.playing},
                {"name": "✨ Success!", "type": discord.ActivityType.playing},
                {"name": "🌟 Amazing!", "type": discord.ActivityType.playing},
                {"name": "🎊 Party time!", "type": discord.ActivityType.playing},
            ]
        }
        
        # Special emoji animations
        self.emoji_animations = {
            'loading_dots': ['⚪', '🔵', '🔴', '🟡', '🟢', '🟣'],
            'spinning': ['◐', '◓', '◑', '◒'],
            'bouncing': ['⬆️', '↗️', '➡️', '↘️', '⬇️', '↙️', '⬅️', '↖️'],
            'pulsing': ['🔆', '🔅', '💫', '⭐', '✨', '🌟'],
            'musical': ['🎵', '🎶', '🎼', '🎹', '🎸', '🥁'],
            'books': ['📚', '📖', '📝', '📄', '📜', '📋'],
            'search': ['🔍', '🔎', '🕵️', '🔬', '📡', '⚡']
        }
        
        self.current_sequence = 'default'
        self.animation_speed = 3.0  # seconds between status changes
        
    async def start_animated_status(self):
        """Start the animated status system"""
        if not self.is_running:
            self.is_running = True
            self.status_updater.start()
            logger.info("Animated status system started")
    
    async def stop_animated_status(self):
        """Stop the animated status system"""
        if self.is_running:
            self.is_running = False
            self.status_updater.stop()
            logger.info("Animated status system stopped")
    
    async def set_sequence(self, sequence_name: str, duration: int = None):
        """Set a specific status sequence"""
        if sequence_name in self.status_sequences:
            self.current_sequence = sequence_name
            self.current_status_index = 0
            logger.info(f"Status sequence changed to: {sequence_name}")
            
            # If duration is specified, revert to default after that time
            if duration:
                await asyncio.sleep(duration)
                self.current_sequence = 'default'
                self.current_status_index = 0
    
    async def set_temporary_status(self, activity_name: str, activity_type: discord.ActivityType, duration: int = 5):
        """Set a temporary status that reverts after duration"""
        # Store current state
        original_sequence = self.current_sequence
        original_index = self.current_status_index
        
        # Set temporary status
        await self.bot.change_presence(
            activity=discord.Activity(type=activity_type, name=activity_name)
        )
        
        # Wait for duration
        await asyncio.sleep(duration)
        
        # Restore original state
        self.current_sequence = original_sequence
        self.current_status_index = original_index
    
    async def create_animated_embed_title(self, base_title: str, animation_type: str = 'pulsing'):
        """Create an animated title for embeds"""
        if animation_type in self.emoji_animations:
            emoji = random.choice(self.emoji_animations[animation_type])
            return f"{emoji} {base_title}"
        return base_title
    
    async def get_loading_indicator(self, step: int = 0):
        """Get a loading indicator emoji"""
        loading_emojis = self.emoji_animations['loading_dots']
        return loading_emojis[step % len(loading_emojis)]
    
    async def get_activity_emoji(self, activity_type: str):
        """Get an appropriate emoji for activity type"""
        emoji_map = {
            'song': random.choice(self.emoji_animations['musical']),
            'book': random.choice(self.emoji_animations['books']),
            'manga': random.choice(['📖', '🇯🇵', '👑', '✨']),
            'comic': random.choice(['🦸', '💥', '🔥', '⚡']),
            'search': random.choice(self.emoji_animations['search']),
            'gaming': random.choice(['🎮', '🏆', '⚔️', '🎯']),
            'celebration': random.choice(['🎉', '✨', '🌟', '🎊'])
        }
        return emoji_map.get(activity_type, '🤖')
    
    @tasks.loop(seconds=3.0)
    async def status_updater(self):
        """Update bot status with animation"""
        if not self.is_running:
            return
            
        try:
            sequence = self.status_sequences[self.current_sequence]
            status_info = sequence[self.current_status_index]
            
            # Add random variation to some statuses
            if self.current_sequence == 'default':
                # Add server count to some statuses
                if 'Server activity' in status_info['name']:
                    guild_count = len(self.bot.guilds)
                    status_info['name'] = f"💬 {guild_count} servers"
                elif 'AI assistance' in status_info['name']:
                    user_count = sum(guild.member_count for guild in self.bot.guilds)
                    status_info['name'] = f"🤖 {user_count:,} users"
            
            # Apply status
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=status_info['type'],
                    name=status_info['name']
                )
            )
            
            # Move to next status
            self.current_status_index = (self.current_status_index + 1) % len(sequence)
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    @status_updater.before_loop
    async def before_status_updater(self):
        """Wait for bot to be ready before starting status updates"""
        await self.bot.wait_until_ready()
    
    async def trigger_search_animation(self):
        """Trigger search animation sequence"""
        await self.set_sequence('search', duration=8)
    
    async def trigger_loading_animation(self):
        """Trigger loading animation sequence"""
        await self.set_sequence('loading', duration=6)
    
    async def trigger_celebration_animation(self):
        """Trigger celebration animation sequence"""
        await self.set_sequence('celebration', duration=10)
    
    async def set_feature_status(self, feature: str):
        """Set status based on feature being used"""
        feature_sequences = {
            'music': 'music',
            'song': 'music',
            'book': 'books',
            'manga': 'manga',
            'comic': 'manga',
            'gaming': 'gaming',
            'rpg': 'gaming',
            'search': 'search'
        }
        
        sequence = feature_sequences.get(feature, 'default')
        await self.set_sequence(sequence, duration=15)

# Global status manager instance
status_manager = None

def get_status_manager(bot):
    """Get or create status manager instance"""
    global status_manager
    if status_manager is None:
        status_manager = AnimatedStatusManager(bot)
    return status_manager

async def setup_animated_status(bot):
    """Initialize animated status system"""
    manager = get_status_manager(bot)
    await manager.start_animated_status()
    return manager