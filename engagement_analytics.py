import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import datetime, timedelta
import logging
from bot.utils.helpers import create_embed
from bot.utils.engagement_tracker import EngagementTracker
from bot.utils.conversation_mapper import ConversationFlowMapper
import matplotlib.pyplot as plt
import io
import base64
from typing import Optional

logger = logging.getLogger(__name__)

class EngagementAnalyticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engagement_tracker = EngagementTracker()
        self.conversation_mapper = ConversationFlowMapper(self.engagement_tracker)
        
    @app_commands.command(name="engagement_summary", description="View community engagement summary")
    @app_commands.describe(days="Number of days to analyze (default: 7)")
    async def engagement_summary(self, interaction: discord.Interaction, days: int = 7):
        """View community engagement summary"""
        await interaction.response.defer()
        
        # Trigger analytics animation
        if hasattr(self.bot, 'status_manager'):
            await self.bot.status_manager.set_feature_status('gaming')
        
        try:
            guild_id = str(interaction.guild.id)
            summary = self.engagement_tracker.get_engagement_summary(guild_id, days)
            
            if 'error' in summary:
                embed = create_embed(
                    "📊 Engagement Summary",
                    summary['error'],
                    discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create animated title
            animated_title = "📊 Community Engagement Summary"
            if hasattr(self.bot, 'status_manager'):
                animated_title = await self.bot.status_manager.create_animated_embed_title(
                    "Community Engagement Summary", 'pulsing'
                )
            
            embed = create_embed(
                animated_title,
                f"Analysis for the last {days} days",
                discord.Color.blue()
            )
            
            # Overall metrics
            embed.add_field(
                name="📈 Overall Engagement",
                value=f"**Total Score:** {summary['total_engagement']:.1f}\n"
                      f"**Average per Event:** {summary['average_engagement']:.1f}\n"
                      f"**Engagement Events:** {summary['engagement_events']}",
                inline=True
            )
            
            # Top storytellers
            if summary['top_storytellers']:
                storyteller_text = ""
                for i, (user_id, score) in enumerate(summary['top_storytellers'][:5]):
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        storyteller_text += f"{i+1}. {user.display_name}: {score:.1f}\n"
                    except:
                        storyteller_text += f"{i+1}. User {user_id}: {score:.1f}\n"
                
                embed.add_field(
                    name="🎭 Top Storytellers",
                    value=storyteller_text,
                    inline=True
                )
            
            # Narrative themes
            if summary['top_narrative_themes']:
                themes_text = ""
                theme_emojis = {
                    'story_start': '📖',
                    'emotional_moments': '❤️',
                    'community_building': '🏗️',
                    'questions': '❓',
                    'celebration': '🎉',
                    'support': '🤝'
                }
                
                for theme, count in summary['top_narrative_themes'][:5]:
                    emoji = theme_emojis.get(theme, '🔸')
                    themes_text += f"{emoji} {theme.replace('_', ' ').title()}: {count}\n"
                
                embed.add_field(
                    name="🎨 Narrative Themes",
                    value=themes_text,
                    inline=True
                )
            
            # Community mood
            if summary['community_mood']:
                mood_text = ""
                mood_emojis = {
                    'emotional': '😊',
                    'positive': '✨',
                    'supportive': '🤗',
                    'collaborative': '🤝',
                    'curious': '🤔',
                    'creative': '🎨'
                }
                
                for mood, count in sorted(summary['community_mood'].items(), key=lambda x: x[1], reverse=True)[:4]:
                    emoji = mood_emojis.get(mood, '🔸')
                    mood_text += f"{emoji} {mood.title()}: {count}\n"
                
                embed.add_field(
                    name="🌟 Community Mood",
                    value=mood_text,
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting engagement summary: {e}")
            await interaction.followup.send("❌ Error retrieving engagement summary")
    
    @app_commands.command(name="conversation_flows", description="View conversation flow analysis")
    @app_commands.describe(channel="Specific channel to analyze (optional)")
    async def conversation_flows(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """View conversation flow analysis"""
        await interaction.response.defer()
        
        # Trigger search animation
        if hasattr(self.bot, 'status_manager'):
            await self.bot.status_manager.trigger_search_animation()
        
        try:
            guild_id = str(interaction.guild.id)
            channel_id = str(channel.id) if channel else None
            
            analytics = self.conversation_mapper.get_flow_analytics(guild_id, channel_id)
            
            # Create animated title
            animated_title = "🗺️ Conversation Flow Analysis"
            if hasattr(self.bot, 'status_manager'):
                animated_title = await self.bot.status_manager.create_animated_embed_title(
                    "Conversation Flow Analysis", 'bouncing'
                )
            
            embed = create_embed(
                animated_title,
                f"Analysis for {channel.mention if channel else 'entire server'}",
                discord.Color.purple()
            )
            
            if channel_id:
                # Channel-specific analysis
                embed.add_field(
                    name="📊 Flow Statistics",
                    value=f"**Active Flows:** {analytics['active_flows']}\n"
                          f"**Completed Flows:** {analytics['completed_flows']}",
                    inline=True
                )
                
                stats = analytics.get('statistics', {})
                if stats:
                    embed.add_field(
                        name="📈 Performance Metrics",
                        value=f"**Total Flows:** {stats.get('total_flows', 0)}\n"
                              f"**Avg Duration:** {stats.get('avg_duration', 0):.1f} min\n"
                              f"**Common Type:** {stats.get('most_common_type', 'N/A').title()}\n"
                              f"**Peak Engagement:** {stats.get('highest_engagement', 0):.2f}",
                        inline=True
                    )
                
                # Recent flows
                recent_flows = analytics.get('recent_flows', [])
                if recent_flows:
                    flow_text = ""
                    flow_type_emojis = {
                        'linear': '➡️',
                        'branching': '🌳',
                        'circular': '🔄',
                        'convergent': '🎯',
                        'parallel': '⚡'
                    }
                    
                    for flow in recent_flows[:3]:
                        emoji = flow_type_emojis.get(flow['flow_type'], '🔸')
                        flow_text += f"{emoji} {flow['flow_type'].title()}: {flow['duration_minutes']}min, "
                        flow_text += f"{len(flow['participants'])} participants\n"
                    
                    embed.add_field(
                        name="🔄 Recent Flows",
                        value=flow_text,
                        inline=False
                    )
                    
            else:
                # Guild-wide analysis
                embed.add_field(
                    name="📊 Server-Wide Statistics",
                    value=f"**Active Flows:** {analytics['total_active_flows']}\n"
                          f"**Completed Flows:** {analytics['total_completed_flows']}\n"
                          f"**Channels with Flows:** {analytics['channels_with_flows']}",
                    inline=True
                )
                
                embed.add_field(
                    name="📈 Average Metrics",
                    value=f"**Duration:** {analytics['average_duration_minutes']:.1f} min\n"
                          f"**Engagement:** {analytics['average_engagement_intensity']:.2f}\n"
                          f"**Coherence:** {analytics['average_narrative_coherence']:.2f}",
                    inline=True
                )
                
                # Flow type distribution
                type_dist = analytics.get('flow_type_distribution', {})
                if type_dist:
                    dist_text = ""
                    flow_type_emojis = {
                        'linear': '➡️',
                        'branching': '🌳',
                        'circular': '🔄',
                        'convergent': '🎯',
                        'parallel': '⚡'
                    }
                    
                    for flow_type, count in sorted(type_dist.items(), key=lambda x: x[1], reverse=True):
                        emoji = flow_type_emojis.get(flow_type, '🔸')
                        dist_text += f"{emoji} {flow_type.title()}: {count}\n"
                    
                    embed.add_field(
                        name="🎭 Flow Type Distribution",
                        value=dist_text,
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting conversation flows: {e}")
            await interaction.followup.send("❌ Error retrieving conversation flow analysis")
    
    @app_commands.command(name="narrative_insights", description="Get narrative insights for the community")
    @app_commands.describe(period="Analysis period in days (default: 14)")
    async def narrative_insights(self, interaction: discord.Interaction, period: int = 14):
        """Get narrative insights for the community"""
        await interaction.response.defer()
        
        # Trigger loading animation
        if hasattr(self.bot, 'status_manager'):
            await self.bot.status_manager.trigger_loading_animation()
        
        try:
            guild_id = str(interaction.guild.id)
            
            # Get engagement summary
            engagement_summary = self.engagement_tracker.get_engagement_summary(guild_id, period)
            
            # Get conversation threads
            thread_summary = self.engagement_tracker.get_conversation_threads(guild_id)
            
            # Get flow analytics
            flow_analytics = self.conversation_mapper.get_flow_analytics(guild_id)
            
            # Create animated title
            animated_title = "🔍 Narrative Insights"
            if hasattr(self.bot, 'status_manager'):
                animated_title = await self.bot.status_manager.create_animated_embed_title(
                    "Narrative Insights", 'search'
                )
            
            embed = create_embed(
                animated_title,
                f"Deep analysis of community narratives over {period} days",
                discord.Color.gold()
            )
            
            # Narrative activity overview
            if 'error' not in engagement_summary:
                embed.add_field(
                    name="📚 Narrative Activity",
                    value=f"**Engagement Events:** {engagement_summary['engagement_events']}\n"
                          f"**Active Threads:** {thread_summary.get('total_active_threads', 0)}\n"
                          f"**Conversation Flows:** {flow_analytics.get('total_completed_flows', 0)}",
                    inline=True
                )
            
            # Storytelling insights
            if 'top_storytellers' in engagement_summary and engagement_summary['top_storytellers']:
                top_storyteller_id = engagement_summary['top_storytellers'][0][0]
                top_score = engagement_summary['top_storytellers'][0][1]
                
                try:
                    top_user = await self.bot.fetch_user(int(top_storyteller_id))
                    storyteller_name = top_user.display_name
                except:
                    storyteller_name = f"User {top_storyteller_id}"
                
                embed.add_field(
                    name="🎭 Storytelling Champion",
                    value=f"**{storyteller_name}**\n"
                          f"Engagement Score: {top_score:.1f}\n"
                          f"Total Storytellers: {len(engagement_summary['top_storytellers'])}",
                    inline=True
                )
            
            # Flow complexity insights
            if flow_analytics.get('flow_type_distribution'):
                complex_flows = sum(
                    count for flow_type, count in flow_analytics['flow_type_distribution'].items()
                    if flow_type in ['branching', 'circular', 'convergent']
                )
                total_flows = sum(flow_analytics['flow_type_distribution'].values())
                
                complexity_ratio = complex_flows / total_flows if total_flows > 0 else 0
                
                embed.add_field(
                    name="🧠 Conversation Complexity",
                    value=f"**Complex Flows:** {complex_flows}/{total_flows}\n"
                          f"**Complexity Ratio:** {complexity_ratio:.1%}\n"
                          f"**Avg Coherence:** {flow_analytics.get('average_narrative_coherence', 0):.2f}",
                    inline=True
                )
            
            # Community mood trends
            if 'community_mood' in engagement_summary and engagement_summary['community_mood']:
                mood_data = engagement_summary['community_mood']
                total_mood_events = sum(mood_data.values())
                dominant_mood = max(mood_data.items(), key=lambda x: x[1])
                
                embed.add_field(
                    name="🌈 Community Mood Analysis",
                    value=f"**Dominant Mood:** {dominant_mood[0].title()}\n"
                          f"**Mood Diversity:** {len(mood_data)} different moods\n"
                          f"**Total Mood Events:** {total_mood_events}",
                    inline=False
                )
            
            # Narrative theme insights
            if 'top_narrative_themes' in engagement_summary and engagement_summary['top_narrative_themes']:
                themes = engagement_summary['top_narrative_themes']
                
                insights = []
                if any(theme[0] == 'story_start' for theme in themes):
                    insights.append("📖 Strong storytelling culture")
                if any(theme[0] == 'community_building' for theme in themes):
                    insights.append("🏗️ Active community building")
                if any(theme[0] == 'support' for theme in themes):
                    insights.append("🤝 Supportive environment")
                if any(theme[0] == 'questions' for theme in themes):
                    insights.append("❓ Curious and engaging")
                
                if insights:
                    embed.add_field(
                        name="💡 Community Characteristics",
                        value="\n".join(insights),
                        inline=False
                    )
            
            # Recommendations
            recommendations = []
            
            if flow_analytics.get('average_engagement_intensity', 0) < 0.3:
                recommendations.append("💡 Consider hosting more interactive events")
            
            if flow_analytics.get('average_narrative_coherence', 0) < 0.4:
                recommendations.append("💡 Encourage topic-focused discussions")
            
            if thread_summary.get('total_active_threads', 0) < 3:
                recommendations.append("💡 Start conversation threads with questions")
            
            if recommendations:
                embed.add_field(
                    name="🚀 Growth Recommendations",
                    value="\n".join(recommendations),
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting narrative insights: {e}")
            await interaction.followup.send("❌ Error retrieving narrative insights")
    
    @app_commands.command(name="engagement_leaderboard", description="View engagement leaderboard")
    @app_commands.describe(category="Category to rank by")
    @app_commands.choices(category=[
        app_commands.Choice(name="📊 Overall Engagement", value="engagement"),
        app_commands.Choice(name="🎭 Storytelling", value="storytelling"),
        app_commands.Choice(name="💬 Conversation Starters", value="starters"),
        app_commands.Choice(name="🔄 Flow Participation", value="participation")
    ])
    async def engagement_leaderboard(self, interaction: discord.Interaction, category: str = "engagement"):
        """View engagement leaderboard"""
        await interaction.response.defer()
        
        # Trigger celebration animation
        if hasattr(self.bot, 'status_manager'):
            await self.bot.status_manager.trigger_celebration_animation()
        
        try:
            guild_id = str(interaction.guild.id)
            
            # Get engagement data
            engagement_data = self.engagement_tracker.engagement_data.get(guild_id, {})
            users_data = engagement_data.get('users', {})
            
            if not users_data:
                embed = create_embed(
                    "🏆 Engagement Leaderboard",
                    "No engagement data available yet",
                    discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create animated title
            animated_title = "🏆 Engagement Leaderboard"
            if hasattr(self.bot, 'status_manager'):
                animated_title = await self.bot.status_manager.create_animated_embed_title(
                    "Engagement Leaderboard", 'celebration'
                )
            
            # Sort users based on category
            if category == "engagement":
                sorted_users = sorted(users_data.items(), key=lambda x: x[1]['engagement_score'], reverse=True)
                metric_name = "Engagement Score"
                metric_key = "engagement_score"
            elif category == "storytelling":
                sorted_users = sorted(users_data.items(), key=lambda x: x[1]['narrative_contributions'], reverse=True)
                metric_name = "Narrative Contributions"
                metric_key = "narrative_contributions"
            elif category == "starters":
                # This would need additional tracking, for now use engagement score
                sorted_users = sorted(users_data.items(), key=lambda x: x[1]['engagement_score'], reverse=True)
                metric_name = "Conversation Impact"
                metric_key = "engagement_score"
            else:  # participation
                sorted_users = sorted(users_data.items(), key=lambda x: x[1]['messages'], reverse=True)
                metric_name = "Messages Sent"
                metric_key = "messages"
            
            embed = create_embed(
                animated_title,
                f"Top community members by {metric_name.lower()}",
                discord.Color.gold()
            )
            
            # Top 10 users
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅"]
            
            for i, (user_id, user_data) in enumerate(sorted_users[:10]):
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    display_name = user.display_name
                except:
                    display_name = f"User {user_id}"
                
                medal = medals[i] if i < len(medals) else "🔸"
                score = user_data[metric_key]
                
                leaderboard_text += f"{medal} **{display_name}**: {score:.1f}\n"
            
            embed.add_field(
                name=f"🏆 Top 10 by {metric_name}",
                value=leaderboard_text,
                inline=False
            )
            
            # Additional stats
            total_users = len(users_data)
            total_engagement = sum(user_data['engagement_score'] for user_data in users_data.values())
            avg_engagement = total_engagement / total_users if total_users > 0 else 0
            
            embed.add_field(
                name="📊 Community Statistics",
                value=f"**Total Active Users:** {total_users}\n"
                      f"**Average Engagement:** {avg_engagement:.1f}\n"
                      f"**Total Community Score:** {total_engagement:.1f}",
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting engagement leaderboard: {e}")
            await interaction.followup.send("❌ Error retrieving engagement leaderboard")

async def setup(bot):
    await bot.add_cog(EngagementAnalyticsCog(bot))