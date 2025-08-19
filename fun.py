import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import aiohttp
from bot.utils.helpers import create_embed, format_duration

logger = logging.getLogger(__name__)

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.quotes_file = os.path.join(self.data_dir, "quotes.json")
        self.gambling_file = os.path.join(self.data_dir, "gambling.json")
        self.status_file = os.path.join(self.data_dir, "user_status.json")
        
        # Initialize data files
        self._init_file(self.quotes_file, {})
        self._init_file(self.gambling_file, {})
        self._init_file(self.status_file, {})
        
        # Meme subreddits for content
        self.meme_subreddits = [
            'memes', 'dankmemes', 'wholesomememes', 'funny', 'programmerhumor', 
            'animemes', 'gaming', 'meirl', 'me_irl', 'ProgrammerHumor'
        ]
        
        # Fun quote responses
        self.quote_responses = [
            "That's what {author} said! 😄",
            "Classic {author} moment! 🎭",
            "Wise words from {author}! 🧠",
            "Remember when {author} said this? 📝",
            "{author} was onto something! 💡",
            "Throwback to {author}'s wisdom! ⏰"
        ]
        
        # Gambling games
        self.gambling_games = {
            'coinflip': {'min_bet': 10, 'max_bet': 1000, 'house_edge': 0.02},
            'dice': {'min_bet': 10, 'max_bet': 1000, 'house_edge': 0.05},
            'slots': {'min_bet': 5, 'max_bet': 500, 'house_edge': 0.15}
        }
        
    def _init_file(self, file_path: str, default_data: dict):
        """Initialize a JSON file with default data if it doesn't exist"""
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=2)
            logger.info(f"Created {file_path}")
    
    def _read_json(self, file_path: str) -> dict:
        """Read JSON data from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_json(self, file_path: str, data: dict):
        """Write JSON data to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing to {file_path}: {e}")
    
    async def collect_quote(self, message):
        """Collect interesting quotes from users"""
        # Skip if message is too short or from bot
        if len(message.content) < 10 or message.author.bot:
            return
        
        # Skip if message starts with command prefix
        if message.content.startswith(('/', '!', '?', '.', '-')):
            return
        
        # Random chance to collect quote (1 in 100 messages)
        if random.randint(1, 100) != 1:
            return
        
        quotes = self._read_json(self.quotes_file)
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        
        if guild_id not in quotes:
            quotes[guild_id] = {}
        
        if user_id not in quotes[guild_id]:
            quotes[guild_id][user_id] = []
        
        # Store quote with metadata
        quote_data = {
            'content': message.content,
            'author': message.author.display_name,
            'author_id': message.author.id,
            'channel': message.channel.name,
            'timestamp': datetime.utcnow().isoformat(),
            'message_id': message.id
        }
        
        quotes[guild_id][user_id].append(quote_data)
        
        # Keep only last 20 quotes per user
        if len(quotes[guild_id][user_id]) > 20:
            quotes[guild_id][user_id] = quotes[guild_id][user_id][-20:]
        
        self._write_json(self.quotes_file, quotes)
        
        # Very rare chance to respond with the quote (1 in 500 messages)
        if random.randint(1, 500) == 1:
            await self.random_quote_response(message)
    
    async def random_quote_response(self, message):
        """Randomly respond with a collected quote"""
        quotes = self._read_json(self.quotes_file)
        guild_id = str(message.guild.id)
        
        if guild_id not in quotes:
            return
        
        # Get all quotes from this guild
        all_quotes = []
        for user_quotes in quotes[guild_id].values():
            all_quotes.extend(user_quotes)
        
        if not all_quotes:
            return
        
        # Pick a random quote
        quote = random.choice(all_quotes)
        response_template = random.choice(self.quote_responses)
        
        # Format the response
        response = response_template.format(author=quote['author'])
        
        embed = discord.Embed(
            description=f'"{quote["content"]}"',
            color=discord.Color.random()
        )
        embed.set_footer(text=f"- {quote['author']}, {quote['timestamp'][:10]}")
        
        await message.channel.send(response, embed=embed)
    
    @app_commands.command(name="quote", description="Get a random quote from server members")
    @app_commands.describe(user="Get a quote from a specific user (optional)")
    async def quote(self, interaction: discord.Interaction, user: discord.Member = None):
        """Get a random quote from server members"""
        quotes = self._read_json(self.quotes_file)
        guild_id = str(interaction.guild.id)
        
        if guild_id not in quotes:
            await interaction.response.send_message("❌ No quotes collected yet! Keep chatting and I'll collect some memorable quotes.", ephemeral=True)
            return
        
        if user:
            user_id = str(user.id)
            if user_id not in quotes[guild_id] or not quotes[guild_id][user_id]:
                await interaction.response.send_message(f"❌ No quotes found for {user.mention}", ephemeral=True)
                return
            
            quote = random.choice(quotes[guild_id][user_id])
        else:
            # Get all quotes from this guild
            all_quotes = []
            for user_quotes in quotes[guild_id].values():
                all_quotes.extend(user_quotes)
            
            if not all_quotes:
                await interaction.response.send_message("❌ No quotes collected yet! Keep chatting and I'll collect some memorable quotes.", ephemeral=True)
                return
            
            quote = random.choice(all_quotes)
        
        embed = discord.Embed(
            title="💬 Random Quote",
            description=f'"{quote["content"]}"',
            color=discord.Color.random()
        )
        embed.set_footer(text=f"- {quote['author']}, {quote['timestamp'][:10]} in #{quote['channel']}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="meme", description="Get a random meme from Google")
    @app_commands.describe(query="Search term for memes (optional)")
    async def meme(self, interaction: discord.Interaction, query: str = None):
        """Get a random meme from Google"""
        await interaction.response.defer()
        
        try:
            await self._get_google_meme(interaction, query)
                
        except Exception as e:
            logger.error(f"Error fetching meme: {e}")
            await interaction.followup.send(f"❌ Error fetching meme: {str(e)}")
    
    async def _get_reddit_meme(self, interaction: discord.Interaction, subreddit: str = None):
        """Get meme from Reddit or fallback to meme APIs"""
        try:
            if subreddit:
                chosen_subreddit = subreddit
            else:
                chosen_subreddit = random.choice(self.meme_subreddits)
            
            # Try multiple Reddit API endpoints
            reddit_urls = [
                f"https://www.reddit.com/r/{chosen_subreddit}/hot.json?limit=50",
                f"https://www.reddit.com/r/{chosen_subreddit}/top.json?limit=50&t=week",
                f"https://www.reddit.com/r/{chosen_subreddit}.json?limit=50"
            ]
            
            async with aiohttp.ClientSession() as session:
                for url in reddit_urls:
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                        
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if 'data' not in data or 'children' not in data['data']:
                                    continue
                                
                                posts = data['data']['children']
                                
                                # Filter for image posts
                                image_posts = []
                                for post in posts:
                                    post_data = post['data']
                                    url_check = post_data.get('url', '')
                                    
                                    # Check for image URLs
                                    if (url_check.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) or 
                                        'i.redd.it' in url_check or 
                                        'i.imgur.com' in url_check or
                                        'imgur.com' in url_check):
                                        
                                        # Skip deleted/removed posts
                                        if not post_data.get('removed_by_category') and post_data.get('title'):
                                            image_posts.append(post_data)
                                
                                if image_posts:
                                    # Pick random meme
                                    meme = random.choice(image_posts)
                                    
                                    embed = discord.Embed(
                                        title=meme['title'][:256],  # Discord title limit
                                        color=discord.Color.random()
                                    )
                                    
                                    # Handle different image URL formats
                                    image_url = meme['url']
                                    if 'imgur.com' in image_url and not image_url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                        image_url = image_url.replace('imgur.com', 'i.imgur.com') + '.jpg'
                                    
                                    embed.set_image(url=image_url)
                                    embed.set_footer(text=f"👍 {meme.get('ups', 0)} | r/{chosen_subreddit} | Posted by u/{meme.get('author', 'unknown')}")
                                    
                                    await interaction.followup.send(embed=embed)
                                    return
                    except:
                        continue
                
                # If Reddit fails, fallback to meme API
                await interaction.followup.send(f"❌ Reddit API unavailable for r/{chosen_subreddit}. Trying alternative meme source...")
                await self._get_google_meme(interaction, "memes")
                        
        except Exception as e:
            logger.error(f"Error fetching Reddit meme: {e}")
            # Fallback to meme API
            await self._get_google_meme(interaction, "memes")
    
    async def _get_google_meme(self, interaction: discord.Interaction, query: str = None):
        """Get meme from meme APIs and services"""
        try:
            search_query = query or "funny memes"
            
            async with aiohttp.ClientSession() as session:
                # Try multiple meme APIs in order
                meme_apis = [
                    ("https://api.imgflip.com/get_memes", "imgflip"),
                    ("https://meme-api.herokuapp.com/gimme", "reddit_api"),
                    ("https://api.memegen.link/templates", "memegen"),
                ]
                
                for api_url, api_type in meme_apis:
                    try:
                        async with session.get(api_url, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if api_type == "imgflip":
                                    # ImgFlip API
                                    if 'data' in data and 'memes' in data['data']:
                                        memes = data['data']['memes']
                                        meme = random.choice(memes)
                                        
                                        embed = discord.Embed(
                                            title=meme['name'],
                                            color=discord.Color.random()
                                        )
                                        embed.set_image(url=meme['url'])
                                        embed.set_footer(text=f"Source: ImgFlip | Template: {meme['name']}")
                                        
                                        await interaction.followup.send(embed=embed)
                                        return
                                
                                elif api_type == "reddit_api":
                                    # Reddit meme API
                                    if 'url' in data and 'title' in data:
                                        embed = discord.Embed(
                                            title=data['title'][:256],
                                            color=discord.Color.random()
                                        )
                                        embed.set_image(url=data['url'])
                                        embed.set_footer(text=f"Source: r/{data.get('subreddit', 'unknown')} | 👍 {data.get('ups', 0)}")
                                        
                                        await interaction.followup.send(embed=embed)
                                        return
                                
                                elif api_type == "memegen":
                                    # MemeGen API
                                    if isinstance(data, list) and len(data) > 0:
                                        meme = random.choice(data)
                                        if 'example' in meme:
                                            embed = discord.Embed(
                                                title=meme.get('name', 'Meme Template'),
                                                color=discord.Color.random()
                                            )
                                            embed.set_image(url=meme['example']['url'])
                                            embed.set_footer(text=f"Source: MemeGen | Template: {meme.get('id', 'unknown')}")
                                            
                                            await interaction.followup.send(embed=embed)
                                            return
                                            
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout for {api_type} API")
                        continue
                    except Exception as e:
                        logger.warning(f"Error with {api_type} API: {e}")
                        continue
                
                # Enhanced fallback with more meme templates
                fallback_memes = [
                    {
                        "title": "This is Fine",
                        "url": "https://i.imgflip.com/1wz3as.jpg"
                    },
                    {
                        "title": "Distracted Boyfriend",
                        "url": "https://i.imgflip.com/1ur9b0.jpg"
                    },
                    {
                        "title": "Drake Pointing",
                        "url": "https://i.imgflip.com/30b1gx.jpg"
                    },
                    {
                        "title": "Two Buttons",
                        "url": "https://i.imgflip.com/1g8my4.jpg"
                    },
                    {
                        "title": "Expanding Brain",
                        "url": "https://i.imgflip.com/1jwhww.jpg"
                    },
                    {
                        "title": "Woman Yelling at Cat",
                        "url": "https://i.imgflip.com/345v97.jpg"
                    },
                    {
                        "title": "Change My Mind",
                        "url": "https://i.imgflip.com/24y43o.jpg"
                    },
                    {
                        "title": "Surprised Pikachu",
                        "url": "https://i.imgflip.com/2kbn1e.jpg"
                    }
                ]
                
                meme = random.choice(fallback_memes)
                embed = discord.Embed(
                    title=meme['title'],
                    color=discord.Color.random()
                )
                embed.set_image(url=meme['url'])
                embed.set_footer(text="Source: Curated Meme Collection")
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error fetching meme: {e}")
            await interaction.followup.send(f"❌ Error fetching meme: {str(e)}")
    
    @app_commands.command(name="balance", description="Check your gambling balance")
    async def balance(self, interaction: discord.Interaction):
        """Check user's gambling balance"""
        gambling_data = self._read_json(self.gambling_file)
        user_id = str(interaction.user.id)
        
        if user_id not in gambling_data:
            gambling_data[user_id] = {
                'balance': 1000,  # Starting balance
                'total_won': 0,
                'total_lost': 0,
                'games_played': 0,
                'last_daily': None
            }
            self._write_json(self.gambling_file, gambling_data)
        
        user_data = gambling_data[user_id]
        
        embed = discord.Embed(
            title=f"💰 {interaction.user.display_name}'s Balance",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="💵 Current Balance",
            value=f"{user_data['balance']:,} coins",
            inline=True
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"**Games Played:** {user_data['games_played']}\n"
                  f"**Total Won:** {user_data['total_won']:,}\n"
                  f"**Total Lost:** {user_data['total_lost']:,}",
            inline=True
        )
        
        # Calculate net profit/loss
        net = user_data['total_won'] - user_data['total_lost']
        embed.add_field(
            name="📈 Net Profit/Loss",
            value=f"{net:+,} coins",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="daily", description="Claim your daily coins")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily coins"""
        gambling_data = self._read_json(self.gambling_file)
        user_id = str(interaction.user.id)
        
        if user_id not in gambling_data:
            gambling_data[user_id] = {
                'balance': 1000,
                'total_won': 0,
                'total_lost': 0,
                'games_played': 0,
                'last_daily': None
            }
        
        user_data = gambling_data[user_id]
        now = datetime.utcnow()
        
        # Check if user already claimed today
        if user_data['last_daily']:
            last_daily = datetime.fromisoformat(user_data['last_daily'])
            if (now - last_daily).days < 1:
                next_daily = last_daily + timedelta(days=1)
                time_left = next_daily - now
                await interaction.response.send_message(
                    f"⏰ You already claimed your daily coins! Come back in {format_duration(int(time_left.total_seconds()))}"
                )
                return
        
        # Give daily coins (200-500 random)
        daily_amount = random.randint(200, 500)
        user_data['balance'] += daily_amount
        user_data['last_daily'] = now.isoformat()
        
        self._write_json(self.gambling_file, gambling_data)
        
        embed = discord.Embed(
            title="🎁 Daily Coins Claimed!",
            description=f"You received **{daily_amount:,} coins**!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="💰 New Balance",
            value=f"{user_data['balance']:,} coins",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="coinflip", description="Flip a coin and bet on the outcome")
    @app_commands.describe(
        bet="Amount to bet",
        choice="Heads or Tails"
    )
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: str):
        """Coinflip gambling game"""
        if choice.lower() not in ['heads', 'tails', 'h', 't']:
            await interaction.response.send_message("❌ Choose either 'heads' or 'tails'!", ephemeral=True)
            return
        
        await self._process_gambling_game(interaction, 'coinflip', bet, choice.lower())
    
    @app_commands.command(name="dice", description="Roll a dice and bet on the outcome")
    @app_commands.describe(
        bet="Amount to bet",
        number="Number to bet on (1-6)"
    )
    async def dice(self, interaction: discord.Interaction, bet: int, number: int):
        """Dice gambling game"""
        if number < 1 or number > 6:
            await interaction.response.send_message("❌ Choose a number between 1 and 6!", ephemeral=True)
            return
        
        await self._process_gambling_game(interaction, 'dice', bet, number)
    
    @app_commands.command(name="slots", description="Play the slot machine")
    @app_commands.describe(bet="Amount to bet")
    async def slots(self, interaction: discord.Interaction, bet: int):
        """Slot machine gambling game"""
        await self._process_gambling_game(interaction, 'slots', bet, None)
    
    async def _process_gambling_game(self, interaction: discord.Interaction, game_type: str, bet: int, choice):
        """Process gambling game logic"""
        gambling_data = self._read_json(self.gambling_file)
        user_id = str(interaction.user.id)
        
        # Initialize user if not exists
        if user_id not in gambling_data:
            gambling_data[user_id] = {
                'balance': 1000,
                'total_won': 0,
                'total_lost': 0,
                'games_played': 0,
                'last_daily': None
            }
        
        user_data = gambling_data[user_id]
        game_config = self.gambling_games[game_type]
        
        # Validate bet
        if bet < game_config['min_bet'] or bet > game_config['max_bet']:
            await interaction.response.send_message(
                f"❌ Bet must be between {game_config['min_bet']} and {game_config['max_bet']} coins!",
                ephemeral=True
            )
            return
        
        if bet > user_data['balance']:
            await interaction.response.send_message("❌ Insufficient balance!", ephemeral=True)
            return
        
        # Process game
        won = False
        result = None
        multiplier = 1
        
        if game_type == 'coinflip':
            result = random.choice(['heads', 'tails'])
            user_choice = choice if choice in ['heads', 'tails'] else ('heads' if choice == 'h' else 'tails')
            won = result == user_choice
            multiplier = 2 if won else 0
            
        elif game_type == 'dice':
            result = random.randint(1, 6)
            won = result == choice
            multiplier = 6 if won else 0
            
        elif game_type == 'slots':
            slots_emojis = ['🍎', '🍊', '🍇', '🍒', '🍋', '⭐', '💎']
            result = [random.choice(slots_emojis) for _ in range(3)]
            
            # Check for wins
            if result[0] == result[1] == result[2]:
                if result[0] == '💎':
                    multiplier = 10  # Diamond jackpot
                elif result[0] == '⭐':
                    multiplier = 5   # Star win
                else:
                    multiplier = 3   # Normal triple
                won = True
            elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
                multiplier = 1.5  # Pair
                won = True
            else:
                multiplier = 0
                won = False
        
        # Apply house edge
        if won and random.random() < game_config['house_edge']:
            won = False
            multiplier = 0
        
        # Calculate winnings
        if won:
            winnings = int(bet * multiplier) - bet
            user_data['balance'] += winnings
            user_data['total_won'] += winnings
        else:
            user_data['balance'] -= bet
            user_data['total_lost'] += bet
        
        user_data['games_played'] += 1
        
        # Create result embed
        color = discord.Color.green() if won else discord.Color.red()
        title = "🎉 You Won!" if won else "💸 You Lost!"
        
        embed = discord.Embed(title=title, color=color)
        
        if game_type == 'coinflip':
            embed.add_field(
                name="🪙 Coin Result",
                value=f"**{result.title()}**",
                inline=True
            )
            embed.add_field(
                name="Your Choice",
                value=f"**{user_choice.title()}**",
                inline=True
            )
        elif game_type == 'dice':
            embed.add_field(
                name="🎲 Dice Result",
                value=f"**{result}**",
                inline=True
            )
            embed.add_field(
                name="Your Choice",
                value=f"**{choice}**",
                inline=True
            )
        elif game_type == 'slots':
            embed.add_field(
                name="🎰 Slot Result",
                value=" ".join(result),
                inline=False
            )
        
        if won:
            embed.add_field(
                name="💰 Winnings",
                value=f"+{int(bet * multiplier) - bet:,} coins",
                inline=True
            )
        else:
            embed.add_field(
                name="💸 Lost",
                value=f"-{bet:,} coins",
                inline=True
            )
        
        embed.add_field(
            name="💵 New Balance",
            value=f"{user_data['balance']:,} coins",
            inline=True
        )
        
        self._write_json(self.gambling_file, gambling_data)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="set_status", description="Set your server status")
    @app_commands.describe(
        status="Your status (sleeping, afk, busy, gaming, etc.)",
        details="Additional details about your status"
    )
    async def set_status(self, interaction: discord.Interaction, status: str, details: str = ""):
        """Set user's server status"""
        status_data = self._read_json(self.status_file)
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        
        if guild_id not in status_data:
            status_data[guild_id] = {}
        
        status_data[guild_id][user_id] = {
            'status': status,
            'details': details,
            'set_at': datetime.utcnow().isoformat(),
            'username': interaction.user.display_name
        }
        
        self._write_json(self.status_file, status_data)
        
        embed = discord.Embed(
            title="✅ Status Updated",
            description=f"Your status has been set to: **{status}**",
            color=discord.Color.green()
        )
        
        if details:
            embed.add_field(
                name="📝 Details",
                value=details,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="status", description="Check someone's server status")
    @app_commands.describe(user="User to check status for")
    async def status(self, interaction: discord.Interaction, user: discord.Member = None):
        """Check user's server status"""
        target_user = user or interaction.user
        status_data = self._read_json(self.status_file)
        user_id = str(target_user.id)
        guild_id = str(interaction.guild.id)
        
        if (guild_id not in status_data or 
            user_id not in status_data[guild_id]):
            await interaction.response.send_message(
                f"❌ {target_user.mention} hasn't set a status yet!",
                ephemeral=True
            )
            return
        
        user_status = status_data[guild_id][user_id]
        set_at = datetime.fromisoformat(user_status['set_at'])
        time_ago = datetime.utcnow() - set_at
        
        embed = discord.Embed(
            title=f"📊 {target_user.display_name}'s Status",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Status",
            value=user_status['status'],
            inline=True
        )
        
        embed.add_field(
            name="⏰ Set",
            value=f"{format_duration(int(time_ago.total_seconds()))} ago",
            inline=True
        )
        
        if user_status['details']:
            embed.add_field(
                name="📝 Details",
                value=user_status['details'],
                inline=False
            )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="server_statuses", description="View all server statuses")
    async def server_statuses(self, interaction: discord.Interaction):
        """View all server statuses"""
        status_data = self._read_json(self.status_file)
        guild_id = str(interaction.guild.id)
        
        if guild_id not in status_data or not status_data[guild_id]:
            await interaction.response.send_message(
                "❌ No one has set a status yet!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"📊 Server Statuses - {interaction.guild.name}",
            color=discord.Color.purple()
        )
        
        status_list = []
        for user_id, user_status in status_data[guild_id].items():
            set_at = datetime.fromisoformat(user_status['set_at'])
            time_ago = datetime.utcnow() - set_at
            
            status_text = f"**{user_status['username']}**: {user_status['status']}"
            if user_status['details']:
                status_text += f" - {user_status['details']}"
            status_text += f" ({format_duration(int(time_ago.total_seconds()))} ago)"
            
            status_list.append(status_text)
        
        # Split into chunks if too many statuses
        chunk_size = 10
        status_chunks = [status_list[i:i + chunk_size] for i in range(0, len(status_list), chunk_size)]
        
        for i, chunk in enumerate(status_chunks):
            embed.add_field(
                name=f"📋 Statuses {i+1}" if len(status_chunks) > 1 else "📋 Current Statuses",
                value="\n".join(chunk),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="timeout_info", description="Check timeout information for a user")
    @app_commands.describe(user="User to check timeout for")
    async def timeout_info(self, interaction: discord.Interaction, user: discord.Member):
        """Check timeout information for a user"""
        if not user.is_timed_out():
            await interaction.response.send_message(
                f"✅ {user.mention} is not currently timed out.",
                ephemeral=True
            )
            return
        
        time_left = user.timed_out_until - datetime.utcnow()
        
        embed = discord.Embed(
            title=f"⏰ Timeout Information - {user.display_name}",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="⏱️ Time Remaining",
            value=format_duration(int(time_left.total_seconds())),
            inline=True
        )
        
        embed.add_field(
            name="🔚 Timeout Ends",
            value=f"<t:{int(user.timed_out_until.timestamp())}:R>",
            inline=True
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Timeout started: {user.timed_out_until - timedelta(seconds=time_left.total_seconds())}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(FunCog(bot))