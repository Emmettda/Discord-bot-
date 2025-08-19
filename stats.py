import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime, timedelta
from bot.utils.stats_tracker import StatsTracker
from bot.utils.helpers import create_embed, format_duration

logger = logging.getLogger(__name__)

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_tracker = StatsTracker()
    
    @app_commands.command(name="stats", description="View your server statistics")
    @app_commands.describe(user="User to view stats for (optional)")
    async def stats(self, interaction: discord.Interaction, user: discord.Member = None):
        """View user statistics"""
        await interaction.response.defer()
        
        try:
            target_user = user or interaction.user
            user_stats = self.stats_tracker.get_user_stats(target_user.id, interaction.guild.id)
            
            if not user_stats["messages"] and not user_stats["commands"]:
                embed = discord.Embed(
                    title="📊 No Statistics Found",
                    description=f"No activity data found for {target_user.mention}",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"📊 Statistics for {target_user.display_name}",
                description="Here's your server activity:",
                color=discord.Color.blue()
            )
            
            # Message statistics
            message_data = user_stats["messages"]
            if message_data:
                total_messages = message_data.get("total_messages", 0)
                total_characters = message_data.get("total_characters", 0)
                avg_length = total_characters / max(total_messages, 1)
                
                embed.add_field(
                    name="💬 Messages",
                    value=f"**Total:** {total_messages:,}\n"
                          f"**Characters:** {total_characters:,}\n"
                          f"**Avg Length:** {avg_length:.1f}",
                    inline=True
                )
                
                # Last message info
                if message_data.get("last_message"):
                    last_msg = datetime.fromisoformat(message_data["last_message"])
                    time_diff = datetime.utcnow() - last_msg
                    embed.add_field(
                        name="⏰ Last Message",
                        value=f"{format_duration(int(time_diff.total_seconds()))} ago",
                        inline=True
                    )
            
            # Command statistics
            command_data = user_stats["commands"]
            if command_data:
                total_commands = command_data.get("total_commands", 0)
                commands_used = command_data.get("commands", {})
                
                embed.add_field(
                    name="🤖 Commands",
                    value=f"**Total Used:** {total_commands:,}\n"
                          f"**Different Commands:** {len(commands_used)}",
                    inline=True
                )
                
                # Most used commands
                if commands_used:
                    top_commands = sorted(commands_used.items(), key=lambda x: x[1], reverse=True)[:3]
                    command_list = []
                    for cmd, count in top_commands:
                        command_list.append(f"`/{cmd}` ({count})")
                    
                    embed.add_field(
                        name="🔥 Favorite Commands",
                        value="\n".join(command_list),
                        inline=True
                    )
            
            # Activity chart for last 7 days
            activity_chart = self.stats_tracker.get_user_activity_chart(target_user.id, interaction.guild.id, 7)
            if activity_chart:
                recent_activity = []
                for date, data in list(activity_chart.items())[-7:]:
                    messages = data.get("messages", 0)
                    if messages > 0:
                        recent_activity.append(f"{date}: {messages} messages")
                
                if recent_activity:
                    embed.add_field(
                        name="📈 Recent Activity (Last 7 Days)",
                        value="\n".join(recent_activity[-5:]),  # Show last 5 days with activity
                        inline=False
                    )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Member since {target_user.joined_at.strftime('%B %d, %Y')}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            await interaction.followup.send(f"❌ Error getting stats: {str(e)}")
    
    @app_commands.command(name="leaderboard", description="View server leaderboards")
    @app_commands.describe(
        category="Category to view (messages, commands)",
        limit="Number of users to show (default: 10)"
    )
    async def leaderboard(self, interaction: discord.Interaction, category: str = "messages", limit: int = 10):
        """View server leaderboards"""
        await interaction.response.defer()
        
        try:
            if limit < 1 or limit > 25:
                await interaction.followup.send("❌ Limit must be between 1 and 25")
                return
            
            if category.lower() == "messages":
                leaderboard = self.stats_tracker.get_guild_leaderboard(interaction.guild.id, limit)
                title = "💬 Message Leaderboard"
                description = "Most active members by message count"
            elif category.lower() == "commands":
                leaderboard = self.stats_tracker.get_command_leaderboard(interaction.guild.id, limit)
                title = "🤖 Command Leaderboard"
                description = "Most active command users"
            else:
                await interaction.followup.send("❌ Invalid category. Use 'messages' or 'commands'")
                return
            
            if not leaderboard:
                embed = discord.Embed(
                    title="📊 No Data Available",
                    description="No activity data found for this server",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.gold()
            )
            
            leaderboard_text = []
            medals = ["🥇", "🥈", "🥉"]
            
            for i, (user_id, stats) in enumerate(leaderboard, 1):
                try:
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    user_name = user.display_name if user else f"User {user_id}"
                except:
                    user_name = f"User {user_id}"
                
                medal = medals[i-1] if i <= 3 else f"{i}."
                
                if category.lower() == "messages":
                    value = f"{stats['total_messages']:,} messages"
                    if stats['total_characters'] > 0:
                        value += f" ({stats['avg_message_length']:.1f} avg)"
                else:
                    value = f"{stats['total_commands']:,} commands"
                    if stats['favorite_command'] != "None":
                        value += f" (loves `/{stats['favorite_command']}`)"
                
                leaderboard_text.append(f"{medal} **{user_name}** - {value}")
            
            embed.add_field(
                name="🏆 Rankings",
                value="\n".join(leaderboard_text),
                inline=False
            )
            
            embed.set_footer(text=f"📊 {interaction.guild.name} • Top {len(leaderboard)} users")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            await interaction.followup.send(f"❌ Error getting leaderboard: {str(e)}")
    
    @app_commands.command(name="server_stats", description="View overall server statistics")
    async def server_stats(self, interaction: discord.Interaction):
        """View overall server statistics"""
        await interaction.response.defer()
        
        try:
            guild_stats = self.stats_tracker.get_guild_stats(interaction.guild.id)
            
            embed = discord.Embed(
                title=f"📊 Server Statistics for {interaction.guild.name}",
                description="Overall server activity overview",
                color=discord.Color.purple()
            )
            
            # Basic stats
            embed.add_field(
                name="💬 Messages",
                value=f"**Total:** {guild_stats['total_messages']:,}\n"
                      f"**Characters:** {guild_stats['total_characters']:,}\n"
                      f"**Avg Length:** {guild_stats['avg_message_length']:.1f}",
                inline=True
            )
            
            embed.add_field(
                name="🤖 Commands",
                value=f"**Total Used:** {guild_stats['total_commands']:,}\n"
                      f"**Active Users:** {guild_stats['active_users']:,}",
                inline=True
            )
            
            # Server info
            embed.add_field(
                name="👥 Server Info",
                value=f"**Members:** {interaction.guild.member_count:,}\n"
                      f"**Created:** {interaction.guild.created_at.strftime('%B %d, %Y')}\n"
                      f"**Channels:** {len(interaction.guild.channels)}",
                inline=True
            )
            
            # Popular commands
            popular_commands = guild_stats.get('popular_commands', {})
            if popular_commands:
                command_list = []
                for cmd, count in list(popular_commands.items())[:5]:
                    command_list.append(f"`/{cmd}` ({count:,})")
                
                embed.add_field(
                    name="🔥 Popular Commands",
                    value="\n".join(command_list),
                    inline=False
                )
            
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(text=f"Statistics tracked since bot joined • {datetime.utcnow().strftime('%B %d, %Y')}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            await interaction.followup.send(f"❌ Error getting server stats: {str(e)}")
    
    @app_commands.command(name="activity_chart", description="View your activity chart")
    @app_commands.describe(
        user="User to view activity for (optional)",
        days="Number of days to show (default: 14)"
    )
    async def activity_chart(self, interaction: discord.Interaction, user: discord.Member = None, days: int = 14):
        """View user activity chart"""
        await interaction.response.defer()
        
        try:
            if days < 1 or days > 90:
                await interaction.followup.send("❌ Days must be between 1 and 90")
                return
            
            target_user = user or interaction.user
            activity_chart = self.stats_tracker.get_user_activity_chart(target_user.id, interaction.guild.id, days)
            
            if not activity_chart:
                embed = discord.Embed(
                    title="📈 No Activity Data",
                    description=f"No activity data found for {target_user.mention}",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"📈 Activity Chart for {target_user.display_name}",
                description=f"Message activity over the last {days} days",
                color=discord.Color.green()
            )
            
            # Create a simple text-based chart
            chart_lines = []
            max_messages = max(data.get("messages", 0) for data in activity_chart.values())
            
            if max_messages == 0:
                embed.add_field(
                    name="📊 Chart",
                    value="No messages in the selected period",
                    inline=False
                )
            else:
                for date, data in list(activity_chart.items())[-days:]:
                    messages = data.get("messages", 0)
                    if messages > 0:
                        # Create a simple bar chart with blocks
                        bar_length = max(1, int((messages / max_messages) * 20))
                        bar = "█" * bar_length
                        chart_lines.append(f"`{date}` {bar} ({messages})")
                
                if chart_lines:
                    # Show chart in chunks if too long
                    chart_text = "\n".join(chart_lines[-20:])  # Show last 20 days max
                    embed.add_field(
                        name="📊 Activity Chart",
                        value=chart_text,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="📊 Chart",
                        value="No messages in the selected period",
                        inline=False
                    )
            
            # Summary stats
            total_messages = sum(data.get("messages", 0) for data in activity_chart.values())
            active_days = sum(1 for data in activity_chart.values() if data.get("messages", 0) > 0)
            
            embed.add_field(
                name="📊 Summary",
                value=f"**Total Messages:** {total_messages:,}\n"
                      f"**Active Days:** {active_days}/{days}\n"
                      f"**Daily Average:** {total_messages/days:.1f}",
                inline=True
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Chart for {days} days • Peak: {max_messages} messages")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting activity chart: {e}")
            await interaction.followup.send(f"❌ Error getting activity chart: {str(e)}")

async def setup(bot):
    await bot.add_cog(StatsCog(bot))