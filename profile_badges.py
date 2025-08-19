import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import os
import asyncio
import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict
import random

logger = logging.getLogger(__name__)

class ProfileBadgesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_url = os.getenv('DATABASE_URL')
        self.data_dir = "data"
        self.badges_file = os.path.join(self.data_dir, "user_badges.json")
        self.achievements_file = os.path.join(self.data_dir, "achievements.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files
        self._init_file(self.badges_file, {})
        self._init_file(self.achievements_file, {})
        
        # Initialize database
        self._init_database()
        
        # Badge definitions with requirements and rewards
        self.badge_definitions = {
            # Activity Badges
            "first_message": {
                "name": "First Steps",
                "description": "Send your first message in the server",
                "emoji": "👋",
                "color": 0x90EE90,
                "category": "Activity",
                "rarity": "common",
                "points": 10
            },
            "chatterbox": {
                "name": "Chatterbox",
                "description": "Send 100 messages",
                "emoji": "💬",
                "color": 0x87CEEB,
                "category": "Activity",
                "rarity": "common",
                "points": 50,
                "requirement": {"type": "message_count", "value": 100}
            },
            "social_butterfly": {
                "name": "Social Butterfly",
                "description": "Send 1,000 messages",
                "emoji": "🦋",
                "color": 0xDDA0DD,
                "category": "Activity",
                "rarity": "uncommon",
                "points": 200,
                "requirement": {"type": "message_count", "value": 1000}
            },
            "legend": {
                "name": "Server Legend",
                "description": "Send 10,000 messages",
                "emoji": "👑",
                "color": 0xFFD700,
                "category": "Activity",
                "rarity": "legendary",
                "points": 1000,
                "requirement": {"type": "message_count", "value": 10000}
            },
            
            # Music Badges
            "music_lover": {
                "name": "Music Lover",
                "description": "Play your first song",
                "emoji": "🎵",
                "color": 0xFF69B4,
                "category": "Music",
                "rarity": "common",
                "points": 25
            },
            "dj_master": {
                "name": "DJ Master",
                "description": "Play 50 songs",
                "emoji": "🎧",
                "color": 0x8A2BE2,
                "category": "Music",
                "rarity": "uncommon",
                "points": 150,
                "requirement": {"type": "songs_played", "value": 50}
            },
            "music_curator": {
                "name": "Music Curator",
                "description": "Set music preferences and create profile",
                "emoji": "🎼",
                "color": 0x20B2AA,
                "category": "Music",
                "rarity": "uncommon",
                "points": 100
            },
            
            # Gaming Badges
            "first_gamble": {
                "name": "Lucky Beginner",
                "description": "Place your first bet",
                "emoji": "🎲",
                "color": 0xFF6347,
                "category": "Gaming",
                "rarity": "common",
                "points": 20
            },
            "high_roller": {
                "name": "High Roller",
                "description": "Win 10,000 coins gambling",
                "emoji": "💰",
                "color": 0xFFD700,
                "category": "Gaming",
                "rarity": "rare",
                "points": 300,
                "requirement": {"type": "gambling_wins", "value": 10000}
            },
            "rpg_hero": {
                "name": "RPG Hero",
                "description": "Reach level 10 in RPG",
                "emoji": "⚔️",
                "color": 0xDC143C,
                "category": "Gaming",
                "rarity": "rare",
                "points": 250,
                "requirement": {"type": "rpg_level", "value": 10}
            },
            "quest_master": {
                "name": "Quest Master",
                "description": "Complete 25 RPG quests",
                "emoji": "🗡️",
                "color": 0x8B4513,
                "category": "Gaming",
                "rarity": "uncommon",
                "points": 180,
                "requirement": {"type": "quests_completed", "value": 25}
            },
            
            # Social Badges
            "helper": {
                "name": "Helpful Soul",
                "description": "Help other members with commands",
                "emoji": "🤝",
                "color": 0x32CD32,
                "category": "Social",
                "rarity": "uncommon",
                "points": 120
            },
            "early_bird": {
                "name": "Early Bird",
                "description": "Be active during early morning hours",
                "emoji": "🌅",
                "color": 0xFFA500,
                "category": "Social",
                "rarity": "uncommon",
                "points": 80
            },
            "night_owl": {
                "name": "Night Owl",
                "description": "Be active during late night hours",
                "emoji": "🦉",
                "color": 0x191970,
                "category": "Social",
                "rarity": "uncommon",
                "points": 80
            },
            "streak_keeper": {
                "name": "Streak Keeper",
                "description": "Maintain a 7-day activity streak",
                "emoji": "🔥",
                "color": 0xFF4500,
                "category": "Social",
                "rarity": "rare",
                "points": 200,
                "requirement": {"type": "daily_streak", "value": 7}
            },
            
            # Special Badges
            "beta_tester": {
                "name": "Beta Tester",
                "description": "Help test new bot features",
                "emoji": "🧪",
                "color": 0x9400D3,
                "category": "Special",
                "rarity": "rare",
                "points": 500
            },
            "supporter": {
                "name": "Server Supporter",
                "description": "Show outstanding support for the community",
                "emoji": "💎",
                "color": 0x00CED1,
                "category": "Special",
                "rarity": "legendary",
                "points": 750
            },
            "perfectionist": {
                "name": "Perfectionist",
                "description": "Earn 10 different badges",
                "emoji": "⭐",
                "color": 0xFFD700,
                "category": "Special",
                "rarity": "legendary",
                "points": 1000,
                "requirement": {"type": "badges_count", "value": 10}
            },
            
            # Command Usage Badges
            "meme_lord": {
                "name": "Meme Lord",
                "description": "Use meme command 25 times",
                "emoji": "😂",
                "color": 0xFF1493,
                "category": "Commands",
                "rarity": "uncommon",
                "points": 100,
                "requirement": {"type": "command_usage", "command": "meme", "value": 25}
            },
            "anime_enthusiast": {
                "name": "Anime Enthusiast",
                "description": "Use anime commands 20 times",
                "emoji": "🎌",
                "color": 0xFF69B4,
                "category": "Commands",
                "rarity": "uncommon",
                "points": 120,
                "requirement": {"type": "anime_commands", "value": 20}
            },
            "movie_buff": {
                "name": "Movie Buff",
                "description": "Search for 15 different movies",
                "emoji": "🎬",
                "color": 0x4169E1,
                "category": "Commands",
                "rarity": "uncommon",
                "points": 110,
                "requirement": {"type": "movie_searches", "value": 15}
            }
        }
        
        # Rarity colors for visual distinction
        self.rarity_colors = {
            "common": 0x808080,      # Gray
            "uncommon": 0x00FF00,    # Green
            "rare": 0x0080FF,        # Blue
            "epic": 0x8000FF,        # Purple
            "legendary": 0xFFD700    # Gold
        }

    def _init_file(self, file_path: str, default_data: dict):
        """Initialize a JSON file with default data if it doesn't exist"""
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=2)

    def _read_json(self, file_path: str) -> dict:
        """Read JSON data from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_json(self, file_path: str, data: dict):
        """Write JSON data to file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _init_database(self):
        """Initialize PostgreSQL database tables"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Create user_badges table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_badges (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    guild_id BIGINT NOT NULL,
                    badge_id VARCHAR(50) NOT NULL,
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    progress JSONB DEFAULT '{}',
                    UNIQUE(user_id, guild_id, badge_id)
                )
            """)
            
            # Create badge_progress table for tracking requirements
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS badge_progress (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    guild_id BIGINT NOT NULL,
                    badge_id VARCHAR(50) NOT NULL,
                    current_value INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, guild_id, badge_id)
                )
            """)
            
            # Create user_stats table for comprehensive tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profile_stats (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    guild_id BIGINT NOT NULL,
                    total_badges INTEGER DEFAULT 0,
                    badge_points INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    favorite_badge VARCHAR(50),
                    badge_showcase JSONB DEFAULT '[]',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, guild_id)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    async def _get_user_badges(self, user_id: int, guild_id: int) -> list:
        """Get all badges for a user"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT badge_id, earned_at FROM user_badges 
                WHERE user_id = %s AND guild_id = %s
                ORDER BY earned_at DESC
            """, (user_id, guild_id))
            
            badges = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [(badge[0], badge[1]) for badge in badges]
            
        except Exception as e:
            logger.error(f"Error getting user badges: {e}")
            return []

    async def _award_badge(self, user_id: int, guild_id: int, badge_id: str) -> bool:
        """Award a badge to a user"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Check if user already has this badge
            cursor.execute("""
                SELECT id FROM user_badges 
                WHERE user_id = %s AND guild_id = %s AND badge_id = %s
            """, (user_id, guild_id, badge_id))
            
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return False  # Already has badge
            
            # Award the badge
            cursor.execute("""
                INSERT INTO user_badges (user_id, guild_id, badge_id)
                VALUES (%s, %s, %s)
            """, (user_id, guild_id, badge_id))
            
            # Update user stats
            badge_info = self.badge_definitions.get(badge_id, {})
            points = badge_info.get('points', 0)
            
            cursor.execute("""
                INSERT INTO user_profile_stats (user_id, guild_id, total_badges, badge_points)
                VALUES (%s, %s, 1, %s)
                ON CONFLICT (user_id, guild_id)
                DO UPDATE SET 
                    total_badges = user_profile_stats.total_badges + 1,
                    badge_points = user_profile_stats.badge_points + %s,
                    last_updated = CURRENT_TIMESTAMP
            """, (user_id, guild_id, points, points))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error awarding badge: {e}")
            return False

    async def _update_progress(self, user_id: int, guild_id: int, badge_id: str, value: int):
        """Update progress for a badge requirement"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO badge_progress (user_id, guild_id, badge_id, current_value)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, guild_id, badge_id)
                DO UPDATE SET 
                    current_value = %s,
                    last_updated = CURRENT_TIMESTAMP
            """, (user_id, guild_id, badge_id, value, value))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    async def _check_badge_requirements(self, user_id: int, guild_id: int, event_type: str, event_data: dict = None):
        """Check if user meets requirements for any badges"""
        user_badges = await self._get_user_badges(user_id, guild_id)
        earned_badge_ids = [badge[0] for badge in user_badges]
        
        newly_earned = []
        
        # Check each badge definition
        for badge_id, badge_info in self.badge_definitions.items():
            if badge_id in earned_badge_ids:
                continue  # Already has this badge
            
            requirement = badge_info.get('requirement')
            if not requirement:
                continue  # No requirement to check
            
            # Check different types of requirements
            if requirement['type'] == event_type:
                should_award = False
                
                if event_type == "message_count":
                    # Get current message count from stats
                    current_count = await self._get_user_stat(user_id, guild_id, 'message_count')
                    if current_count >= requirement['value']:
                        should_award = True
                        
                elif event_type == "command_usage":
                    if event_data and event_data.get('command') == requirement.get('command'):
                        current_count = await self._get_user_stat(user_id, guild_id, f"command_{requirement['command']}")
                        if current_count >= requirement['value']:
                            should_award = True
                            
                elif event_type == "songs_played":
                    current_count = await self._get_user_stat(user_id, guild_id, 'songs_played')
                    if current_count >= requirement['value']:
                        should_award = True
                        
                # Add more requirement checks as needed
                
                if should_award:
                    success = await self._award_badge(user_id, guild_id, badge_id)
                    if success:
                        newly_earned.append(badge_id)
        
        return newly_earned

    async def _get_user_stat(self, user_id: int, guild_id: int, stat_name: str) -> int:
        """Get a specific user statistic"""
        # This would integrate with existing stats systems
        # For now, return mock data
        return 0

    @app_commands.command(name="profile", description="View your profile with badges and achievements")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        """View user profile with badges"""
        target_user = user or interaction.user
        user_id = target_user.id
        guild_id = interaction.guild.id
        
        # Get user badges
        user_badges = await self._get_user_badges(user_id, guild_id)
        
        # Get user stats
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT total_badges, badge_points, level, experience, favorite_badge, badge_showcase
                FROM user_profile_stats 
                WHERE user_id = %s AND guild_id = %s
            """, (user_id, guild_id))
            
            stats = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if stats:
                total_badges, badge_points, level, experience, favorite_badge, badge_showcase = stats
                badge_showcase = badge_showcase or []
            else:
                total_badges = badge_points = experience = 0
                level = 1
                favorite_badge = None
                badge_showcase = []
                
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            total_badges = badge_points = experience = 0
            level = 1
            favorite_badge = None
            badge_showcase = []
        
        # Calculate level progress
        level_exp_required = level * 100
        level_progress = (experience % level_exp_required) / level_exp_required * 100
        
        # Create profile embed
        embed = discord.Embed(
            title=f"🏆 {target_user.display_name}'s Profile",
            color=discord.Color.purple()
        )
        
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
        
        # Level and experience
        embed.add_field(
            name="📊 Level & Experience",
            value=f"**Level:** {level}\n"
                  f"**Experience:** {experience:,}\n"
                  f"**Progress:** {'█' * int(level_progress//10)}{'░' * (10-int(level_progress//10))} {level_progress:.1f}%",
            inline=True
        )
        
        # Badge statistics
        embed.add_field(
            name="🏅 Badge Collection",
            value=f"**Total Badges:** {total_badges}\n"
                  f"**Badge Points:** {badge_points:,}\n"
                  f"**Completion:** {(total_badges/len(self.badge_definitions)*100):.1f}%",
            inline=True
        )
        
        # Rarity breakdown
        rarity_counts = defaultdict(int)
        for badge_id, _ in user_badges:
            badge_info = self.badge_definitions.get(badge_id, {})
            rarity = badge_info.get('rarity', 'common')
            rarity_counts[rarity] += 1
        
        rarity_text = ""
        for rarity in ['common', 'uncommon', 'rare', 'epic', 'legendary']:
            count = rarity_counts[rarity]
            if count > 0:
                rarity_text += f"**{rarity.title()}:** {count}\n"
        
        if rarity_text:
            embed.add_field(
                name="💎 Badge Rarity",
                value=rarity_text,
                inline=True
            )
        
        # Showcase badges (top 6)
        if user_badges:
            showcase_badges = user_badges[:6]  # Show top 6 most recent
            badge_display = ""
            
            for badge_id, earned_at in showcase_badges:
                badge_info = self.badge_definitions.get(badge_id, {})
                badge_display += f"{badge_info.get('emoji', '🏅')} **{badge_info.get('name', badge_id)}**\n"
            
            embed.add_field(
                name="🎖️ Badge Showcase",
                value=badge_display,
                inline=False
            )
        
        # Recent achievements
        if user_badges:
            recent_badge = user_badges[0]
            badge_info = self.badge_definitions.get(recent_badge[0], {})
            embed.add_field(
                name="🆕 Latest Achievement",
                value=f"{badge_info.get('emoji', '🏅')} **{badge_info.get('name', 'Unknown')}**\n"
                      f"*{badge_info.get('description', 'No description')}*",
                inline=False
            )
        
        embed.set_footer(text=f"Use /badges to see all available badges • Profile Level {level}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="badges", description="View all available badges and your progress")
    async def badges(self, interaction: discord.Interaction, category: str = None, rarity: str = None):
        """View all badges with filters"""
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        # Get user's earned badges
        user_badges = await self._get_user_badges(user_id, guild_id)
        earned_badge_ids = [badge[0] for badge in user_badges]
        
        # Filter badges
        filtered_badges = {}
        for badge_id, badge_info in self.badge_definitions.items():
            if category and badge_info.get('category', '').lower() != category.lower():
                continue
            if rarity and badge_info.get('rarity', '').lower() != rarity.lower():
                continue
            filtered_badges[badge_id] = badge_info
        
        if not filtered_badges:
            await interaction.response.send_message("❌ No badges found with those filters!", ephemeral=True)
            return
        
        # Create paginated embed
        badges_per_page = 8
        pages = []
        badge_items = list(filtered_badges.items())
        
        for i in range(0, len(badge_items), badges_per_page):
            embed = discord.Embed(
                title="🏆 Badge Collection",
                description=f"Showing badges {i+1}-{min(i+badges_per_page, len(badge_items))} of {len(badge_items)}",
                color=discord.Color.gold()
            )
            
            if category:
                embed.description += f" | Category: {category.title()}"
            if rarity:
                embed.description += f" | Rarity: {rarity.title()}"
            
            page_badges = badge_items[i:i+badges_per_page]
            
            for badge_id, badge_info in page_badges:
                earned = badge_id in earned_badge_ids
                
                # Progress tracking
                requirement = badge_info.get('requirement')
                progress_text = ""
                if requirement and not earned:
                    # Get current progress
                    current_value = await self._get_progress(user_id, guild_id, badge_id)
                    required_value = requirement.get('value', 0)
                    progress_text = f"\n📈 Progress: {current_value}/{required_value}"
                
                status_emoji = "✅" if earned else "🔒"
                rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(
                    badge_info.get('rarity', 'common'), "⚪"
                )
                
                embed.add_field(
                    name=f"{status_emoji} {badge_info.get('emoji', '🏅')} {badge_info.get('name', badge_id)}",
                    value=f"*{badge_info.get('description', 'No description')}*\n"
                          f"{rarity_emoji} **{badge_info.get('rarity', 'common').title()}** | "
                          f"**{badge_info.get('points', 0)} pts**"
                          f"{progress_text}",
                    inline=True
                )
            
            # Add empty fields for better layout
            while len(embed.fields) % 3 != 0:
                embed.add_field(name="\u200b", value="\u200b", inline=True)
            
            embed.set_footer(text=f"Page {len(pages)+1} | {len([b for b in earned_badge_ids if b in filtered_badges])}/{len(filtered_badges)} earned")
            pages.append(embed)
        
        if len(pages) == 1:
            await interaction.response.send_message(embed=pages[0])
        else:
            # Implement pagination view
            view = BadgePaginationView(pages)
            await interaction.response.send_message(embed=pages[0], view=view)

    async def _get_progress(self, user_id: int, guild_id: int, badge_id: str) -> int:
        """Get current progress for a badge"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT current_value FROM badge_progress
                WHERE user_id = %s AND guild_id = %s AND badge_id = %s
            """, (user_id, guild_id, badge_id))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting progress: {e}")
            return 0

    @app_commands.command(name="badge_leaderboard", description="View the server badge leaderboard")
    async def badge_leaderboard(self, interaction: discord.Interaction, sort_by: str = "points"):
        """View badge leaderboard"""
        guild_id = interaction.guild.id
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            if sort_by == "points":
                order_field = "badge_points DESC"
                title = "🏆 Badge Points Leaderboard"
            elif sort_by == "badges":
                order_field = "total_badges DESC"
                title = "🏅 Total Badges Leaderboard"
            elif sort_by == "level":
                order_field = "level DESC, experience DESC"
                title = "📊 Level Leaderboard"
            else:
                order_field = "badge_points DESC"
                title = "🏆 Badge Points Leaderboard"
            
            cursor.execute(f"""
                SELECT user_id, total_badges, badge_points, level, experience
                FROM user_profile_stats 
                WHERE guild_id = %s AND total_badges > 0
                ORDER BY {order_field}
                LIMIT 10
            """, (guild_id,))
            
            leaderboard = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not leaderboard:
                await interaction.response.send_message("❌ No badge data found for this server!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=title,
                color=discord.Color.gold()
            )
            
            for i, (user_id, total_badges, badge_points, level, experience) in enumerate(leaderboard, 1):
                user = self.bot.get_user(user_id)
                if not user:
                    continue
                
                if sort_by == "points":
                    value = f"**{badge_points:,}** points | {total_badges} badges"
                elif sort_by == "badges":
                    value = f"**{total_badges}** badges | {badge_points:,} points"
                else:
                    value = f"**Level {level}** | {experience:,} XP"
                
                medal = {"1": "🥇", "2": "🥈", "3": "🥉"}.get(str(i), f"{i}.")
                
                embed.add_field(
                    name=f"{medal} {user.display_name}",
                    value=value,
                    inline=False
                )
            
            embed.set_footer(text=f"Showing top {len(leaderboard)} members")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            await interaction.response.send_message("❌ Error retrieving leaderboard data!", ephemeral=True)

    @app_commands.command(name="award_badge", description="Award a special badge to a user (Admin only)")
    @app_commands.describe(user="User to award badge to", badge_id="Badge ID to award")
    async def award_badge(self, interaction: discord.Interaction, user: discord.Member, badge_id: str):
        """Manually award a badge (admin only)"""
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to award badges!", ephemeral=True)
            return
        
        if badge_id not in self.badge_definitions:
            available_badges = ", ".join(list(self.badge_definitions.keys())[:10])
            await interaction.response.send_message(f"❌ Invalid badge ID! Available: {available_badges}...", ephemeral=True)
            return
        
        success = await self._award_badge(user.id, interaction.guild.id, badge_id)
        
        if success:
            badge_info = self.badge_definitions[badge_id]
            embed = discord.Embed(
                title="🎉 Badge Awarded!",
                description=f"{user.mention} has been awarded the **{badge_info['name']}** badge!",
                color=badge_info.get('color', discord.Color.green())
            )
            
            embed.add_field(
                name=f"{badge_info.get('emoji', '🏅')} {badge_info['name']}",
                value=f"*{badge_info.get('description', 'No description')}*\n"
                      f"**Points:** {badge_info.get('points', 0)}",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ User already has this badge or an error occurred!", ephemeral=True)

    async def track_message_activity(self, message):
        """Track message activity for badge progression"""
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Award first message badge
        user_badges = await self._get_user_badges(user_id, guild_id)
        earned_badge_ids = [badge[0] for badge in user_badges]
        
        if "first_message" not in earned_badge_ids:
            await self._award_badge(user_id, guild_id, "first_message")
            
            # Send congratulations
            try:
                badge_info = self.badge_definitions["first_message"]
                embed = discord.Embed(
                    title="🎉 First Badge Earned!",
                    description=f"Congratulations {message.author.mention}! You earned your first badge!",
                    color=badge_info.get('color', discord.Color.green())
                )
                
                embed.add_field(
                    name=f"{badge_info.get('emoji', '🏅')} {badge_info['name']}",
                    value=f"*{badge_info.get('description', 'No description')}*",
                    inline=False
                )
                
                await message.channel.send(embed=embed, delete_after=10)
            except:
                pass
        
        # Check other message-based badges
        await self._check_badge_requirements(user_id, guild_id, "message_count")

    async def track_command_usage(self, interaction, command_name: str):
        """Track command usage for badge progression"""
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        # Track specific command usage
        await self._check_badge_requirements(user_id, guild_id, "command_usage", {"command": command_name})
        
        # Track music commands
        if command_name in ["play", "queue", "skip", "pause", "resume"]:
            if command_name == "play":
                user_badges = await self._get_user_badges(user_id, guild_id)
                earned_badge_ids = [badge[0] for badge in user_badges]
                
                if "music_lover" not in earned_badge_ids:
                    await self._award_badge(user_id, guild_id, "music_lover")

class BadgePaginationView(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0
        
        # Disable buttons if only one page
        if len(pages) <= 1:
            self.previous_page.disabled = True
            self.next_page.disabled = True

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray, emoji="⬅️")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray, emoji="➡️")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

async def setup(bot):
    await bot.add_cog(ProfileBadgesCog(bot))