import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime, timedelta
import asyncio
from bot.utils.auto_moderation import AutoModerationSystem

logger = logging.getLogger(__name__)

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muted_users = {}  # Store muted users temporarily
        self.auto_mod = AutoModerationSystem(bot)
    
    def has_mod_permissions():
        """Check if user has moderation permissions"""
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.manage_messages
        return app_commands.check(predicate)
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(user="The user to kick", reason="Reason for kicking")
    @has_mod_permissions()
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Kick a user from the server"""
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot kick someone with a higher or equal role.", ephemeral=True)
            return
        
        if user == interaction.user:
            await interaction.response.send_message("❌ You cannot kick yourself.", ephemeral=True)
            return
        
        try:
            await user.kick(reason=reason)
            
            # Log the action
            embed = discord.Embed(
                title="✅ User Kicked",
                description=f"**User:** {user.mention}\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {user} kicked by {interaction.user} for: {reason}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error kicking user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(user="The user to ban", reason="Reason for banning", delete_days="Days of messages to delete (0-7)")
    @has_mod_permissions()
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
        """Ban a user from the server"""
        if delete_days < 0 or delete_days > 7:
            await interaction.response.send_message("❌ Delete days must be between 0 and 7.", ephemeral=True)
            return
        
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot ban someone with a higher or equal role.", ephemeral=True)
            return
        
        if user == interaction.user:
            await interaction.response.send_message("❌ You cannot ban yourself.", ephemeral=True)
            return
        
        try:
            await user.ban(reason=reason, delete_message_days=delete_days)
            
            # Log the action
            embed = discord.Embed(
                title="🔨 User Banned",
                description=f"**User:** {user.mention}\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {user} banned by {interaction.user} for: {reason}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error banning user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(user_id="The ID of the user to unban")
    @has_mod_permissions()
    async def unban(self, interaction: discord.Interaction, user_id: str):
        """Unban a user from the server"""
        try:
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)
            
            await interaction.guild.unban(user)
            
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"**User:** {user.mention}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {user} unbanned by {interaction.user}")
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID provided.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found or not banned.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unbanning user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="mute", description="Mute a user for a specified duration")
    @app_commands.describe(user="The user to mute", duration="Duration in minutes", reason="Reason for muting")
    @has_mod_permissions()
    async def mute(self, interaction: discord.Interaction, user: discord.Member, duration: int = 60, reason: str = "No reason provided"):
        """Mute a user for a specified duration"""
        if duration <= 0:
            await interaction.response.send_message("❌ Duration must be positive.", ephemeral=True)
            return
        
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot mute someone with a higher or equal role.", ephemeral=True)
            return
        
        try:
            # Calculate unmute time
            unmute_time = datetime.utcnow() + timedelta(minutes=duration)
            
            # Apply timeout (Discord's built-in mute)
            await user.timeout(unmute_time, reason=reason)
            
            embed = discord.Embed(
                title="🔇 User Muted",
                description=f"**User:** {user.mention}\n**Duration:** {duration} minutes\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {user} muted by {interaction.user} for {duration} minutes: {reason}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to mute this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error muting user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="unmute", description="Unmute a user")
    @app_commands.describe(user="The user to unmute")
    @has_mod_permissions()
    async def unmute(self, interaction: discord.Interaction, user: discord.Member):
        """Unmute a user"""
        try:
            await user.timeout(None)
            
            embed = discord.Embed(
                title="🔊 User Unmuted",
                description=f"**User:** {user.mention}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {user} unmuted by {interaction.user}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unmute this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unmuting user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(user="The user to warn", reason="Reason for warning")
    @has_mod_permissions()
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Warn a user"""
        try:
            # Add warning to database
            warning_data = {
                "user_id": user.id,
                "moderator_id": interaction.user.id,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
                "guild_id": interaction.guild.id
            }
            
            self.bot.db.add_warning(warning_data)
            
            embed = discord.Embed(
                title="⚠️ User Warned",
                description=f"**User:** {user.mention}\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"User {user} warned by {interaction.user}: {reason}")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error warning user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="warnings", description="View warnings for a user")
    @app_commands.describe(user="The user to check warnings for")
    @has_mod_permissions()
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        """View warnings for a user"""
        try:
            warnings = self.bot.db.get_warnings(user.id, interaction.guild.id)
            
            if not warnings:
                await interaction.response.send_message(f"ℹ️ {user.mention} has no warnings.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"⚠️ Warnings for {user.display_name}",
                color=discord.Color.yellow()
            )
            
            for i, warning in enumerate(warnings[-10:], 1):  # Show last 10 warnings
                moderator = self.bot.get_user(warning['moderator_id'])
                moderator_name = moderator.display_name if moderator else "Unknown"
                
                embed.add_field(
                    name=f"Warning {i}",
                    value=f"**Reason:** {warning['reason']}\n**Moderator:** {moderator_name}\n**Date:** {warning['timestamp'][:10]}",
                    inline=False
                )
            
            embed.set_footer(text=f"Total warnings: {len(warnings)}")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error retrieving warnings: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="clear", description="Clear messages in the channel")
    @app_commands.describe(amount="Number of messages to clear (1-100)")
    @has_mod_permissions()
    async def clear(self, interaction: discord.Interaction, amount: int = 10):
        """Clear messages in the channel"""
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100.", ephemeral=True)
            return
        
        try:
            await interaction.response.defer()
            
            deleted = await interaction.channel.purge(limit=amount)
            
            embed = discord.Embed(
                title="🧹 Messages Cleared",
                description=f"**Amount:** {len(deleted)} messages\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"{len(deleted)} messages cleared by {interaction.user}")
            
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to delete messages.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error clearing messages: {str(e)}", ephemeral=True)
    
    # Auto-moderation commands
    @app_commands.command(name="automod_toggle", description="Toggle auto-moderation on/off")
    @app_commands.describe(enabled="Enable or disable auto-moderation")
    @has_mod_permissions()
    async def automod_toggle(self, interaction: discord.Interaction, enabled: bool):
        """Toggle auto-moderation system"""
        try:
            settings = self.auto_mod.get_settings()
            settings['automod_enabled'] = enabled
            self.auto_mod.update_settings(settings)
            
            # Save to database
            self.bot.db.save_automod_settings(interaction.guild.id, settings)
            
            status = "enabled" if enabled else "disabled"
            embed = discord.Embed(
                title=f"🤖 Auto-Moderation {status.title()}",
                description=f"Auto-moderation has been {status} for this server.",
                color=discord.Color.green() if enabled else discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Auto-moderation {status} by {interaction.user} in {interaction.guild}")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error toggling auto-moderation: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="automod_settings", description="View and configure auto-moderation settings")
    @has_mod_permissions()
    async def automod_settings(self, interaction: discord.Interaction):
        """View auto-moderation settings"""
        try:
            settings = self.auto_mod.get_settings()
            
            embed = discord.Embed(
                title="🤖 Auto-Moderation Settings",
                description="Current configuration for auto-moderation system",
                color=discord.Color.blue()
            )
            
            # Status
            status = "✅ Enabled" if settings['automod_enabled'] else "❌ Disabled"
            embed.add_field(
                name="Status",
                value=status,
                inline=True
            )
            
            # Spam settings
            embed.add_field(
                name="🚫 Spam Detection",
                value=f"Threshold: {settings['spam_threshold']} messages\n"
                      f"Window: {settings['spam_window']} seconds\n"
                      f"Enabled: {'✅' if settings['spam_filter'] else '❌'}",
                inline=True
            )
            
            # Content filters
            filters = [
                f"Duplicate Messages: {'✅' if settings['duplicate_filter'] else '❌'}",
                f"Excessive Caps: {'✅' if settings['caps_filter'] else '❌'}",
                f"Suspicious Links: {'✅' if settings['link_filter'] else '❌'}",
                f"Discord Invites: {'✅' if settings['invite_filter'] else '❌'}",
                f"Excessive Mentions: {'✅' if settings['mention_filter'] else '❌'}",
                f"Excessive Emojis: {'✅' if settings['emoji_filter'] else '❌'}"
            ]
            
            embed.add_field(
                name="🛡️ Content Filters",
                value="\n".join(filters),
                inline=False
            )
            
            # Thresholds
            embed.add_field(
                name="⚖️ Thresholds",
                value=f"Caps Ratio: {settings['caps_threshold']*100:.0f}%\n"
                      f"Max Mentions: {settings['max_mentions']}\n"
                      f"Max Emojis: {settings['max_emojis']}\n"
                      f"Duplicate Count: {settings['duplicate_threshold']}",
                inline=True
            )
            
            embed.set_footer(text="Use /automod_configure to modify these settings")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error retrieving settings: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="automod_configure", description="Configure auto-moderation settings")
    @app_commands.describe(
        spam_filter="Enable/disable spam detection",
        duplicate_filter="Enable/disable duplicate message detection",
        caps_filter="Enable/disable excessive caps detection",
        link_filter="Enable/disable suspicious link detection",
        invite_filter="Enable/disable Discord invite detection",
        spam_threshold="Number of messages to trigger spam detection",
        caps_threshold="Percentage of caps to trigger filter (0.1-1.0)"
    )
    @has_mod_permissions()
    async def automod_configure(self, interaction: discord.Interaction,
                               spam_filter: bool = None,
                               duplicate_filter: bool = None,
                               caps_filter: bool = None,
                               link_filter: bool = None,
                               invite_filter: bool = None,
                               spam_threshold: int = None,
                               caps_threshold: float = None):
        """Configure auto-moderation settings"""
        try:
            settings = self.auto_mod.get_settings()
            changes = []
            
            # Update boolean settings
            if spam_filter is not None:
                settings['spam_filter'] = spam_filter
                changes.append(f"Spam filter: {'enabled' if spam_filter else 'disabled'}")
            
            if duplicate_filter is not None:
                settings['duplicate_filter'] = duplicate_filter
                changes.append(f"Duplicate filter: {'enabled' if duplicate_filter else 'disabled'}")
            
            if caps_filter is not None:
                settings['caps_filter'] = caps_filter
                changes.append(f"Caps filter: {'enabled' if caps_filter else 'disabled'}")
            
            if link_filter is not None:
                settings['link_filter'] = link_filter
                changes.append(f"Link filter: {'enabled' if link_filter else 'disabled'}")
            
            if invite_filter is not None:
                settings['invite_filter'] = invite_filter
                changes.append(f"Invite filter: {'enabled' if invite_filter else 'disabled'}")
            
            # Update threshold settings
            if spam_threshold is not None:
                if 2 <= spam_threshold <= 20:
                    settings['spam_threshold'] = spam_threshold
                    changes.append(f"Spam threshold: {spam_threshold}")
                else:
                    await interaction.response.send_message("❌ Spam threshold must be between 2 and 20", ephemeral=True)
                    return
            
            if caps_threshold is not None:
                if 0.1 <= caps_threshold <= 1.0:
                    settings['caps_threshold'] = caps_threshold
                    changes.append(f"Caps threshold: {caps_threshold*100:.0f}%")
                else:
                    await interaction.response.send_message("❌ Caps threshold must be between 0.1 and 1.0", ephemeral=True)
                    return
            
            if not changes:
                await interaction.response.send_message("❌ No settings were changed", ephemeral=True)
                return
            
            # Apply changes
            self.auto_mod.update_settings(settings)
            self.bot.db.save_automod_settings(interaction.guild.id, settings)
            
            embed = discord.Embed(
                title="✅ Auto-Moderation Settings Updated",
                description="The following settings have been changed:",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Changes Made",
                value="\n".join(f"• {change}" for change in changes),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Auto-mod settings updated by {interaction.user}: {changes}")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating settings: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="automod_stats", description="View auto-moderation statistics")
    @app_commands.describe(days="Number of days to look back (default: 30)")
    @has_mod_permissions()
    async def automod_stats(self, interaction: discord.Interaction, days: int = 30):
        """View auto-moderation statistics"""
        try:
            if days < 1 or days > 365:
                await interaction.response.send_message("❌ Days must be between 1 and 365", ephemeral=True)
                return
            
            stats = self.bot.db.get_automod_stats(interaction.guild.id, days)
            
            embed = discord.Embed(
                title="📊 Auto-Moderation Statistics",
                description=f"Statistics for the last {days} days",
                color=discord.Color.blue()
            )
            
            # Total violations
            embed.add_field(
                name="📈 Total Violations",
                value=str(stats['total_violations']),
                inline=True
            )
            
            # Violation types
            if stats['violation_types']:
                violation_list = []
                for v_type, count in sorted(stats['violation_types'].items(), key=lambda x: x[1], reverse=True):
                    violation_list.append(f"{v_type.replace('_', ' ').title()}: {count}")
                
                embed.add_field(
                    name="🔍 Violation Types",
                    value="\n".join(violation_list[:10]),  # Top 10
                    inline=True
                )
            
            # Top violators
            if stats['top_violators']:
                violator_list = []
                for user_id, count in stats['top_violators'][:5]:  # Top 5
                    try:
                        user = self.bot.get_user(user_id)
                        name = user.display_name if user else f"User {user_id}"
                        violator_list.append(f"{name}: {count}")
                    except:
                        violator_list.append(f"User {user_id}: {count}")
                
                embed.add_field(
                    name="⚠️ Top Violators",
                    value="\n".join(violator_list),
                    inline=True
                )
            
            if stats['total_violations'] == 0:
                embed.add_field(
                    name="🎉 Great News!",
                    value="No auto-moderation violations detected in the specified period.",
                    inline=False
                )
            
            embed.set_footer(text=f"Data from {interaction.guild.name}")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error retrieving statistics: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="automod_violations", description="View auto-moderation violations for a user")
    @app_commands.describe(user="User to check violations for", days="Number of days to look back")
    @has_mod_permissions()
    async def automod_violations(self, interaction: discord.Interaction, user: discord.Member, days: int = 30):
        """View auto-moderation violations for a specific user"""
        try:
            violations = self.bot.db.get_automod_violations(user.id, interaction.guild.id, days)
            
            if not violations:
                await interaction.response.send_message(f"ℹ️ {user.mention} has no auto-moderation violations in the last {days} days.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"⚠️ Auto-Mod Violations for {user.display_name}",
                description=f"Violations in the last {days} days: {len(violations)}",
                color=discord.Color.orange()
            )
            
            # Show recent violations
            recent_violations = violations[-10:]  # Last 10 violations
            
            for i, violation in enumerate(recent_violations, 1):
                violation_types = ", ".join(violation['violations'])
                timestamp = violation['timestamp'][:19]  # Remove microseconds
                
                embed.add_field(
                    name=f"Violation {i}",
                    value=f"**Type:** {violation_types}\n"
                          f"**Time:** {timestamp}\n"
                          f"**Message:** {violation['message_content'][:100]}...",
                    inline=False
                )
            
            embed.set_footer(text=f"Showing {len(recent_violations)} of {len(violations)} violations")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error retrieving violations: {str(e)}", ephemeral=True)
