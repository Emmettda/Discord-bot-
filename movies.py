import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime
from bot.utils.tmdb_client import TMDBClient

logger = logging.getLogger(__name__)

class MoviesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tmdb = TMDBClient()
    
    @app_commands.command(name="movie_info", description="Get information about a movie")
    @app_commands.describe(movie_name="Name of the movie to search for")
    async def movie_info(self, interaction: discord.Interaction, movie_name: str):
        """Get detailed information about a movie"""
        await interaction.response.defer()
        
        try:
            movie_data = await self.tmdb.search_movie(movie_name)
            
            if not movie_data:
                await interaction.followup.send(f"❌ Movie '{movie_name}' not found.")
                return
            
            # Get detailed movie info
            movie_details = await self.tmdb.get_movie_details(movie_data['id'])
            
            embed = discord.Embed(
                title=movie_details['title'],
                description=movie_details.get('overview', 'No description available'),
                color=discord.Color.blue(),
                url=f"https://www.themoviedb.org/movie/{movie_details['id']}"
            )
            
            # Add movie poster
            if movie_details.get('poster_path'):
                embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}")
            
            # Add movie details
            embed.add_field(
                name="📅 Release Date",
                value=movie_details.get('release_date', 'Unknown'),
                inline=True
            )
            
            embed.add_field(
                name="⭐ Rating",
                value=f"{movie_details.get('vote_average', 'N/A')}/10",
                inline=True
            )
            
            embed.add_field(
                name="🎭 Genres",
                value=", ".join([genre['name'] for genre in movie_details.get('genres', [])]) or 'Unknown',
                inline=True
            )
            
            embed.add_field(
                name="⏱️ Runtime",
                value=f"{movie_details.get('runtime', 'Unknown')} minutes",
                inline=True
            )
            
            embed.add_field(
                name="💰 Budget",
                value=f"${movie_details.get('budget', 0):,}" if movie_details.get('budget') else 'Unknown',
                inline=True
            )
            
            embed.add_field(
                name="💸 Revenue",
                value=f"${movie_details.get('revenue', 0):,}" if movie_details.get('revenue') else 'Unknown',
                inline=True
            )
            
            # Add cast information
            cast_info = await self.tmdb.get_movie_cast(movie_details['id'])
            if cast_info:
                cast_names = [actor['name'] for actor in cast_info[:5]]  # Top 5 actors
                embed.add_field(
                    name="🎬 Cast",
                    value=", ".join(cast_names),
                    inline=False
                )
            
            embed.set_footer(text="Data from The Movie Database (TMDB)")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting movie info: {e}")
            await interaction.followup.send(f"❌ Error retrieving movie information: {str(e)}")
    
    @app_commands.command(name="upcoming_movies", description="Get upcoming movies")
    @app_commands.describe(page="Page number (default: 1)")
    async def upcoming_movies(self, interaction: discord.Interaction, page: int = 1):
        """Get upcoming movies"""
        await interaction.response.defer()
        
        try:
            movies = await self.tmdb.get_upcoming_movies(page)
            
            if not movies:
                await interaction.followup.send("❌ No upcoming movies found.")
                return
            
            embed = discord.Embed(
                title="🎬 Upcoming Movies",
                description="Here are the upcoming movies:",
                color=discord.Color.green()
            )
            
            for movie in movies[:10]:  # Show top 10 movies
                embed.add_field(
                    name=movie['title'],
                    value=f"**Release:** {movie.get('release_date', 'TBA')}\n"
                          f"**Rating:** {movie.get('vote_average', 'N/A')}/10\n"
                          f"**Overview:** {movie.get('overview', 'No description')[:100]}...",
                    inline=False
                )
            
            embed.set_footer(text=f"Page {page} • Data from TMDB")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting upcoming movies: {e}")
            await interaction.followup.send(f"❌ Error retrieving upcoming movies: {str(e)}")
    
    @app_commands.command(name="popular_movies", description="Get popular movies")
    @app_commands.describe(page="Page number (default: 1)")
    async def popular_movies(self, interaction: discord.Interaction, page: int = 1):
        """Get popular movies"""
        await interaction.response.defer()
        
        try:
            movies = await self.tmdb.get_popular_movies(page)
            
            if not movies:
                await interaction.followup.send("❌ No popular movies found.")
                return
            
            embed = discord.Embed(
                title="🔥 Popular Movies",
                description="Here are the most popular movies:",
                color=discord.Color.red()
            )
            
            for movie in movies[:10]:  # Show top 10 movies
                embed.add_field(
                    name=movie['title'],
                    value=f"**Release:** {movie.get('release_date', 'TBA')}\n"
                          f"**Rating:** {movie.get('vote_average', 'N/A')}/10\n"
                          f"**Overview:** {movie.get('overview', 'No description')[:100]}...",
                    inline=False
                )
            
            embed.set_footer(text=f"Page {page} • Data from TMDB")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting popular movies: {e}")
            await interaction.followup.send(f"❌ Error retrieving popular movies: {str(e)}")
    
    @app_commands.command(name="movie_tickets", description="Find movie ticket information")
    @app_commands.describe(movie_name="Name of the movie", location="Your location (optional)")
    async def movie_tickets(self, interaction: discord.Interaction, movie_name: str, location: str = ""):
        """Find movie ticket information"""
        await interaction.response.defer()
        
        try:
            # First, get movie information
            movie_data = await self.tmdb.search_movie(movie_name)
            
            if not movie_data:
                await interaction.followup.send(f"❌ Movie '{movie_name}' not found.")
                return
            
            # Since we can't access real ticket APIs without additional services,
            # we'll provide guidance on where to find tickets
            embed = discord.Embed(
                title=f"🎫 Ticket Information for {movie_data['title']}",
                description="Here are popular platforms to find movie tickets:",
                color=discord.Color.purple()
            )
            
            # Add movie poster
            if movie_data.get('poster_path'):
                embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}")
            
            # Add ticket platforms
            embed.add_field(
                name="🎬 Popular Ticket Platforms",
                value="• **Fandango** - fandango.com\n"
                      "• **AMC Theatres** - amctheatres.com\n"
                      "• **Regal Cinemas** - regmovies.com\n"
                      "• **Cinemark** - cinemark.com\n"
                      "• **Atom Tickets** - atomtickets.com",
                inline=False
            )
            
            embed.add_field(
                name="💡 Tips for Finding Tickets",
                value="• Check showtimes at your local theater\n"
                      "• Compare prices across different platforms\n"
                      "• Look for matinee or discount pricing\n"
                      "• Consider theater membership programs\n"
                      "• Book early for popular movies",
                inline=False
            )
            
            # Add movie details
            embed.add_field(
                name="📅 Release Date",
                value=movie_data.get('release_date', 'Unknown'),
                inline=True
            )
            
            embed.add_field(
                name="⭐ Rating",
                value=f"{movie_data.get('vote_average', 'N/A')}/10",
                inline=True
            )
            
            if location:
                embed.add_field(
                    name="📍 Location",
                    value=f"Searching near: {location}",
                    inline=True
                )
            
            embed.set_footer(text="Use these platforms to find actual ticket prices and showtimes")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting ticket info: {e}")
            await interaction.followup.send(f"❌ Error retrieving ticket information: {str(e)}")
