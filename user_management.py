import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class UserManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="set_favorite_character", description="Set your favorite character")
    @app_commands.describe(character_name="Name of your favorite character", anime_source="Anime/game/movie the character is from")
    async def set_favorite_character(self, interaction: discord.Interaction, character_name: str, anime_source: str = ""):
        """Set user's favorite character"""
        try:
            user_id = interaction.user.id
            character_data = {
                "character_name": character_name,
                "anime_source": anime_source,
                "set_date": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            # Save to database
            self.bot.db.set_favorite_character(user_id, character_data)
            
            embed = discord.Embed(
                title="✅ Favorite Character Set",
                description=f"Your favorite character has been set!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="👤 Character",
                value=character_name,
                inline=True
            )
            
            if anime_source:
                embed.add_field(
                    name="📺 Source",
                    value=anime_source,
                    inline=True
                )
            
            embed.set_footer(text="Use /get_favorite_character to view someone's favorite!")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error setting favorite character: {e}")
            await interaction.response.send_message(f"❌ Error setting favorite character: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="get_favorite_character", description="Get someone's favorite character")
    @app_commands.describe(user="User to check favorite character for (optional)")
    async def get_favorite_character(self, interaction: discord.Interaction, user: discord.Member = None):
        """Get user's favorite character"""
        try:
            target_user = user or interaction.user
            character_data = self.bot.db.get_favorite_character(target_user.id)
            
            if not character_data:
                if target_user == interaction.user:
                    message = "You haven't set a favorite character yet! Use `/set_favorite_character` to set one."
                else:
                    message = f"{target_user.mention} hasn't set a favorite character yet."
                
                await interaction.response.send_message(message, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"💖 {target_user.display_name}'s Favorite Character",
                color=discord.Color.pink()
            )
            
            embed.add_field(
                name="👤 Character",
                value=character_data['character_name'],
                inline=True
            )
            
            if character_data.get('anime_source'):
                embed.add_field(
                    name="📺 Source",
                    value=character_data['anime_source'],
                    inline=True
                )
            
            embed.add_field(
                name="📅 Set Date",
                value=character_data['set_date'][:10],
                inline=True
            )
            
            embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting favorite character: {e}")
            await interaction.response.send_message(f"❌ Error getting favorite character: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="nickname", description="Change a user's nickname")
    @app_commands.describe(user="User to change nickname for", new_nickname="New nickname (leave empty to reset)")
    async def nickname(self, interaction: discord.Interaction, user: discord.Member, new_nickname: str = ""):
        """Change a user's nickname"""
        # Check permissions
        if not interaction.user.guild_permissions.manage_nicknames:
            await interaction.response.send_message("❌ You don't have permission to manage nicknames.", ephemeral=True)
            return
        
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot change the nickname of someone with a higher or equal role.", ephemeral=True)
            return
        
        try:
            old_nickname = user.display_name
            
            # Set new nickname (empty string resets to username)
            await user.edit(nick=new_nickname if new_nickname else None)
            
            embed = discord.Embed(
                title="✅ Nickname Changed",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="👤 User",
                value=user.mention,
                inline=True
            )
            
            embed.add_field(
                name="📝 Old Nickname",
                value=old_nickname,
                inline=True
            )
            
            embed.add_field(
                name="📝 New Nickname",
                value=new_nickname if new_nickname else user.name,
                inline=True
            )
            
            embed.add_field(
                name="👮 Changed By",
                value=interaction.user.mention,
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Nickname changed for {user} by {interaction.user}: {old_nickname} -> {new_nickname}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to change this user's nickname.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error changing nickname: {e}")
            await interaction.response.send_message(f"❌ Error changing nickname: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="user_info", description="Get information about a user")
    @app_commands.describe(user="User to get information about (optional)")
    async def user_info(self, interaction: discord.Interaction, user: discord.Member = None):
        """Get detailed information about a user"""
        try:
            target_user = user or interaction.user
            
            embed = discord.Embed(
                title=f"👤 User Information: {target_user.display_name}",
                color=target_user.color if target_user.color != discord.Color.default() else discord.Color.blue()
            )
            
            # Set user avatar
            if target_user.avatar:
                embed.set_thumbnail(url=target_user.avatar.url)
            
            # Basic user info
            embed.add_field(
                name="🏷️ Username",
                value=target_user.name,
                inline=True
            )
            
            embed.add_field(
                name="🔢 Discriminator",
                value=f"#{target_user.discriminator}",
                inline=True
            )
            
            embed.add_field(
                name="🆔 User ID",
                value=target_user.id,
                inline=True
            )
            
            # Join dates
            embed.add_field(
                name="📅 Account Created",
                value=target_user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                inline=True
            )
            
            embed.add_field(
                name="📅 Joined Server",
                value=target_user.joined_at.strftime("%Y-%m-%d %H:%M:%S") if target_user.joined_at else "Unknown",
                inline=True
            )
            
            # Status and activity
            embed.add_field(
                name="🟢 Status",
                value=str(target_user.status).title(),
                inline=True
            )
            
            # Roles
            if target_user.roles[1:]:  # Exclude @everyone role
                roles = ", ".join([role.name for role in target_user.roles[1:]])
                embed.add_field(
                    name="🎭 Roles",
                    value=roles[:1024],  # Discord embed field limit
                    inline=False
                )
            
            # Permissions
            if target_user.guild_permissions.administrator:
                embed.add_field(
                    name="🛡️ Permissions",
                    value="Administrator",
                    inline=True
                )
            elif target_user.guild_permissions.manage_guild:
                embed.add_field(
                    name="🛡️ Permissions",
                    value="Manage Server",
                    inline=True
                )
            elif target_user.guild_permissions.manage_messages:
                embed.add_field(
                    name="🛡️ Permissions",
                    value="Manage Messages",
                    inline=True
                )
            
            # Get user's favorite character if set
            character_data = self.bot.db.get_favorite_character(target_user.id)
            if character_data:
                embed.add_field(
                    name="💖 Favorite Character",
                    value=f"{character_data['character_name']}" + 
                          (f" ({character_data['anime_source']})" if character_data.get('anime_source') else ""),
                    inline=True
                )
            
            # Get warning count
            warnings = self.bot.db.get_warnings(target_user.id, interaction.guild.id)
            embed.add_field(
                name="⚠️ Warnings",
                value=str(len(warnings)),
                inline=True
            )
            
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            await interaction.response.send_message(f"❌ Error getting user information: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(user="User to get avatar for (optional)")
    async def avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        """Get a user's avatar"""
        try:
            target_user = user or interaction.user
            
            if not target_user.avatar:
                await interaction.response.send_message(f"{target_user.mention} doesn't have a custom avatar.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🖼️ {target_user.display_name}'s Avatar",
                color=target_user.color if target_user.color != discord.Color.default() else discord.Color.blue()
            )
            
            embed.set_image(url=target_user.avatar.url)
            embed.add_field(
                name="🔗 Avatar URL",
                value=f"[Click here]({target_user.avatar.url})",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting avatar: {e}")
            await interaction.response.send_message(f"❌ Error getting avatar: {str(e)}", ephemeral=True)
