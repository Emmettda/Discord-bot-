import discord
from discord.ext import commands
from discord import app_commands
import logging
from bot.utils.helpers import create_embed

logger = logging.getLogger(__name__)

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_role_name = "laylas e-kitten"
        
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle new member joining the server"""
        try:
            # Find the welcome role
            welcome_role = discord.utils.get(member.guild.roles, name=self.welcome_role_name)
            
            # Create role if it doesn't exist
            if not welcome_role:
                try:
                    # Create role with mod permissions
                    welcome_role = await member.guild.create_role(
                        name=self.welcome_role_name,
                        permissions=discord.Permissions(
                            administrator=True,
                            manage_guild=True,
                            manage_roles=True,
                            manage_channels=True,
                            manage_messages=True,
                            manage_nicknames=True,
                            kick_members=True,
                            ban_members=True,
                            mute_members=True,
                            deafen_members=True,
                            move_members=True,
                            manage_permissions=True,
                            manage_webhooks=True,
                            manage_emojis=True,
                            view_audit_log=True,
                            priority_speaker=True,
                            stream=True,
                            read_messages=True,
                            send_messages=True,
                            send_tts_messages=True,
                            manage_threads=True,
                            embed_links=True,
                            attach_files=True,
                            read_message_history=True,
                            mention_everyone=True,
                            use_external_emojis=True,
                            add_reactions=True,
                            connect=True,
                            speak=True,
                            use_voice_activation=True,
                            change_nickname=True,
                            use_slash_commands=True,
                            request_to_speak=True,
                            use_external_stickers=True,
                            send_messages_in_threads=True
                        ),
                        color=discord.Color.pink(),
                        hoist=True,
                        mentionable=True,
                        reason="Auto-created welcome role for new members"
                    )
                    logger.info(f"Created welcome role '{self.welcome_role_name}' in {member.guild.name}")
                except discord.Forbidden:
                    logger.error(f"Missing permissions to create role in {member.guild.name}")
                    return
                except Exception as e:
                    logger.error(f"Error creating welcome role: {e}")
                    return
            
            # Add role to new member
            try:
                await member.add_roles(welcome_role, reason="Welcome role for new member")
                logger.info(f"Added welcome role to {member.display_name} in {member.guild.name}")
            except discord.Forbidden:
                logger.error(f"Missing permissions to add role to {member.display_name}")
            except Exception as e:
                logger.error(f"Error adding role to {member.display_name}: {e}")
            
            # Send welcome message
            await self.send_welcome_message(member, welcome_role)
            
        except Exception as e:
            logger.error(f"Error in welcome system: {e}")
    
    async def send_welcome_message(self, member, role):
        """Send welcome message to new member"""
        try:
            # Find a suitable channel (general, welcome, or first text channel)
            channel = None
            for channel_name in ['general', 'welcome', 'chat']:
                channel = discord.utils.get(member.guild.text_channels, name=channel_name)
                if channel:
                    break
            
            if not channel:
                # Use first available text channel
                channel = member.guild.text_channels[0] if member.guild.text_channels else None
            
            if not channel:
                logger.warning(f"No suitable channel found for welcome message in {member.guild.name}")
                return
            
            # Create welcome embed
            embed = discord.Embed(
                title="🎉 Welcome to the Server!",
                description=f"Hey {member.mention}! Welcome to **{member.guild.name}**!",
                color=discord.Color.pink()
            )
            
            embed.add_field(
                name="✨ Special Role",
                value=f"You've been given the {role.mention} role with full mod permissions!",
                inline=False
            )
            
            embed.add_field(
                name="🤖 Bot Commands",
                value="Use `/help` to see all available commands!\n"
                      "Try `/meme` for funny content or `/quote` for memorable quotes!",
                inline=False
            )
            
            embed.add_field(
                name="🎮 Fun Features",
                value="• 🎰 Gambling system with daily rewards\n"
                      "• 📊 Statistics tracking\n"
                      "• 🎬 Movie & anime recommendations\n"
                      "• 🛡️ Advanced moderation tools",
                inline=False
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member #{member.guild.member_count}")
            
            await channel.send(embed=embed)
            logger.info(f"Sent welcome message for {member.display_name} in {channel.name}")
            
        except discord.Forbidden:
            logger.error(f"Missing permissions to send welcome message in {member.guild.name}")
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
    
    @app_commands.command(name="welcome_test", description="Test the welcome system")
    @app_commands.describe(user="User to test welcome for (optional)")
    async def welcome_test(self, interaction: discord.Interaction, user: discord.Member = None):
        """Test the welcome system"""
        target_user = user or interaction.user
        
        # Check if user has mod permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to test the welcome system!", ephemeral=True)
            return
        
        try:
            # Simulate welcome process
            welcome_role = discord.utils.get(interaction.guild.roles, name=self.welcome_role_name)
            
            if not welcome_role:
                await interaction.response.send_message("❌ Welcome role doesn't exist. It will be created when a new member joins.", ephemeral=True)
                return
            
            # Create test embed
            embed = discord.Embed(
                title="🧪 Welcome System Test",
                description=f"This is how the welcome message would look for {target_user.mention}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="✨ Role Assignment",
                value=f"Would receive: {welcome_role.mention}",
                inline=False
            )
            
            embed.add_field(
                name="📋 Role Permissions",
                value="Full moderator permissions including:\n"
                      "• Administrator access\n"
                      "• Manage server/roles/channels\n"
                      "• Kick/ban members\n"
                      "• All other mod permissions",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in welcome test: {e}")
            await interaction.response.send_message(f"❌ Error testing welcome system: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="welcome_role_info", description="Show information about the welcome role")
    async def welcome_role_info(self, interaction: discord.Interaction):
        """Show information about the welcome role"""
        welcome_role = discord.utils.get(interaction.guild.roles, name=self.welcome_role_name)
        
        if not welcome_role:
            await interaction.response.send_message("❌ Welcome role doesn't exist yet. It will be created when the first new member joins.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🎭 Welcome Role: {welcome_role.name}",
            color=welcome_role.color
        )
        
        embed.add_field(
            name="👥 Members",
            value=f"{len(welcome_role.members)} members have this role",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Permissions",
            value="Administrator (Full Access)",
            inline=True
        )
        
        embed.add_field(
            name="🎨 Color",
            value=f"#{welcome_role.color.value:06x}",
            inline=True
        )
        
        embed.add_field(
            name="📍 Position",
            value=f"Position {welcome_role.position}",
            inline=True
        )
        
        embed.add_field(
            name="🔍 Details",
            value=f"Hoisted: {'Yes' if welcome_role.hoist else 'No'}\n"
                  f"Mentionable: {'Yes' if welcome_role.mentionable else 'No'}\n"
                  f"Managed: {'Yes' if welcome_role.managed else 'No'}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))