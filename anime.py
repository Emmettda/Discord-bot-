import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class AnimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Popular anime database (can be expanded)
        self.anime_database = {
            "action": [
                {"name": "Attack on Titan", "genre": "Action, Drama", "rating": 9.0, "year": 2013, "episodes": 75, "streaming": ["Crunchyroll", "Funimation", "Hulu"]},
                {"name": "Demon Slayer", "genre": "Action, Supernatural", "rating": 8.7, "year": 2019, "episodes": 44, "streaming": ["Crunchyroll", "Funimation", "Netflix"]},
                {"name": "One Piece", "genre": "Action, Adventure", "rating": 9.0, "year": 1999, "episodes": 1000, "streaming": ["Crunchyroll", "Funimation", "Netflix"]},
                {"name": "Naruto", "genre": "Action, Martial Arts", "rating": 8.4, "year": 2002, "episodes": 720, "streaming": ["Crunchyroll", "Funimation", "Hulu"]},
                {"name": "Dragon Ball Z", "genre": "Action, Martial Arts", "rating": 8.8, "year": 1989, "episodes": 291, "streaming": ["Crunchyroll", "Funimation", "Hulu"]},
                {"name": "My Hero Academia", "genre": "Action, School", "rating": 8.5, "year": 2016, "episodes": 138, "streaming": ["Crunchyroll", "Funimation", "Hulu"]},
                {"name": "Jujutsu Kaisen", "genre": "Action, Supernatural", "rating": 8.6, "year": 2020, "episodes": 24, "streaming": ["Crunchyroll", "Funimation"]},
                {"name": "Hunter x Hunter", "genre": "Action, Adventure", "rating": 9.1, "year": 2011, "episodes": 148, "streaming": ["Crunchyroll", "Netflix"]}
            ],
            "romance": [
                {"name": "Your Name", "genre": "Romance, Drama", "rating": 8.2, "year": 2016, "episodes": 1, "streaming": ["Crunchyroll", "Funimation", "Netflix"]},
                {"name": "A Silent Voice", "genre": "Romance, Drama", "rating": 8.1, "year": 2016, "episodes": 1, "streaming": ["Netflix", "Crunchyroll"]},
                {"name": "Toradora!", "genre": "Romance, Comedy", "rating": 8.1, "year": 2008, "episodes": 25, "streaming": ["Crunchyroll", "Funimation"]},
                {"name": "Kaguya-sama: Love is War", "genre": "Romance, Comedy", "rating": 8.4, "year": 2019, "episodes": 37, "streaming": ["Crunchyroll", "Funimation"]},
                {"name": "Your Lie in April", "genre": "Romance, Music", "rating": 8.6, "year": 2014, "episodes": 22, "streaming": ["Crunchyroll", "Netflix"]},
                {"name": "Clannad", "genre": "Romance, Drama", "rating": 8.0, "year": 2007, "episodes": 47, "streaming": ["Crunchyroll", "Funimation"]}
            ],
            "comedy": [
                {"name": "One Punch Man", "genre": "Comedy, Action", "rating": 8.8, "year": 2015, "episodes": 24, "streaming": ["Crunchyroll", "Funimation", "Netflix"]},
                {"name": "Gintama", "genre": "Comedy, Action", "rating": 9.0, "year": 2006, "episodes": 367, "streaming": ["Crunchyroll", "Funimation"]},
                {"name": "Konosuba", "genre": "Comedy, Fantasy", "rating": 8.1, "year": 2016, "episodes": 20, "streaming": ["Crunchyroll", "Funimation"]},
                {"name": "The Disastrous Life of Saiki K.", "genre": "Comedy, School", "rating": 8.4, "year": 2016, "episodes": 120, "streaming": ["Netflix", "Funimation"]},
                {"name": "Mob Psycho 100", "genre": "Comedy, Supernatural", "rating": 8.7, "year": 2016, "episodes": 37, "streaming": ["Crunchyroll", "Funimation"]}
            ],
            "thriller": [
                {"name": "Death Note", "genre": "Thriller, Supernatural", "rating": 9.0, "year": 2006, "episodes": 37, "streaming": ["Netflix", "Crunchyroll", "Funimation"]},
                {"name": "Monster", "genre": "Thriller, Drama", "rating": 9.0, "year": 2004, "episodes": 74, "streaming": ["Netflix", "Crunchyroll"]},
                {"name": "Psycho-Pass", "genre": "Thriller, Sci-Fi", "rating": 8.2, "year": 2012, "episodes": 41, "streaming": ["Crunchyroll", "Funimation"]},
                {"name": "Steins;Gate", "genre": "Thriller, Sci-Fi", "rating": 8.8, "year": 2011, "episodes": 24, "streaming": ["Crunchyroll", "Funimation"]},
                {"name": "Paranoia Agent", "genre": "Thriller, Mystery", "rating": 8.0, "year": 2004, "episodes": 13, "streaming": ["Crunchyroll", "Funimation"]}
            ],
            "slice_of_life": [
                {"name": "Spirited Away", "genre": "Slice of Life, Fantasy", "rating": 9.3, "year": 2001, "episodes": 1, "streaming": ["Netflix", "HBO Max"]},
                {"name": "My Neighbor Totoro", "genre": "Slice of Life, Family", "rating": 8.2, "year": 1988, "episodes": 1, "streaming": ["Netflix", "HBO Max"]},
                {"name": "Violet Evergarden", "genre": "Slice of Life, Drama", "rating": 8.5, "year": 2018, "episodes": 13, "streaming": ["Netflix", "Crunchyroll"]},
                {"name": "K-On!", "genre": "Slice of Life, Music", "rating": 7.8, "year": 2009, "episodes": 39, "streaming": ["Crunchyroll", "Funimation"]},
                {"name": "Barakamon", "genre": "Slice of Life, Comedy", "rating": 8.3, "year": 2014, "episodes": 12, "streaming": ["Crunchyroll", "Funimation"]}
            ]
        }
        
        # Streaming platform emojis
        self.streaming_emojis = {
            "Crunchyroll": "🟠",
            "Funimation": "🟣",
            "Netflix": "🔴",
            "Hulu": "🟢",
            "HBO Max": "🟡",
            "Amazon Prime": "🔵",
            "Disney+": "⚪"
        }
    
    def _format_streaming_platforms(self, platforms):
        """Format streaming platforms with emojis"""
        if not platforms:
            return "Not available"
        
        formatted = []
        for platform in platforms:
            emoji = self.streaming_emojis.get(platform, "📺")
            formatted.append(f"{emoji} {platform}")
        
        return " | ".join(formatted)
    
    @app_commands.command(name="anime_recommend", description="Get anime recommendations")
    @app_commands.describe(genre="Genre preference (action, romance, comedy, thriller, slice_of_life)")
    async def anime_recommend(self, interaction: discord.Interaction, genre: str = ""):
        """Get anime recommendations based on genre"""
        await interaction.response.defer()
        
        try:
            if genre.lower() in self.anime_database:
                anime_list = self.anime_database[genre.lower()]
                recommendations = random.sample(anime_list, min(5, len(anime_list)))
                title = f"🎌 {genre.title()} Anime Recommendations"
            else:
                # Random recommendations from all genres
                all_anime = []
                for genre_list in self.anime_database.values():
                    all_anime.extend(genre_list)
                recommendations = random.sample(all_anime, min(5, len(all_anime)))
                title = "🎌 Random Anime Recommendations"
            
            embed = discord.Embed(
                title=title,
                description="Here are some great anime recommendations for you:",
                color=discord.Color.purple()
            )
            
            for anime in recommendations:
                streaming_info = self._format_streaming_platforms(anime.get('streaming', []))
                embed.add_field(
                    name=anime['name'],
                    value=f"**Genre:** {anime['genre']}\n"
                          f"**Rating:** {anime['rating']}/10\n"
                          f"**Year:** {anime['year']}\n"
                          f"**Episodes:** {anime['episodes']}\n"
                          f"**Streaming:** {streaming_info}",
                    inline=True
                )
            
            embed.set_footer(text="Happy watching! 🍿")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting anime recommendations: {e}")
            await interaction.followup.send(f"❌ Error getting recommendations: {str(e)}")
    
    @app_commands.command(name="anime_search", description="Search for anime information")
    @app_commands.describe(anime_name="Name of the anime to search for")
    async def anime_search(self, interaction: discord.Interaction, anime_name: str):
        """Search for specific anime information"""
        await interaction.response.defer()
        
        try:
            # Search through our database
            found_anime = None
            for genre_list in self.anime_database.values():
                for anime in genre_list:
                    if anime_name.lower() in anime['name'].lower():
                        found_anime = anime
                        break
                if found_anime:
                    break
            
            if not found_anime:
                embed = discord.Embed(
                    title="❌ Anime Not Found",
                    description=f"Sorry, '{anime_name}' was not found in our database.",
                    color=discord.Color.red()
                )
                
                embed.add_field(
                    name="💡 Suggestions",
                    value="• Try using `/anime_recommend` for random suggestions\n"
                          "• Check spelling and try again\n"
                          "• Use `/anime_popular` to see trending anime",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"🎌 {found_anime['name']}",
                description="Here's what I found about this anime:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="🎭 Genre",
                value=found_anime['genre'],
                inline=True
            )
            
            embed.add_field(
                name="⭐ Rating",
                value=f"{found_anime['rating']}/10",
                inline=True
            )
            
            embed.add_field(
                name="📅 Year",
                value=found_anime['year'],
                inline=True
            )
            
            embed.add_field(
                name="📺 Episodes",
                value=found_anime['episodes'],
                inline=True
            )
            
            # Add streaming information
            streaming_info = self._format_streaming_platforms(found_anime.get('streaming', []))
            embed.add_field(
                name="🎬 Available On",
                value=streaming_info,
                inline=False
            )
            
            # Add recommendation based on genre
            similar_anime = []
            for genre_list in self.anime_database.values():
                for anime in genre_list:
                    if anime != found_anime and any(g in anime['genre'] for g in found_anime['genre'].split(', ')):
                        similar_anime.append(anime['name'])
            
            if similar_anime:
                embed.add_field(
                    name="💡 Similar Anime",
                    value=", ".join(similar_anime[:3]),
                    inline=False
                )
            
            embed.set_footer(text="Use /anime_recommend for more suggestions!")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error searching anime: {e}")
            await interaction.followup.send(f"❌ Error searching anime: {str(e)}")
    
    @app_commands.command(name="anime_popular", description="Get popular anime")
    async def anime_popular(self, interaction: discord.Interaction):
        """Get popular anime"""
        await interaction.response.defer()
        
        try:
            # Get top rated anime from all genres
            all_anime = []
            for genre_list in self.anime_database.values():
                all_anime.extend(genre_list)
            
            # Sort by rating and get top 8
            popular_anime = sorted(all_anime, key=lambda x: x['rating'], reverse=True)[:8]
            
            embed = discord.Embed(
                title="🔥 Popular Anime",
                description="Here are the most popular anime based on ratings:",
                color=discord.Color.gold()
            )
            
            for i, anime in enumerate(popular_anime, 1):
                embed.add_field(
                    name=f"{i}. {anime['name']}",
                    value=f"**Genre:** {anime['genre']}\n"
                          f"**Rating:** {anime['rating']}/10\n"
                          f"**Year:** {anime['year']}\n"
                          f"**Episodes:** {anime['episodes']}",
                    inline=True
                )
            
            embed.set_footer(text="Rankings based on community ratings")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting popular anime: {e}")
            await interaction.followup.send(f"❌ Error getting popular anime: {str(e)}")
    
    @app_commands.command(name="anime_genres", description="List available anime genres")
    async def anime_genres(self, interaction: discord.Interaction):
        """List available anime genres"""
        embed = discord.Embed(
            title="🎌 Available Anime Genres",
            description="Here are the genres you can search for:",
            color=discord.Color.purple()
        )
        
        for genre in self.anime_database.keys():
            anime_count = len(self.anime_database[genre])
            embed.add_field(
                name=genre.replace('_', ' ').title(),
                value=f"{anime_count} anime available",
                inline=True
            )
        
        embed.add_field(
            name="💡 How to Use",
            value="Use `/anime_recommend genre:action` to get recommendations from a specific genre!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="anime_streaming", description="Find anime by streaming platform")
    @app_commands.describe(platform="Streaming platform (Netflix, Crunchyroll, Funimation, Hulu, etc.)")
    async def anime_streaming(self, interaction: discord.Interaction, platform: str):
        """Find anime available on a specific streaming platform"""
        await interaction.response.defer()
        
        try:
            platform_anime = []
            
            # Search through all anime for the specified platform
            for genre_list in self.anime_database.values():
                for anime in genre_list:
                    if 'streaming' in anime:
                        # Case-insensitive search for platform
                        if any(platform.lower() in p.lower() for p in anime['streaming']):
                            platform_anime.append(anime)
            
            if not platform_anime:
                embed = discord.Embed(
                    title=f"❌ No Anime Found on {platform}",
                    description=f"Sorry, no anime found for '{platform}' in our database.",
                    color=discord.Color.red()
                )
                
                available_platforms = set()
                for genre_list in self.anime_database.values():
                    for anime in genre_list:
                        if 'streaming' in anime:
                            available_platforms.update(anime['streaming'])
                
                embed.add_field(
                    name="📺 Available Platforms",
                    value=", ".join(sorted(available_platforms)),
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                return
            
            # Sort by rating and limit to top 10
            platform_anime.sort(key=lambda x: x['rating'], reverse=True)
            platform_anime = platform_anime[:10]
            
            embed = discord.Embed(
                title=f"📺 Anime on {platform}",
                description=f"Here are the top anime available on {platform}:",
                color=discord.Color.blue()
            )
            
            for anime in platform_anime:
                streaming_info = self._format_streaming_platforms(anime.get('streaming', []))
                embed.add_field(
                    name=f"{anime['name']} ({anime['rating']}/10)",
                    value=f"**Genre:** {anime['genre']}\n"
                          f"**Year:** {anime['year']}\n"
                          f"**Episodes:** {anime['episodes']}\n"
                          f"**Streaming:** {streaming_info}",
                    inline=True
                )
            
            embed.set_footer(text=f"Found {len(platform_anime)} anime on {platform}")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error searching anime by platform: {e}")
            await interaction.followup.send(f"❌ Error searching anime by platform: {str(e)}")
    
    @app_commands.command(name="anime_platforms", description="View all available streaming platforms")
    async def anime_platforms(self, interaction: discord.Interaction):
        """View all available streaming platforms"""
        try:
            # Collect all platforms from database
            platforms = {}
            for genre_list in self.anime_database.values():
                for anime in genre_list:
                    if 'streaming' in anime:
                        for platform in anime['streaming']:
                            if platform not in platforms:
                                platforms[platform] = []
                            platforms[platform].append(anime['name'])
            
            embed = discord.Embed(
                title="📺 Available Streaming Platforms",
                description="Here are all the streaming platforms in our database:",
                color=discord.Color.green()
            )
            
            for platform, anime_list in sorted(platforms.items()):
                emoji = self.streaming_emojis.get(platform, "📺")
                embed.add_field(
                    name=f"{emoji} {platform}",
                    value=f"{len(anime_list)} anime available\n"
                          f"Use `/anime_streaming platform:{platform}` to browse",
                    inline=True
                )
            
            embed.set_footer(text="Click on a platform to see available anime!")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting streaming platforms: {e}")
            await interaction.response.send_message(f"❌ Error getting streaming platforms: {str(e)}")
    
    @app_commands.command(name="anime_where_to_watch", description="Find where to watch a specific anime")
    @app_commands.describe(anime_name="Name of the anime to find streaming platforms for")
    async def anime_where_to_watch(self, interaction: discord.Interaction, anime_name: str):
        """Find where to watch a specific anime"""
        await interaction.response.defer()
        
        try:
            found_anime = None
            for genre_list in self.anime_database.values():
                for anime in genre_list:
                    if anime_name.lower() in anime['name'].lower():
                        found_anime = anime
                        break
                if found_anime:
                    break
            
            if not found_anime:
                embed = discord.Embed(
                    title="❌ Anime Not Found",
                    description=f"Sorry, '{anime_name}' was not found in our database.",
                    color=discord.Color.red()
                )
                
                embed.add_field(
                    name="💡 Suggestions",
                    value="• Try using `/anime_search` to find similar anime\n"
                          "• Check spelling and try again\n"
                          "• Use `/anime_platforms` to see all available platforms",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                return
            
            streaming_info = self._format_streaming_platforms(found_anime.get('streaming', []))
            
            embed = discord.Embed(
                title=f"📺 Where to Watch: {found_anime['name']}",
                description="Here's where you can stream this anime:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="🎭 Genre",
                value=found_anime['genre'],
                inline=True
            )
            
            embed.add_field(
                name="⭐ Rating",
                value=f"{found_anime['rating']}/10",
                inline=True
            )
            
            embed.add_field(
                name="📅 Year",
                value=found_anime['year'],
                inline=True
            )
            
            embed.add_field(
                name="📺 Episodes",
                value=found_anime['episodes'],
                inline=True
            )
            
            embed.add_field(
                name="🎬 Available On",
                value=streaming_info,
                inline=False
            )
            
            embed.set_footer(text="Happy watching! 🍿")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error finding where to watch anime: {e}")
            await interaction.followup.send(f"❌ Error finding where to watch anime: {str(e)}")
