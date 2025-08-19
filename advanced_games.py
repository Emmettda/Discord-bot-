import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import os
import random
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class AdvancedGamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.rpg_file = os.path.join(self.data_dir, "rpg_data.json")
        self.dungeon_file = os.path.join(self.data_dir, "dungeon_sessions.json")
        self.guild_battles_file = os.path.join(self.data_dir, "guild_battles.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files
        self._init_file(self.rpg_file, {})
        self._init_file(self.dungeon_file, {})
        self._init_file(self.guild_battles_file, {})
        
        # Game configuration
        self.character_classes = {
            "warrior": {"hp": 120, "attack": 15, "defense": 12, "speed": 8, "emoji": "⚔️"},
            "mage": {"hp": 80, "attack": 20, "defense": 6, "speed": 12, "emoji": "🔮"},
            "archer": {"hp": 100, "attack": 18, "defense": 8, "speed": 15, "emoji": "🏹"},
            "rogue": {"hp": 90, "attack": 16, "defense": 7, "speed": 18, "emoji": "🗡️"},
            "paladin": {"hp": 140, "attack": 12, "defense": 16, "speed": 6, "emoji": "🛡️"}
        }
        
        self.equipment = {
            "weapons": {
                "rusty_sword": {"attack": 5, "price": 100, "emoji": "🗡️"},
                "steel_blade": {"attack": 12, "price": 500, "emoji": "⚔️"},
                "enchanted_staff": {"attack": 18, "price": 800, "emoji": "🔮"},
                "legendary_bow": {"attack": 25, "price": 1500, "emoji": "🏹"},
                "demon_slayer": {"attack": 35, "price": 3000, "emoji": "🗡️"}
            },
            "armor": {
                "leather_vest": {"defense": 5, "price": 150, "emoji": "🦺"},
                "chain_mail": {"defense": 10, "price": 400, "emoji": "🛡️"},
                "plate_armor": {"defense": 18, "price": 1000, "emoji": "🛡️"},
                "dragon_scale": {"defense": 30, "price": 2500, "emoji": "🐉"}
            }
        }
        
        self.monsters = {
            "goblin": {"hp": 30, "attack": 8, "defense": 3, "exp": 15, "gold": 25, "emoji": "👹"},
            "orc": {"hp": 60, "attack": 12, "defense": 6, "exp": 30, "gold": 50, "emoji": "👹"},
            "troll": {"hp": 100, "attack": 18, "defense": 10, "exp": 60, "gold": 100, "emoji": "👹"},
            "dragon": {"hp": 200, "attack": 30, "defense": 20, "exp": 150, "gold": 500, "emoji": "🐉"},
            "demon_lord": {"hp": 350, "attack": 45, "defense": 25, "exp": 300, "gold": 1000, "emoji": "👹"}
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

    def _get_player_data(self, user_id: str, guild_id: str) -> dict:
        """Get or create player RPG data"""
        rpg_data = self._read_json(self.rpg_file)
        
        if guild_id not in rpg_data:
            rpg_data[guild_id] = {}
        
        if user_id not in rpg_data[guild_id]:
            rpg_data[guild_id][user_id] = {
                "character_class": None,
                "level": 1,
                "exp": 0,
                "hp": 100,
                "max_hp": 100,
                "attack": 10,
                "defense": 5,
                "speed": 10,
                "gold": 100,
                "weapon": None,
                "armor": None,
                "inventory": [],
                "quest_cooldown": None,
                "dungeon_runs": 0,
                "pvp_wins": 0,
                "pvp_losses": 0,
                "achievements": []
            }
            self._write_json(self.rpg_file, rpg_data)
        
        return rpg_data[guild_id][user_id]

    def _save_player_data(self, user_id: str, guild_id: str, player_data: dict):
        """Save player RPG data"""
        rpg_data = self._read_json(self.rpg_file)
        if guild_id not in rpg_data:
            rpg_data[guild_id] = {}
        rpg_data[guild_id][user_id] = player_data
        self._write_json(self.rpg_file, rpg_data)

    @app_commands.command(name="rpg_start", description="Start your RPG adventure by choosing a character class")
    @app_commands.describe(character_class="Choose your character class")
    async def rpg_start(self, interaction: discord.Interaction, character_class: str):
        """Start RPG adventure"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        
        if character_class.lower() not in self.character_classes:
            classes_list = ", ".join(self.character_classes.keys())
            await interaction.response.send_message(f"❌ Invalid class! Choose from: {classes_list}", ephemeral=True)
            return
        
        player_data = self._get_player_data(user_id, guild_id)
        
        if player_data["character_class"]:
            await interaction.response.send_message("❌ You already have a character! Use `/rpg_profile` to view your stats.", ephemeral=True)
            return
        
        # Set character class and base stats
        class_info = self.character_classes[character_class.lower()]
        player_data["character_class"] = character_class.lower()
        player_data["max_hp"] = class_info["hp"]
        player_data["hp"] = class_info["hp"]
        player_data["attack"] = class_info["attack"]
        player_data["defense"] = class_info["defense"]
        player_data["speed"] = class_info["speed"]
        
        self._save_player_data(user_id, guild_id, player_data)
        
        embed = discord.Embed(
            title=f"🎮 Welcome to the RPG Adventure!",
            description=f"{interaction.user.mention} has chosen the **{character_class.title()}** class!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name=f"{class_info['emoji']} Your Stats",
            value=f"**HP:** {class_info['hp']}\n"
                  f"**Attack:** {class_info['attack']}\n"
                  f"**Defense:** {class_info['defense']}\n"
                  f"**Speed:** {class_info['speed']}\n"
                  f"**Gold:** 100",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Next Steps",
            value="• `/rpg_profile` - View your character\n"
                  "• `/rpg_quest` - Go on adventures\n"
                  "• `/rpg_shop` - Buy equipment\n"
                  "• `/rpg_battle` - Fight other players",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rpg_profile", description="View your RPG character profile")
    async def rpg_profile(self, interaction: discord.Interaction, user: discord.Member = None):
        """View RPG character profile"""
        target_user = user or interaction.user
        user_id = str(target_user.id)
        guild_id = str(interaction.guild.id)
        
        player_data = self._get_player_data(user_id, guild_id)
        
        if not player_data["character_class"]:
            await interaction.response.send_message("❌ Character not found! Use `/rpg_start` to begin your adventure.", ephemeral=True)
            return
        
        class_info = self.character_classes[player_data["character_class"]]
        
        # Calculate total stats with equipment
        total_attack = player_data["attack"]
        total_defense = player_data["defense"]
        
        if player_data["weapon"]:
            weapon_info = self.equipment["weapons"][player_data["weapon"]]
            total_attack += weapon_info["attack"]
        
        if player_data["armor"]:
            armor_info = self.equipment["armor"][player_data["armor"]]
            total_defense += armor_info["defense"]
        
        embed = discord.Embed(
            title=f"{class_info['emoji']} {target_user.display_name}'s RPG Profile",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Character Info",
            value=f"**Class:** {player_data['character_class'].title()}\n"
                  f"**Level:** {player_data['level']}\n"
                  f"**EXP:** {player_data['exp']}/100\n"
                  f"**Gold:** {player_data['gold']:,}",
            inline=True
        )
        
        embed.add_field(
            name="⚔️ Combat Stats",
            value=f"**HP:** {player_data['hp']}/{player_data['max_hp']}\n"
                  f"**Attack:** {total_attack}\n"
                  f"**Defense:** {total_defense}\n"
                  f"**Speed:** {player_data['speed']}",
            inline=True
        )
        
        equipment_text = "**Weapon:** " + (player_data["weapon"].replace("_", " ").title() if player_data["weapon"] else "None") + "\n"
        equipment_text += "**Armor:** " + (player_data["armor"].replace("_", " ").title() if player_data["armor"] else "None")
        
        embed.add_field(
            name="🎒 Equipment",
            value=equipment_text,
            inline=True
        )
        
        embed.add_field(
            name="🏆 Battle Record",
            value=f"**PvP Wins:** {player_data['pvp_wins']}\n"
                  f"**PvP Losses:** {player_data['pvp_losses']}\n"
                  f"**Dungeon Runs:** {player_data['dungeon_runs']}",
            inline=True
        )
        
        if player_data["achievements"]:
            achievements_text = "\n".join([f"🏅 {achievement}" for achievement in player_data["achievements"][:5]])
            embed.add_field(
                name="🏅 Recent Achievements",
                value=achievements_text,
                inline=False
            )
        
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rpg_quest", description="Go on a quest to fight monsters and gain experience")
    async def rpg_quest(self, interaction: discord.Interaction):
        """Go on a quest"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        
        player_data = self._get_player_data(user_id, guild_id)
        
        if not player_data["character_class"]:
            await interaction.response.send_message("❌ Start your adventure first with `/rpg_start`!", ephemeral=True)
            return
        
        # Check cooldown
        if player_data["quest_cooldown"]:
            cooldown_time = datetime.fromisoformat(player_data["quest_cooldown"])
            if datetime.now() < cooldown_time:
                remaining = cooldown_time - datetime.now()
                await interaction.response.send_message(f"⏰ Quest cooldown: {remaining.seconds}s remaining", ephemeral=True)
                return
        
        # Random monster encounter
        monster_name = random.choice(list(self.monsters.keys()))
        monster = self.monsters[monster_name].copy()
        
        await interaction.response.defer()
        
        # Combat simulation
        player_hp = player_data["hp"]
        monster_hp = monster["hp"]
        
        # Calculate player stats with equipment
        player_attack = player_data["attack"]
        player_defense = player_data["defense"]
        
        if player_data["weapon"]:
            weapon_info = self.equipment["weapons"][player_data["weapon"]]
            player_attack += weapon_info["attack"]
        
        if player_data["armor"]:
            armor_info = self.equipment["armor"][player_data["armor"]]
            player_defense += armor_info["defense"]
        
        combat_log = []
        turn = 1
        
        while player_hp > 0 and monster_hp > 0 and turn <= 10:
            # Player attacks first if speed is higher
            if player_data["speed"] >= monster.get("speed", 10):
                # Player attack
                damage = max(1, player_attack - monster["defense"])
                monster_hp -= damage
                combat_log.append(f"⚔️ You deal {damage} damage! Monster HP: {max(0, monster_hp)}")
                
                if monster_hp <= 0:
                    break
                
                # Monster attack
                damage = max(1, monster["attack"] - player_defense)
                player_hp -= damage
                combat_log.append(f"👹 {monster_name.title()} deals {damage} damage! Your HP: {max(0, player_hp)}")
            else:
                # Monster attacks first
                damage = max(1, monster["attack"] - player_defense)
                player_hp -= damage
                combat_log.append(f"👹 {monster_name.title()} deals {damage} damage! Your HP: {max(0, player_hp)}")
                
                if player_hp <= 0:
                    break
                
                # Player attack
                damage = max(1, player_attack - monster["defense"])
                monster_hp -= damage
                combat_log.append(f"⚔️ You deal {damage} damage! Monster HP: {max(0, monster_hp)}")
            
            turn += 1
        
        # Determine outcome
        if player_hp <= 0:
            # Player defeated
            embed = discord.Embed(
                title=f"💀 Quest Failed!",
                description=f"You were defeated by the {monster_name.title()}!",
                color=discord.Color.red()
            )
            player_data["hp"] = 1  # Don't let player die completely
        else:
            # Player won
            exp_gained = monster["exp"]
            gold_gained = monster["gold"]
            
            player_data["exp"] += exp_gained
            player_data["gold"] += gold_gained
            player_data["hp"] = player_hp
            
            # Level up check
            level_up = False
            while player_data["exp"] >= 100:
                player_data["exp"] -= 100
                player_data["level"] += 1
                player_data["max_hp"] += 10
                player_data["hp"] = player_data["max_hp"]  # Full heal on level up
                player_data["attack"] += 2
                player_data["defense"] += 1
                level_up = True
            
            embed = discord.Embed(
                title=f"🎉 Quest Complete!",
                description=f"You defeated the {monster_name.title()}!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Rewards",
                value=f"**EXP:** +{exp_gained}\n**Gold:** +{gold_gained}",
                inline=True
            )
            
            if level_up:
                embed.add_field(
                    name="🎊 LEVEL UP!",
                    value=f"Level {player_data['level']}!\n+10 HP, +2 ATK, +1 DEF",
                    inline=True
                )
        
        # Set cooldown (5 minutes)
        player_data["quest_cooldown"] = (datetime.now() + timedelta(minutes=5)).isoformat()
        
        self._save_player_data(user_id, guild_id, player_data)
        
        # Add combat log
        if len(combat_log) > 0:
            embed.add_field(
                name="⚔️ Combat Log",
                value="\n".join(combat_log[-4:]),  # Show last 4 actions
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rpg_shop", description="Buy weapons and armor to improve your character")
    async def rpg_shop(self, interaction: discord.Interaction, item_type: str = "weapons"):
        """RPG shop for equipment"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        
        player_data = self._get_player_data(user_id, guild_id)
        
        if not player_data["character_class"]:
            await interaction.response.send_message("❌ Start your adventure first with `/rpg_start`!", ephemeral=True)
            return
        
        if item_type.lower() not in ["weapons", "armor"]:
            await interaction.response.send_message("❌ Choose 'weapons' or 'armor'", ephemeral=True)
            return
        
        items = self.equipment[item_type.lower()]
        
        embed = discord.Embed(
            title=f"🏪 RPG Shop - {item_type.title()}",
            description=f"Your Gold: {player_data['gold']:,}",
            color=discord.Color.orange()
        )
        
        for item_name, item_info in items.items():
            stat_name = "Attack" if item_type.lower() == "weapons" else "Defense"
            stat_value = item_info.get("attack" if item_type.lower() == "weapons" else "defense", 0)
            
            embed.add_field(
                name=f"{item_info['emoji']} {item_name.replace('_', ' ').title()}",
                value=f"**{stat_name}:** +{stat_value}\n**Price:** {item_info['price']} gold",
                inline=True
            )
        
        embed.set_footer(text="Use /rpg_buy <item_name> to purchase")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rpg_buy", description="Buy an item from the RPG shop")
    @app_commands.describe(item_name="Name of the item to buy")
    async def rpg_buy(self, interaction: discord.Interaction, item_name: str):
        """Buy an item from the shop"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        
        player_data = self._get_player_data(user_id, guild_id)
        
        if not player_data["character_class"]:
            await interaction.response.send_message("❌ Start your adventure first with `/rpg_start`!", ephemeral=True)
            return
        
        item_name = item_name.lower().replace(" ", "_")
        item_found = None
        item_type = None
        
        # Find the item
        for category, items in self.equipment.items():
            if item_name in items:
                item_found = items[item_name]
                item_type = category
                break
        
        if not item_found:
            await interaction.response.send_message("❌ Item not found! Check `/rpg_shop` for available items.", ephemeral=True)
            return
        
        if player_data["gold"] < item_found["price"]:
            await interaction.response.send_message(f"❌ Not enough gold! You need {item_found['price']} gold.", ephemeral=True)
            return
        
        # Purchase item
        player_data["gold"] -= item_found["price"]
        
        if item_type == "weapons":
            old_weapon = player_data["weapon"]
            player_data["weapon"] = item_name
        else:
            old_armor = player_data["armor"]
            player_data["armor"] = item_name
        
        self._save_player_data(user_id, guild_id, player_data)
        
        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"You bought **{item_name.replace('_', ' ').title()}**!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Cost",
            value=f"{item_found['price']} gold\nRemaining: {player_data['gold']} gold",
            inline=True
        )
        
        stat_name = "Attack" if item_type == "weapons" else "Defense"
        stat_value = item_found.get("attack" if item_type == "weapons" else "defense", 0)
        
        embed.add_field(
            name="📈 Stats",
            value=f"+{stat_value} {stat_name}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rpg_battle", description="Challenge another player to PvP combat")
    @app_commands.describe(opponent="Player to challenge")
    async def rpg_battle(self, interaction: discord.Interaction, opponent: discord.Member):
        """PvP battle between players"""
        if opponent.bot:
            await interaction.response.send_message("❌ Can't battle bots!", ephemeral=True)
            return
        
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("❌ Can't battle yourself!", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        opponent_id = str(opponent.id)
        guild_id = str(interaction.guild.id)
        
        player1_data = self._get_player_data(user_id, guild_id)
        player2_data = self._get_player_data(opponent_id, guild_id)
        
        if not player1_data["character_class"] or not player2_data["character_class"]:
            await interaction.response.send_message("❌ Both players need characters! Use `/rpg_start` first.", ephemeral=True)
            return
        
        # Battle invitation
        embed = discord.Embed(
            title="⚔️ PvP Battle Challenge!",
            description=f"{interaction.user.mention} challenges {opponent.mention} to battle!",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name=f"{interaction.user.display_name}",
            value=f"Level {player1_data['level']} {player1_data['character_class'].title()}",
            inline=True
        )
        
        embed.add_field(
            name=f"{opponent.display_name}",
            value=f"Level {player2_data['level']} {player2_data['character_class'].title()}",
            inline=True
        )
        
        view = BattleView(interaction.user, opponent, player1_data, player2_data, self)
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="rpg_leaderboard", description="View the RPG leaderboard")
    async def rpg_leaderboard(self, interaction: discord.Interaction, category: str = "level"):
        """View RPG leaderboard"""
        guild_id = str(interaction.guild.id)
        rpg_data = self._read_json(self.rpg_file)
        
        if guild_id not in rpg_data or not rpg_data[guild_id]:
            await interaction.response.send_message("❌ No RPG data found!", ephemeral=True)
            return
        
        players = []
        for user_id, player_data in rpg_data[guild_id].items():
            if player_data.get("character_class"):
                user = self.bot.get_user(int(user_id))
                if user:
                    players.append((user, player_data))
        
        if category == "level":
            players.sort(key=lambda x: x[1]["level"], reverse=True)
            title = "🏆 Level Leaderboard"
        elif category == "gold":
            players.sort(key=lambda x: x[1]["gold"], reverse=True)
            title = "💰 Gold Leaderboard"
        elif category == "pvp":
            players.sort(key=lambda x: x[1]["pvp_wins"], reverse=True)
            title = "⚔️ PvP Wins Leaderboard"
        else:
            await interaction.response.send_message("❌ Choose: level, gold, or pvp", ephemeral=True)
            return
        
        embed = discord.Embed(title=title, color=discord.Color.gold())
        
        for i, (user, data) in enumerate(players[:10], 1):
            if category == "level":
                value = f"Level {data['level']}"
            elif category == "gold":
                value = f"{data['gold']:,} gold"
            else:
                value = f"{data['pvp_wins']} wins"
            
            embed.add_field(
                name=f"{i}. {user.display_name}",
                value=value,
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)

class BattleView(discord.ui.View):
    def __init__(self, challenger, opponent, player1_data, player2_data, cog):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.player1_data = player1_data
        self.player2_data = player2_data
        self.cog = cog
        self.accepted = False

    @discord.ui.button(label="Accept Battle", style=discord.ButtonStyle.green, emoji="⚔️")
    async def accept_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("❌ Only the challenged player can accept!", ephemeral=True)
            return
        
        self.accepted = True
        
        # Simulate battle
        await interaction.response.defer()
        
        # Calculate stats for both players
        p1_attack = self.player1_data["attack"]
        p1_defense = self.player1_data["defense"]
        p1_hp = self.player1_data["hp"]
        
        p2_attack = self.player2_data["attack"]
        p2_defense = self.player2_data["defense"]
        p2_hp = self.player2_data["hp"]
        
        # Add equipment bonuses
        if self.player1_data["weapon"]:
            weapon_info = self.cog.equipment["weapons"][self.player1_data["weapon"]]
            p1_attack += weapon_info["attack"]
        if self.player1_data["armor"]:
            armor_info = self.cog.equipment["armor"][self.player1_data["armor"]]
            p1_defense += armor_info["defense"]
            
        if self.player2_data["weapon"]:
            weapon_info = self.cog.equipment["weapons"][self.player2_data["weapon"]]
            p2_attack += weapon_info["attack"]
        if self.player2_data["armor"]:
            armor_info = self.cog.equipment["armor"][self.player2_data["armor"]]
            p2_defense += armor_info["defense"]
        
        # Battle simulation
        turn = 1
        while p1_hp > 0 and p2_hp > 0 and turn <= 20:
            if self.player1_data["speed"] >= self.player2_data["speed"]:
                # Player 1 attacks first
                damage = max(1, p1_attack - p2_defense)
                p2_hp -= damage
                if p2_hp <= 0:
                    break
                
                damage = max(1, p2_attack - p1_defense)
                p1_hp -= damage
            else:
                # Player 2 attacks first
                damage = max(1, p2_attack - p1_defense)
                p1_hp -= damage
                if p1_hp <= 0:
                    break
                
                damage = max(1, p1_attack - p2_defense)
                p2_hp -= damage
            
            turn += 1
        
        # Determine winner
        if p1_hp > p2_hp:
            winner = self.challenger
            loser = self.opponent
            winner_data = self.player1_data
            loser_data = self.player2_data
        else:
            winner = self.opponent
            loser = self.challenger
            winner_data = self.player2_data
            loser_data = self.player1_data
        
        # Update stats
        winner_data["pvp_wins"] += 1
        loser_data["pvp_losses"] += 1
        
        # Save data
        guild_id = str(interaction.guild.id)
        self.cog._save_player_data(str(winner.id), guild_id, winner_data)
        self.cog._save_player_data(str(loser.id), guild_id, loser_data)
        
        # Create result embed
        embed = discord.Embed(
            title="🏆 Battle Complete!",
            description=f"{winner.mention} defeats {loser.mention}!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🎊 Winner",
            value=f"{winner.display_name}\nPvP Wins: {winner_data['pvp_wins']}",
            inline=True
        )
        
        embed.add_field(
            name="💀 Defeated",
            value=f"{loser.display_name}\nPvP Losses: {loser_data['pvp_losses']}",
            inline=True
        )
        
        self.clear_items()
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌")
    async def decline_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("❌ Only the challenged player can decline!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="❌ Battle Declined",
            description=f"{self.opponent.mention} declined the battle challenge.",
            color=discord.Color.red()
        )
        
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    await bot.add_cog(AdvancedGamesCog(bot))