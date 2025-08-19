import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedStatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.user_stats_file = os.path.join(self.data_dir, "user_stats.json")
        self.message_stats_file = os.path.join(self.data_dir, "message_stats.json")
        self.command_stats_file = os.path.join(self.data_dir, "command_stats.json")
        self.detailed_stats_file = os.path.join(self.data_dir, "detailed_stats.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files
        self._init_file(self.user_stats_file, {})
        self._init_file(self.message_stats_file, {})
        self._init_file(self.command_stats_file, {})
        self._init_file(self.detailed_stats_file, {})

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

    @app_commands.command(name="detailed_stats", description="View comprehensive user statistics")
    async def detailed_stats(self, interaction: discord.Interaction, user: discord.Member = None):
        """View comprehensive user statistics"""
        target_user = user or interaction.user
        user_id = str(target_user.id)
        guild_id = str(interaction.guild.id)
        
        detailed_stats = self._read_json(self.detailed_stats_file)
        user_data = detailed_stats.get(guild_id, {}).get(user_id, {})
        
        if not user_data:
            await interaction.response.send_message(f"❌ No detailed stats found for {target_user.mention}", ephemeral=True)
            return
        
        # Calculate various metrics
        total_messages = user_data.get('total_messages', 0)
        total_characters = user_data.get('total_characters', 0)
        avg_message_length = total_characters / total_messages if total_messages > 0 else 0
        
        commands_used = user_data.get('commands_used', {})
        most_used_command = max(commands_used.items(), key=lambda x: x[1]) if commands_used else ("None", 0)
        
        activity_by_hour = user_data.get('activity_by_hour', {})
        most_active_hour = max(activity_by_hour.items(), key=lambda x: x[1]) if activity_by_hour else ("Unknown", 0)
        
        channels_activity = user_data.get('channels_activity', {})
        most_active_channel = max(channels_activity.items(), key=lambda x: x[1]) if channels_activity else ("Unknown", 0)
        
        # Streak information
        current_streak = user_data.get('daily_streak', 0)
        longest_streak = user_data.get('longest_streak', 0)
        
        # Create comprehensive embed
        embed = discord.Embed(
            title=f"📊 Detailed Statistics - {target_user.display_name}",
            color=discord.Color.blue()
        )
        
        # Basic stats
        embed.add_field(
            name="💬 Message Statistics",
            value=f"**Total Messages:** {total_messages:,}\n"
                  f"**Total Characters:** {total_characters:,}\n"
                  f"**Avg Message Length:** {avg_message_length:.1f} chars",
            inline=True
        )
        
        # Command usage
        embed.add_field(
            name="🎮 Command Usage",
            value=f"**Most Used:** {most_used_command[0]}\n"
                  f"**Times Used:** {most_used_command[1]:,}\n"
                  f"**Total Commands:** {sum(commands_used.values()):,}",
            inline=True
        )
        
        # Activity patterns
        embed.add_field(
            name="⏰ Activity Patterns",
            value=f"**Most Active Hour:** {most_active_hour[0]}:00\n"
                  f"**Messages in Hour:** {most_active_hour[1]:,}\n"
                  f"**Daily Streak:** {current_streak} days",
            inline=True
        )
        
        # Channel activity
        if most_active_channel[0] != "Unknown":
            try:
                channel = self.bot.get_channel(int(most_active_channel[0]))
                channel_name = channel.name if channel else "Unknown Channel"
            except:
                channel_name = "Unknown Channel"
        else:
            channel_name = "No Activity"
            
        embed.add_field(
            name="📍 Channel Activity",
            value=f"**Most Active Channel:** #{channel_name}\n"
                  f"**Messages There:** {most_active_channel[1]:,}",
            inline=True
        )
        
        # Achievements and streaks
        embed.add_field(
            name="🏆 Achievements",
            value=f"**Longest Streak:** {longest_streak} days\n"
                  f"**Current Streak:** {current_streak} days\n"
                  f"**Account Age:** {(datetime.now() - target_user.created_at).days} days",
            inline=True
        )
        
        # Join date and server tenure
        if hasattr(target_user, 'joined_at') and target_user.joined_at:
            server_days = (datetime.now() - target_user.joined_at.replace(tzinfo=None)).days
            embed.add_field(
                name="📅 Server Info",
                value=f"**Joined Server:** {target_user.joined_at.strftime('%Y-%m-%d')}\n"
                      f"**Days in Server:** {server_days}\n"
                      f"**Messages/Day:** {total_messages/max(server_days, 1):.1f}",
                inline=True
            )
        
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
        embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="server_analytics", description="View comprehensive server analytics")
    async def server_analytics(self, interaction: discord.Interaction):
        """View comprehensive server analytics"""
        guild_id = str(interaction.guild.id)
        
        detailed_stats = self._read_json(self.detailed_stats_file)
        server_data = detailed_stats.get(guild_id, {})
        
        if not server_data:
            await interaction.response.send_message("❌ No server analytics available yet!", ephemeral=True)
            return
        
        # Calculate server-wide metrics
        total_users = len(server_data)
        total_messages = sum(user.get('total_messages', 0) for user in server_data.values())
        total_characters = sum(user.get('total_characters', 0) for user in server_data.values())
        total_commands = sum(sum(user.get('commands_used', {}).values()) for user in server_data.values())
        
        # Find most active users
        most_active_users = sorted(
            [(user_id, user.get('total_messages', 0)) for user_id, user in server_data.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        
        # Find most used commands across server
        all_commands = {}
        for user in server_data.values():
            for cmd, count in user.get('commands_used', {}).items():
                all_commands[cmd] = all_commands.get(cmd, 0) + count
        
        most_used_commands = sorted(all_commands.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Calculate activity by hour across server
        hourly_activity = {}
        for user in server_data.values():
            for hour, count in user.get('activity_by_hour', {}).items():
                hourly_activity[hour] = hourly_activity.get(hour, 0) + count
        
        peak_hour = max(hourly_activity.items(), key=lambda x: x[1]) if hourly_activity else ("Unknown", 0)
        
        embed = discord.Embed(
            title=f"📈 Server Analytics - {interaction.guild.name}",
            color=discord.Color.gold()
        )
        
        # Overview stats
        embed.add_field(
            name="📊 Overview",
            value=f"**Active Users:** {total_users:,}\n"
                  f"**Total Messages:** {total_messages:,}\n"
                  f"**Total Characters:** {total_characters:,}\n"
                  f"**Commands Used:** {total_commands:,}",
            inline=True
        )
        
        # Activity patterns
        embed.add_field(
            name="⏰ Activity Patterns",
            value=f"**Peak Hour:** {peak_hour[0]}:00\n"
                  f"**Messages/Hour:** {peak_hour[1]:,}\n"
                  f"**Avg Messages/User:** {total_messages/max(total_users, 1):.1f}",
            inline=True
        )
        
        # Most active users
        active_users_text = ""
        for i, (user_id, count) in enumerate(most_active_users, 1):
            try:
                user = self.bot.get_user(int(user_id))
                name = user.display_name if user else "Unknown User"
            except:
                name = "Unknown User"
            active_users_text += f"{i}. {name}: {count:,}\n"
        
        embed.add_field(
            name="👑 Most Active Users",
            value=active_users_text or "No data",
            inline=False
        )
        
        # Most used commands
        commands_text = ""
        for i, (cmd, count) in enumerate(most_used_commands, 1):
            commands_text += f"{i}. /{cmd}: {count:,}\n"
        
        embed.add_field(
            name="🎮 Popular Commands",
            value=commands_text or "No data",
            inline=False
        )
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text=f"Server created: {interaction.guild.created_at.strftime('%Y-%m-%d')}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="compare_stats", description="Compare your stats with another user")
    async def compare_stats(self, interaction: discord.Interaction, user: discord.Member):
        """Compare your stats with another user"""
        user1_id = str(interaction.user.id)
        user2_id = str(user.id)
        guild_id = str(interaction.guild.id)
        
        detailed_stats = self._read_json(self.detailed_stats_file)
        server_data = detailed_stats.get(guild_id, {})
        
        user1_data = server_data.get(user1_id, {})
        user2_data = server_data.get(user2_id, {})
        
        if not user1_data or not user2_data:
            await interaction.response.send_message("❌ Not enough data for comparison!", ephemeral=True)
            return
        
        # Compare metrics
        metrics = [
            ("Messages", "total_messages"),
            ("Characters", "total_characters"),
            ("Commands Used", lambda d: sum(d.get('commands_used', {}).values())),
            ("Daily Streak", "daily_streak"),
            ("Longest Streak", "longest_streak")
        ]
        
        embed = discord.Embed(
            title=f"⚔️ Stats Comparison",
            description=f"{interaction.user.display_name} vs {user.display_name}",
            color=discord.Color.purple()
        )
        
        for metric_name, metric_key in metrics:
            if callable(metric_key):
                val1 = metric_key(user1_data)
                val2 = metric_key(user2_data)
            else:
                val1 = user1_data.get(metric_key, 0)
                val2 = user2_data.get(metric_key, 0)
            
            if val1 > val2:
                winner = "🥇"
                loser = "🥈"
            elif val1 < val2:
                winner = "🥈"
                loser = "🥇"
            else:
                winner = loser = "🤝"
            
            embed.add_field(
                name=f"{metric_name}",
                value=f"{winner} {interaction.user.display_name}: {val1:,}\n"
                      f"{loser} {user.display_name}: {val2:,}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)

    async def track_message(self, message):
        """Track detailed message statistics"""
        if message.author.bot:
            return
        
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        current_hour = datetime.now().hour
        
        detailed_stats = self._read_json(self.detailed_stats_file)
        
        if guild_id not in detailed_stats:
            detailed_stats[guild_id] = {}
        
        if user_id not in detailed_stats[guild_id]:
            detailed_stats[guild_id][user_id] = {
                'total_messages': 0,
                'total_characters': 0,
                'commands_used': {},
                'activity_by_hour': {},
                'channels_activity': {},
                'daily_streak': 0,
                'longest_streak': 0,
                'last_message_date': None
            }
        
        user_data = detailed_stats[guild_id][user_id]
        
        # Update basic stats
        user_data['total_messages'] += 1
        user_data['total_characters'] += len(message.content)
        
        # Update hourly activity
        hour_key = str(current_hour)
        user_data['activity_by_hour'][hour_key] = user_data['activity_by_hour'].get(hour_key, 0) + 1
        
        # Update channel activity
        user_data['channels_activity'][channel_id] = user_data['channels_activity'].get(channel_id, 0) + 1
        
        # Update daily streak
        today = datetime.now().date().isoformat()
        last_date = user_data.get('last_message_date')
        
        if last_date != today:
            if last_date:
                last_datetime = datetime.fromisoformat(last_date).date()
                if (datetime.now().date() - last_datetime).days == 1:
                    user_data['daily_streak'] += 1
                elif (datetime.now().date() - last_datetime).days > 1:
                    user_data['daily_streak'] = 1
            else:
                user_data['daily_streak'] = 1
            
            user_data['longest_streak'] = max(user_data['longest_streak'], user_data['daily_streak'])
            user_data['last_message_date'] = today
        
        self._write_json(self.detailed_stats_file, detailed_stats)

    async def track_command(self, interaction):
        """Track command usage in detailed stats"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        command_name = interaction.command.name
        
        detailed_stats = self._read_json(self.detailed_stats_file)
        
        if guild_id not in detailed_stats:
            detailed_stats[guild_id] = {}
        
        if user_id not in detailed_stats[guild_id]:
            detailed_stats[guild_id][user_id] = {
                'total_messages': 0,
                'total_characters': 0,
                'commands_used': {},
                'activity_by_hour': {},
                'channels_activity': {},
                'daily_streak': 0,
                'longest_streak': 0,
                'last_message_date': None
            }
        
        user_data = detailed_stats[guild_id][user_id]
        user_data['commands_used'][command_name] = user_data['commands_used'].get(command_name, 0) + 1
        
        self._write_json(self.detailed_stats_file, detailed_stats)

async def setup(bot):
    await bot.add_cog(EnhancedStatsCog(bot))