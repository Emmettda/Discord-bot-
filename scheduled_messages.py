import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

class ScheduledMessagesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.scheduled_messages_file = os.path.join(self.data_dir, "scheduled_messages.json")
        self.farewell_settings_file = os.path.join(self.data_dir, "farewell_settings.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files
        self._init_file(self.scheduled_messages_file, {"messages": []})
        self._init_file(self.farewell_settings_file, {})
        
        # Start the scheduler task
        self.message_scheduler.start()

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

    @tasks.loop(minutes=1)
    async def message_scheduler(self):
        """Check for scheduled messages to send"""
        try:
            scheduled_data = self._read_json(self.scheduled_messages_file)
            messages = scheduled_data.get("messages", [])
            current_time = datetime.now()
            
            messages_to_send = []
            remaining_messages = []
            
            for message_data in messages:
                scheduled_time = datetime.fromisoformat(message_data["scheduled_time"])
                
                if current_time >= scheduled_time:
                    messages_to_send.append(message_data)
                else:
                    remaining_messages.append(message_data)
            
            # Send due messages
            for message_data in messages_to_send:
                try:
                    channel = self.bot.get_channel(message_data["channel_id"])
                    if channel:
                        if message_data.get("embed"):
                            embed_data = message_data["embed"]
                            embed = discord.Embed(
                                title=embed_data.get("title", ""),
                                description=embed_data.get("description", ""),
                                color=embed_data.get("color", 0x00ff00)
                            )
                            await channel.send(embed=embed)
                        else:
                            await channel.send(message_data["content"])
                        
                        logger.info(f"Sent scheduled message in {channel.name}")
                except Exception as e:
                    logger.error(f"Error sending scheduled message: {e}")
            
            # Update the file with remaining messages
            if len(remaining_messages) != len(messages):
                scheduled_data["messages"] = remaining_messages
                self._write_json(self.scheduled_messages_file, scheduled_data)
                
        except Exception as e:
            logger.error(f"Error in message scheduler: {e}")

    @message_scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="schedule_message", description="Schedule a message to be sent at a specific time")
    @app_commands.describe(
        channel="Channel to send the message to",
        message="Message content",
        time_minutes="Minutes from now to send (or use datetime for specific time)",
        title="Optional embed title",
        description="Optional embed description"
    )
    async def schedule_message(self, interaction: discord.Interaction, 
                             channel: discord.TextChannel, 
                             message: str,
                             time_minutes: int = None,
                             title: str = None,
                             description: str = None):
        """Schedule a message to be sent later"""
        
        # Check permissions
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need 'Manage Messages' permissions to schedule messages!", ephemeral=True)
            return
        
        if time_minutes is None:
            await interaction.response.send_message("❌ Please specify when to send the message (in minutes from now)!", ephemeral=True)
            return
        
        if time_minutes < 1 or time_minutes > 10080:  # Max 1 week
            await interaction.response.send_message("❌ Time must be between 1 minute and 1 week (10080 minutes)!", ephemeral=True)
            return
        
        # Calculate scheduled time
        scheduled_time = datetime.now() + timedelta(minutes=time_minutes)
        
        # Prepare message data
        message_data = {
            "id": f"{interaction.guild.id}_{int(scheduled_time.timestamp())}",
            "guild_id": interaction.guild.id,
            "channel_id": channel.id,
            "author_id": interaction.user.id,
            "content": message,
            "scheduled_time": scheduled_time.isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        # Add embed data if provided
        if title or description:
            message_data["embed"] = {
                "title": title or "",
                "description": description or message,
                "color": 0x00ff00
            }
            message_data["content"] = ""  # Use embed instead of plain content
        
        # Save to file
        scheduled_data = self._read_json(self.scheduled_messages_file)
        scheduled_data["messages"].append(message_data)
        self._write_json(self.scheduled_messages_file, scheduled_data)
        
        # Send confirmation
        embed = discord.Embed(
            title="📅 Message Scheduled",
            description=f"Your message will be sent to {channel.mention}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="⏰ Scheduled Time",
            value=f"<t:{int(scheduled_time.timestamp())}:F>\n(<t:{int(scheduled_time.timestamp())}:R>)",
            inline=False
        )
        
        if title or description:
            embed.add_field(
                name="📋 Content",
                value=f"**Title:** {title or 'None'}\n**Description:** {description or message}",
                inline=False
            )
        else:
            embed.add_field(
                name="📋 Content",
                value=message[:500] + ("..." if len(message) > 500 else ""),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list_scheduled", description="View all scheduled messages")
    async def list_scheduled(self, interaction: discord.Interaction):
        """List all scheduled messages for this server"""
        
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need 'Manage Messages' permissions to view scheduled messages!", ephemeral=True)
            return
        
        scheduled_data = self._read_json(self.scheduled_messages_file)
        messages = [msg for msg in scheduled_data.get("messages", []) if msg["guild_id"] == interaction.guild.id]
        
        if not messages:
            await interaction.response.send_message("📅 No scheduled messages for this server.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📅 Scheduled Messages",
            description=f"Found {len(messages)} scheduled messages",
            color=discord.Color.blue()
        )
        
        for i, message_data in enumerate(messages[:10], 1):  # Show max 10
            channel = self.bot.get_channel(message_data["channel_id"])
            author = self.bot.get_user(message_data["author_id"])
            scheduled_time = datetime.fromisoformat(message_data["scheduled_time"])
            
            content_preview = message_data.get("content", "")
            if message_data.get("embed"):
                content_preview = f"Embed: {message_data['embed'].get('title', 'No title')}"
            
            embed.add_field(
                name=f"{i}. {channel.name if channel else 'Unknown Channel'}",
                value=f"**Content:** {content_preview[:100]}...\n"
                      f"**Author:** {author.display_name if author else 'Unknown'}\n"
                      f"**Time:** <t:{int(scheduled_time.timestamp())}:R>",
                inline=False
            )
        
        if len(messages) > 10:
            embed.set_footer(text=f"Showing 10 of {len(messages)} messages")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setup_farewell", description="Setup farewell messages when members leave")
    @app_commands.describe(
        channel="Channel to send farewell messages",
        message="Farewell message (use {user} for username, {server} for server name)",
        enabled="Enable or disable farewell messages"
    )
    async def setup_farewell(self, interaction: discord.Interaction,
                           channel: discord.TextChannel = None,
                           message: str = None,
                           enabled: bool = True):
        """Setup farewell messages for when members leave"""
        
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permissions to setup farewell messages!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        farewell_data = self._read_json(self.farewell_settings_file)
        
        if guild_id not in farewell_data:
            farewell_data[guild_id] = {}
        
        # Update settings
        if channel:
            farewell_data[guild_id]["channel_id"] = channel.id
        if message:
            farewell_data[guild_id]["message"] = message
        farewell_data[guild_id]["enabled"] = enabled
        
        self._write_json(self.farewell_settings_file, farewell_data)
        
        # Create response embed
        embed = discord.Embed(
            title="👋 Farewell Setup",
            color=discord.Color.orange() if enabled else discord.Color.red()
        )
        
        current_settings = farewell_data[guild_id]
        farewell_channel = self.bot.get_channel(current_settings.get("channel_id"))
        
        embed.add_field(
            name="Status",
            value="✅ Enabled" if enabled else "❌ Disabled",
            inline=True
        )
        
        embed.add_field(
            name="Channel",
            value=farewell_channel.mention if farewell_channel else "Not set",
            inline=True
        )
        
        embed.add_field(
            name="Message",
            value=current_settings.get("message", "Not set")[:100],
            inline=False
        )
        
        if enabled and farewell_channel and current_settings.get("message"):
            embed.description = "Farewell messages are now active!"
        else:
            embed.description = "⚠️ Please set both channel and message to activate farewell messages."
        
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle member leaving for farewell messages"""
        try:
            guild_id = str(member.guild.id)
            farewell_data = self._read_json(self.farewell_settings_file)
            
            if guild_id not in farewell_data:
                return
            
            settings = farewell_data[guild_id]
            if not settings.get("enabled", False):
                return
            
            channel_id = settings.get("channel_id")
            message_template = settings.get("message")
            
            if not channel_id or not message_template:
                return
            
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return
            
            # Format the farewell message
            farewell_message = message_template.format(
                user=member.display_name,
                username=member.name,
                server=member.guild.name,
                mention=member.mention
            )
            
            # Create farewell embed
            embed = discord.Embed(
                title="👋 Farewell",
                description=farewell_message,
                color=discord.Color.orange()
            )
            
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            
            embed.add_field(
                name="Member Info",
                value=f"**Username:** {member.name}\n"
                      f"**Joined:** <t:{int(member.joined_at.timestamp())}:D>\n"
                      f"**Left:** <t:{int(datetime.now().timestamp())}:F>",
                inline=False
            )
            
            embed.set_footer(text=f"We now have {member.guild.member_count} members")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error sending farewell message: {e}")

    @app_commands.command(name="test_farewell", description="Test the farewell message system")
    async def test_farewell(self, interaction: discord.Interaction):
        """Test farewell message with current user"""
        
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permissions to test farewell messages!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        farewell_data = self._read_json(self.farewell_settings_file)
        
        if guild_id not in farewell_data or not farewell_data[guild_id].get("enabled"):
            await interaction.response.send_message("❌ Farewell messages are not enabled for this server!", ephemeral=True)
            return
        
        settings = farewell_data[guild_id]
        channel_id = settings.get("channel_id")
        message_template = settings.get("message", "Goodbye {user}!")
        
        if not channel_id:
            await interaction.response.send_message("❌ No farewell channel is set!", ephemeral=True)
            return
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("❌ Farewell channel not found!", ephemeral=True)
            return
        
        # Format test message
        test_message = message_template.format(
            user=interaction.user.display_name,
            username=interaction.user.name,
            server=interaction.guild.name,
            mention=interaction.user.mention
        )
        
        # Create test embed
        embed = discord.Embed(
            title="👋 Farewell (TEST)",
            description=test_message,
            color=discord.Color.orange()
        )
        
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)
        
        embed.add_field(
            name="Member Info",
            value=f"**Username:** {interaction.user.name}\n"
                  f"**Joined:** <t:{int(interaction.user.joined_at.timestamp())}:D>\n"
                  f"**Left:** <t:{int(datetime.now().timestamp())}:F>",
            inline=False
        )
        
        embed.set_footer(text=f"This is a test message • Server has {interaction.guild.member_count} members")
        
        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Test farewell message sent to {channel.mention}!", ephemeral=True)

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.message_scheduler.cancel()

async def setup(bot):
    await bot.add_cog(ScheduledMessagesCog(bot))