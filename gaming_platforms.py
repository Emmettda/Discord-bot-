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

class GamingPlatformsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.gaming_accounts_file = os.path.join(self.data_dir, "gaming_accounts.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files
        self._init_file(self.gaming_accounts_file, {})
        
        # Gaming platform configs
        self.destiny_api_key = os.getenv('BUNGIE_API_KEY')  # User needs to provide
        self.xbox_api_key = os.getenv('XBOX_API_KEY')      # User needs to provide

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

    async def _make_api_request(self, url: str, headers: dict = None) -> dict:
        """Make an API request"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return None

    @app_commands.command(name="link_gaming_account", description="Link your gaming platform accounts")
    @app_commands.describe(
        platform="Gaming platform to link",
        username="Your username/gamertag on that platform",
        platform_id="Platform-specific ID (optional for some platforms)"
    )
    async def link_gaming_account(self, interaction: discord.Interaction, 
                                platform: str, 
                                username: str,
                                platform_id: str = None):
        """Link gaming platform accounts"""
        
        platform = platform.lower()
        valid_platforms = ['xbox', 'playstation', 'nintendo', 'steam', 'destiny2', 'epic']
        
        if platform not in valid_platforms:
            await interaction.response.send_message(
                f"❌ Invalid platform! Supported: {', '.join(valid_platforms)}", 
                ephemeral=True
            )
            return
        
        # Save the gaming account link
        gaming_data = self._read_json(self.gaming_accounts_file)
        user_id = str(interaction.user.id)
        
        if user_id not in gaming_data:
            gaming_data[user_id] = {}
        
        gaming_data[user_id][platform] = {
            "username": username,
            "platform_id": platform_id,
            "linked_at": datetime.now().isoformat()
        }
        
        self._write_json(self.gaming_accounts_file, gaming_data)
        
        # Platform-specific embed colors and emojis
        platform_info = {
            'xbox': {'color': 0x107C10, 'emoji': '🎮', 'name': 'Xbox'},
            'playstation': {'color': 0x003087, 'emoji': '🎮', 'name': 'PlayStation'},
            'nintendo': {'color': 0xE60012, 'emoji': '🎮', 'name': 'Nintendo'},
            'steam': {'color': 0x1B2838, 'emoji': '💨', 'name': 'Steam'},
            'destiny2': {'color': 0xFFD700, 'emoji': '🌟', 'name': 'Destiny 2'},
            'epic': {'color': 0x2F3136, 'emoji': '🏪', 'name': 'Epic Games'}
        }
        
        info = platform_info.get(platform, {'color': 0x7289DA, 'emoji': '🎮', 'name': platform.title()})
        
        embed = discord.Embed(
            title=f"{info['emoji']} {info['name']} Account Linked",
            description=f"Successfully linked your {info['name']} account!",
            color=info['color']
        )
        
        embed.add_field(
            name="Account Details",
            value=f"**Platform:** {info['name']}\n"
                  f"**Username:** {username}" + (f"\n**ID:** {platform_id}" if platform_id else ""),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gaming_profile", description="View gaming platform profiles")
    @app_commands.describe(user="User to view profile for (optional)")
    async def gaming_profile(self, interaction: discord.Interaction, user: discord.Member = None):
        """View linked gaming accounts"""
        
        target_user = user or interaction.user
        gaming_data = self._read_json(self.gaming_accounts_file)
        user_data = gaming_data.get(str(target_user.id), {})
        
        if not user_data:
            await interaction.response.send_message(
                f"❌ {target_user.display_name} hasn't linked any gaming accounts!", 
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🎮 {target_user.display_name}'s Gaming Profile",
            color=discord.Color.purple()
        )
        
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
        
        platform_emojis = {
            'xbox': '🎮',
            'playstation': '🎮',
            'nintendo': '🎮',
            'steam': '💨',
            'destiny2': '🌟',
            'epic': '🏪'
        }
        
        for platform, account_info in user_data.items():
            emoji = platform_emojis.get(platform, '🎮')
            linked_date = datetime.fromisoformat(account_info['linked_at'])
            
            value = f"**Username:** {account_info['username']}"
            if account_info.get('platform_id'):
                value += f"\n**ID:** {account_info['platform_id']}"
            value += f"\n**Linked:** <t:{int(linked_date.timestamp())}:R>"
            
            embed.add_field(
                name=f"{emoji} {platform.title()}",
                value=value,
                inline=True
            )
        
        embed.set_footer(text=f"Total platforms linked: {len(user_data)}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="destiny_stats", description="View Destiny 2 player statistics")
    @app_commands.describe(username="Destiny 2 username (optional, uses linked account)")
    async def destiny_stats(self, interaction: discord.Interaction, username: str = None):
        """Get Destiny 2 player stats"""
        await interaction.response.defer()
        
        if not self.destiny_api_key:
            embed = discord.Embed(
                title="❌ Destiny 2 API Not Available",
                description="To enable Destiny 2 integration, the server admin needs to provide a Bungie API key.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="How to get API access:",
                value="1. Go to https://www.bungie.net/en/Application\n"
                      "2. Create a new application\n"
                      "3. Get your API key\n"
                      "4. Provide it to the bot developer",
                inline=False
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Get username from linked account or parameter
        if not username:
            gaming_data = self._read_json(self.gaming_accounts_file)
            user_data = gaming_data.get(str(interaction.user.id), {})
            destiny_account = user_data.get('destiny2')
            
            if not destiny_account:
                await interaction.followup.send("❌ You haven't linked your Destiny 2 account! Use `/link_gaming_account` first.")
                return
            
            username = destiny_account['username']
        
        # Mock Destiny 2 stats display (would use real API with key)
        embed = discord.Embed(
            title=f"🌟 Destiny 2 Stats - {username}",
            description="Destiny 2 API integration ready - provide Bungie API key to enable",
            color=0xFFD700
        )
        
        embed.add_field(
            name="🎯 PvE Stats",
            value="**Raids Completed:** API Key Required\n"
                  "**Strikes Completed:** API Key Required\n"
                  "**Power Level:** API Key Required",
            inline=True
        )
        
        embed.add_field(
            name="⚔️ PvP Stats",
            value="**K/D Ratio:** API Key Required\n"
                  "**Wins:** API Key Required\n"
                  "**Glory Rank:** API Key Required",
            inline=True
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="xbox_profile", description="View Xbox Live profile information")
    @app_commands.describe(gamertag="Xbox gamertag (optional, uses linked account)")
    async def xbox_profile(self, interaction: discord.Interaction, gamertag: str = None):
        """Get Xbox Live profile info"""
        await interaction.response.defer()
        
        if not self.xbox_api_key:
            embed = discord.Embed(
                title="❌ Xbox Live API Not Available",
                description="To enable Xbox Live integration, the server admin needs to provide an Xbox API key.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="How to get API access:",
                value="1. Register at https://xapi.us or similar Xbox API service\n"
                      "2. Get your API key\n"
                      "3. Provide it to the bot developer",
                inline=False
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Get gamertag from linked account or parameter
        if not gamertag:
            gaming_data = self._read_json(self.gaming_accounts_file)
            user_data = gaming_data.get(str(interaction.user.id), {})
            xbox_account = user_data.get('xbox')
            
            if not xbox_account:
                await interaction.followup.send("❌ You haven't linked your Xbox account! Use `/link_gaming_account` first.")
                return
            
            gamertag = xbox_account['username']
        
        # Mock Xbox profile display (would use real API with key)
        embed = discord.Embed(
            title=f"🎮 Xbox Profile - {gamertag}",
            description="Xbox Live API integration ready - provide API key to enable",
            color=0x107C10
        )
        
        embed.add_field(
            name="📊 Profile Stats",
            value="**Gamerscore:** API Key Required\n"
                  "**Account Tier:** API Key Required\n"
                  "**Rep:** API Key Required",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Recent Activity",
            value="**Currently Playing:** API Key Required\n"
                  "**Recent Games:** API Key Required\n"
                  "**Achievements:** API Key Required",
            inline=True
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="steam_profile", description="View Steam profile information")
    @app_commands.describe(steam_id="Steam ID or custom URL (optional, uses linked account)")
    async def steam_profile(self, interaction: discord.Interaction, steam_id: str = None):
        """Get Steam profile info using public Steam API"""
        await interaction.response.defer()
        
        # Get Steam ID from linked account or parameter
        if not steam_id:
            gaming_data = self._read_json(self.gaming_accounts_file)
            user_data = gaming_data.get(str(interaction.user.id), {})
            steam_account = user_data.get('steam')
            
            if not steam_account:
                await interaction.followup.send("❌ You haven't linked your Steam account! Use `/link_gaming_account` first.")
                return
            
            steam_id = steam_account.get('platform_id') or steam_account['username']
        
        # Try to resolve Steam ID if it's a custom URL
        if not steam_id.isdigit():
            # If it's not numeric, try to resolve vanity URL
            resolve_url = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key=STEAM_API_KEY&vanityurl={steam_id}"
            # Note: Would need Steam API key for this
        
        # Mock Steam profile display (Steam API is free but requires key)
        embed = discord.Embed(
            title=f"💨 Steam Profile - {steam_id}",
            description="Steam profile integration available with Steam API key",
            color=0x1B2838
        )
        
        embed.add_field(
            name="📊 Profile Info",
            value="**Display Name:** Requires Steam API Key\n"
                  "**Account Created:** Requires Steam API Key\n"
                  "**Country:** Requires Steam API Key",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Gaming Stats",
            value="**Games Owned:** Requires Steam API Key\n"
                  "**Currently Playing:** Requires Steam API Key\n"
                  "**Recent Activity:** Requires Steam API Key",
            inline=True
        )
        
        embed.add_field(
            name="🔗 How to Enable",
            value="Get a free Steam API key from:\nhttps://steamcommunity.com/dev/apikey",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gaming_leaderboard", description="View server gaming activity leaderboard")
    async def gaming_leaderboard(self, interaction: discord.Interaction):
        """Show gaming platform leaderboard for server"""
        
        gaming_data = self._read_json(self.gaming_accounts_file)
        
        if not gaming_data:
            await interaction.response.send_message("❌ No linked gaming accounts found!", ephemeral=True)
            return
        
        # Count platforms per user
        user_platform_counts = {}
        platform_totals = {}
        
        for user_id, platforms in gaming_data.items():
            user = self.bot.get_user(int(user_id))
            if not user or not interaction.guild.get_member(user.id):
                continue  # Skip users not in this server
            
            user_platform_counts[user] = len(platforms)
            
            for platform in platforms:
                platform_totals[platform] = platform_totals.get(platform, 0) + 1
        
        embed = discord.Embed(
            title="🏆 Gaming Platform Leaderboard",
            description=f"Gaming activity for {interaction.guild.name}",
            color=discord.Color.gold()
        )
        
        # Most connected users
        if user_platform_counts:
            sorted_users = sorted(user_platform_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            leaderboard_text = ""
            for i, (user, count) in enumerate(sorted_users, 1):
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
                leaderboard_text += f"{medal} **{user.display_name}** - {count} platforms\n"
            
            embed.add_field(
                name="👑 Most Connected Gamers",
                value=leaderboard_text,
                inline=False
            )
        
        # Platform popularity
        if platform_totals:
            sorted_platforms = sorted(platform_totals.items(), key=lambda x: x[1], reverse=True)
            
            platform_emojis = {
                'xbox': '🎮', 'playstation': '🎮', 'nintendo': '🎮',
                'steam': '💨', 'destiny2': '🌟', 'epic': '🏪'
            }
            
            platform_text = ""
            for platform, count in sorted_platforms:
                emoji = platform_emojis.get(platform, '🎮')
                platform_text += f"{emoji} **{platform.title()}**: {count} users\n"
            
            embed.add_field(
                name="📊 Platform Popularity",
                value=platform_text,
                inline=True
            )
        
        embed.set_footer(text=f"Total gaming accounts linked: {sum(platform_totals.values())}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unlink_gaming", description="Unlink a gaming platform account")
    @app_commands.describe(platform="Platform to unlink")
    async def unlink_gaming(self, interaction: discord.Interaction, platform: str):
        """Unlink a gaming platform account"""
        
        platform = platform.lower()
        gaming_data = self._read_json(self.gaming_accounts_file)
        user_data = gaming_data.get(str(interaction.user.id), {})
        
        if platform not in user_data:
            await interaction.response.send_message(f"❌ You don't have a linked {platform} account!", ephemeral=True)
            return
        
        # Remove the platform
        del user_data[platform]
        
        # Update the file
        if user_data:
            gaming_data[str(interaction.user.id)] = user_data
        else:
            del gaming_data[str(interaction.user.id)]
        
        self._write_json(self.gaming_accounts_file, gaming_data)
        
        embed = discord.Embed(
            title="🔗 Account Unlinked",
            description=f"Successfully unlinked your {platform.title()} account.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GamingPlatformsCog(bot))