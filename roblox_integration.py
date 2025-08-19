import discord
from discord.ext import commands
from discord import app_commands
import logging
import aiohttp
import json
import os
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class RobloxIntegrationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.roblox_users_file = os.path.join(self.data_dir, "roblox_users.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files
        self._init_file(self.roblox_users_file, {})
        
        # Roblox API endpoints
        self.roblox_api_base = "https://api.roblox.com"
        self.roblox_users_api = "https://users.roblox.com/v1"
        self.roblox_games_api = "https://games.roblox.com/v1"
        self.roblox_groups_api = "https://groups.roblox.com/v1"
        self.roblox_thumbnails_api = "https://thumbnails.roblox.com/v1"
        self.roblox_presence_api = "https://presence.roblox.com/v1"

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

    async def _make_roblox_request(self, url: str, headers: dict = None) -> dict:
        """Make a request to Roblox API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Roblox API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error making Roblox request: {e}")
            return None

    async def _get_user_by_username(self, username: str) -> dict:
        """Get Roblox user data by username"""
        url = f"{self.roblox_users_api}/usernames/users"
        data = {
            "usernames": [username]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("data") and len(result["data"]) > 0:
                            return result["data"][0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None

    async def _get_user_by_id(self, user_id: int) -> dict:
        """Get Roblox user data by ID"""
        url = f"{self.roblox_users_api}/users/{user_id}"
        return await self._make_roblox_request(url)

    async def _get_user_presence(self, user_id: int) -> dict:
        """Get user's current presence/game status"""
        url = f"{self.roblox_presence_api}/users/{user_id}/presence"
        return await self._make_roblox_request(url)

    async def _get_user_avatar(self, user_id: int) -> str:
        """Get user's avatar thumbnail URL"""
        url = f"{self.roblox_thumbnails_api}/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        data = await self._make_roblox_request(url)
        
        if data and data.get("data") and len(data["data"]) > 0:
            return data["data"][0].get("imageUrl")
        return None

    async def _get_user_games(self, user_id: int) -> list:
        """Get games created by user"""
        url = f"{self.roblox_games_api}/games?creator={user_id}&limit=50"
        data = await self._make_roblox_request(url)
        
        if data and data.get("data"):
            return data["data"]
        return []

    async def _get_group_info(self, group_id: int) -> dict:
        """Get group information"""
        url = f"{self.roblox_groups_api}/groups/{group_id}"
        return await self._make_roblox_request(url)

    async def _search_groups(self, query: str, limit: int = 10) -> list:
        """Search for groups"""
        url = f"{self.roblox_groups_api}/groups/search?keyword={query}&limit={limit}"
        data = await self._make_roblox_request(url)
        
        if data and data.get("data"):
            return data["data"]
        return []

    @app_commands.command(name="roblox_link", description="Link your Discord account to your Roblox account")
    @app_commands.describe(username="Your Roblox username")
    async def roblox_link(self, interaction: discord.Interaction, username: str):
        """Link Discord account to Roblox"""
        await interaction.response.defer()
        
        # Get Roblox user data
        user_data = await self._get_user_by_username(username)
        
        if not user_data:
            await interaction.followup.send(f"❌ Roblox user '{username}' not found!")
            return
        
        user_id = user_data["id"]
        display_name = user_data.get("displayName", username)
        
        # Save the link
        roblox_data = self._read_json(self.roblox_users_file)
        roblox_data[str(interaction.user.id)] = {
            "roblox_id": user_id,
            "roblox_username": username,
            "roblox_display_name": display_name,
            "linked_at": datetime.now().isoformat()
        }
        self._write_json(self.roblox_users_file, roblox_data)
        
        # Get avatar
        avatar_url = await self._get_user_avatar(user_id)
        
        embed = discord.Embed(
            title="🔗 Roblox Account Linked",
            description=f"Successfully linked to Roblox account **{display_name}** (@{username})",
            color=discord.Color.green()
        )
        
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        
        embed.add_field(
            name="📊 Account Info",
            value=f"**Username:** {username}\n"
                  f"**Display Name:** {display_name}\n"
                  f"**User ID:** {user_id}",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="roblox_profile", description="View Roblox profile information")
    @app_commands.describe(username="Roblox username (optional, uses your linked account if not provided)")
    async def roblox_profile(self, interaction: discord.Interaction, username: str = None):
        """View Roblox profile"""
        await interaction.response.defer()
        
        user_data = None
        
        if username:
            # Search by provided username
            user_data = await self._get_user_by_username(username)
            if not user_data:
                await interaction.followup.send(f"❌ Roblox user '{username}' not found!")
                return
        else:
            # Use linked account
            roblox_data = self._read_json(self.roblox_users_file)
            user_link = roblox_data.get(str(interaction.user.id))
            
            if not user_link:
                await interaction.followup.send("❌ You haven't linked your Roblox account! Use `/roblox_link` first.")
                return
            
            user_data = await self._get_user_by_id(user_link["roblox_id"])
            if not user_data:
                await interaction.followup.send("❌ Error fetching your linked Roblox account data!")
                return
        
        user_id = user_data["id"]
        display_name = user_data.get("displayName", user_data["name"])
        created_date = datetime.fromisoformat(user_data["created"].replace("Z", "+00:00"))
        
        # Get additional data
        presence_data = await self._get_user_presence(user_id)
        avatar_url = await self._get_user_avatar(user_id)
        
        embed = discord.Embed(
            title=f"🎮 {display_name}'s Roblox Profile",
            color=discord.Color.red()
        )
        
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        
        # Basic info
        embed.add_field(
            name="📊 Basic Information",
            value=f"**Username:** {user_data['name']}\n"
                  f"**Display Name:** {display_name}\n"
                  f"**User ID:** {user_id}\n"
                  f"**Created:** <t:{int(created_date.timestamp())}:D>",
            inline=False
        )
        
        # Presence/Activity
        if presence_data:
            presence_info = presence_data.get("userPresence", {})
            online_status = presence_info.get("userPresenceType", 0)
            
            status_map = {
                0: "🔴 Offline",
                1: "🟢 Online",
                2: "🟡 Away",
                3: "🔵 Playing"
            }
            
            status_text = status_map.get(online_status, "❓ Unknown")
            
            # If playing a game
            if online_status == 3 and presence_info.get("gameInstanceId"):
                game_id = presence_info.get("rootPlaceId")
                if game_id:
                    # Get game info
                    game_url = f"{self.roblox_games_api}/games/{game_id}"
                    game_data = await self._make_roblox_request(game_url)
                    
                    if game_data:
                        game_name = game_data.get("name", "Unknown Game")
                        status_text += f"\n🎯 **Playing:** {game_name}"
            
            embed.add_field(
                name="🟢 Current Status",
                value=status_text,
                inline=True
            )
        
        # Description
        if user_data.get("description"):
            description = user_data["description"][:200]
            if len(user_data["description"]) > 200:
                description += "..."
            embed.add_field(
                name="📝 Description",
                value=description,
                inline=False
            )
        
        embed.set_footer(text=f"Profile viewed by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="roblox_search", description="Search for Roblox users")
    @app_commands.describe(query="Username to search for")
    async def roblox_search(self, interaction: discord.Interaction, query: str):
        """Search for Roblox users"""
        await interaction.response.defer()
        
        # For user search, we'll try exact match first
        user_data = await self._get_user_by_username(query)
        
        if user_data:
            user_id = user_data["id"]
            display_name = user_data.get("displayName", user_data["name"])
            avatar_url = await self._get_user_avatar(user_id)
            
            embed = discord.Embed(
                title="🔍 User Search Result",
                color=discord.Color.blue()
            )
            
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            
            embed.add_field(
                name=f"👤 {display_name}",
                value=f"**Username:** {user_data['name']}\n"
                      f"**Display Name:** {display_name}\n"
                      f"**User ID:** {user_id}",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ No exact match found for '{query}'. Try the exact username.")

    @app_commands.command(name="roblox_group", description="Get information about a Roblox group")
    @app_commands.describe(group_id="Group ID number")
    async def roblox_group(self, interaction: discord.Interaction, group_id: int):
        """Get Roblox group information"""
        await interaction.response.defer()
        
        group_data = await self._get_group_info(group_id)
        
        if not group_data:
            await interaction.followup.send(f"❌ Group with ID {group_id} not found!")
            return
        
        embed = discord.Embed(
            title=f"👥 {group_data['name']}",
            description=group_data.get("description", "No description available")[:500],
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="📊 Group Stats",
            value=f"**Group ID:** {group_id}\n"
                  f"**Members:** {group_data.get('memberCount', 'Unknown'):,}\n"
                  f"**Public:** {'Yes' if group_data.get('publicEntryAllowed') else 'No'}\n"
                  f"**Created:** <t:{int(datetime.fromisoformat(group_data['created'].replace('Z', '+00:00')).timestamp())}:D>",
            inline=True
        )
        
        if group_data.get("owner"):
            owner = group_data["owner"]
            embed.add_field(
                name="👑 Owner",
                value=f"**{owner.get('displayName', owner['username'])}**\n(@{owner['username']})",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="roblox_group_search", description="Search for Roblox groups")
    @app_commands.describe(query="Group name to search for")
    async def roblox_group_search(self, interaction: discord.Interaction, query: str):
        """Search for Roblox groups"""
        await interaction.response.defer()
        
        groups = await self._search_groups(query, limit=5)
        
        if not groups:
            await interaction.followup.send(f"❌ No groups found for '{query}'!")
            return
        
        embed = discord.Embed(
            title=f"🔍 Group Search: '{query}'",
            description=f"Found {len(groups)} groups",
            color=discord.Color.purple()
        )
        
        for i, group in enumerate(groups, 1):
            embed.add_field(
                name=f"{i}. {group['name']}",
                value=f"**ID:** {group['id']}\n"
                      f"**Members:** {group.get('memberCount', 'Unknown'):,}\n"
                      f"**Description:** {(group.get('description') or 'No description')[:100]}...",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="roblox_status", description="Check who's currently playing Roblox")
    async def roblox_status(self, interaction: discord.Interaction):
        """Check online status of linked Roblox users"""
        await interaction.response.defer()
        
        roblox_data = self._read_json(self.roblox_users_file)
        
        if not roblox_data:
            await interaction.followup.send("❌ No linked Roblox accounts found in this server!")
            return
        
        embed = discord.Embed(
            title="🎮 Roblox Activity Status",
            color=discord.Color.green()
        )
        
        online_users = []
        offline_users = []
        
        for discord_id, user_info in roblox_data.items():
            try:
                discord_user = self.bot.get_user(int(discord_id))
                if not discord_user or not interaction.guild.get_member(discord_user.id):
                    continue  # Skip users not in this server
                
                roblox_id = user_info["roblox_id"]
                presence_data = await self._get_user_presence(roblox_id)
                
                if presence_data:
                    presence_info = presence_data.get("userPresence", {})
                    online_status = presence_info.get("userPresenceType", 0)
                    
                    if online_status in [1, 2, 3]:  # Online, Away, or Playing
                        status_text = f"**{user_info['roblox_display_name']}** ({discord_user.display_name})"
                        
                        if online_status == 3 and presence_info.get("gameInstanceId"):
                            game_id = presence_info.get("rootPlaceId")
                            if game_id:
                                game_url = f"{self.roblox_games_api}/games/{game_id}"
                                game_data = await self._make_roblox_request(game_url)
                                if game_data:
                                    status_text += f" - Playing **{game_data.get('name', 'Unknown Game')}**"
                        
                        online_users.append(status_text)
                    else:
                        offline_users.append(f"**{user_info['roblox_display_name']}** ({discord_user.display_name})")
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error checking user status: {e}")
                continue
        
        if online_users:
            embed.add_field(
                name="🟢 Online/Playing",
                value="\n".join(online_users[:10]),
                inline=False
            )
        
        if offline_users:
            embed.add_field(
                name="🔴 Offline",
                value="\n".join(offline_users[:10]),
                inline=False
            )
        
        if not online_users and not offline_users:
            embed.description = "No linked Roblox accounts found for server members."
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RobloxIntegrationCog(bot))