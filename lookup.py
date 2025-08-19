import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import logging
from bot.utils.helpers import create_embed
from urllib.parse import quote

logger = logging.getLogger(__name__)

class LookupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        
    async def cog_load(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession()
        
    async def cog_unload(self):
        """Clean up aiohttp session"""
        if self.session:
            await self.session.close()

    async def _make_request(self, url: str, headers: dict = None) -> dict:
        """Make HTTP request with error handling"""
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API request failed with status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None

    @app_commands.command(name="song", description="Look up song information using Last.fm")
    async def song_lookup(self, interaction: discord.Interaction, query: str):
        """Look up detailed song information from Last.fm"""
        await interaction.response.defer()
        
        # Trigger search animation
        if hasattr(self.bot, 'status_manager'):
            await self.bot.status_manager.trigger_search_animation()
        
        # Last.fm API endpoint (using public API without key for basic search)
        url = f"https://ws.audioscrobbler.com/2.0/?method=track.search&track={quote(query)}&api_key=b25b959554ed76058ac220b7b2e0a026&format=json&limit=1"
        
        data = await self._make_request(url)
        
        if not data or 'results' not in data or 'trackmatches' not in data['results']:
            embed = create_embed(
                "🎵 Song Not Found",
                f"No results found for '{query}'",
                discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
            
        tracks = data['results']['trackmatches']['track']
        if not tracks:
            embed = create_embed(
                "🎵 Song Not Found",
                f"No results found for '{query}'",
                discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
            
        # Get first track result
        if isinstance(tracks, list):
            track = tracks[0]
        else:
            track = tracks
            
        # Get detailed track info
        detail_url = f"https://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key=b25b959554ed76058ac220b7b2e0a026&artist={quote(track['artist'])}&track={quote(track['name'])}&format=json"
        detail_data = await self._make_request(detail_url)
        
        # Create animated title
        animated_title = f"🎵 {track['name']}"
        if hasattr(self.bot, 'status_manager'):
            animated_title = await self.bot.status_manager.create_animated_embed_title(track['name'], 'musical')
        
        embed = create_embed(
            animated_title,
            f"by **{track['artist']}**",
            discord.Color.blue()
        )
        
        # Add album info if available
        if 'album' in track and track['album']:
            embed.add_field(name="Album", value=track['album'], inline=True)
            
        # Add additional info from detailed response
        if detail_data and 'track' in detail_data:
            detail_track = detail_data['track']
            
            if 'playcount' in detail_track:
                embed.add_field(name="Play Count", value=f"{detail_track['playcount']:,}", inline=True)
                
            if 'listeners' in detail_track:
                embed.add_field(name="Listeners", value=f"{detail_track['listeners']:,}", inline=True)
                
            if 'duration' in detail_track and detail_track['duration']:
                duration_seconds = int(detail_track['duration']) // 1000
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
                
            if 'wiki' in detail_track and 'summary' in detail_track['wiki']:
                summary = detail_track['wiki']['summary']
                if summary:
                    # Clean up the summary
                    summary = summary.split('<a href')[0].strip()
                    if len(summary) > 200:
                        summary = summary[:197] + "..."
                    embed.add_field(name="About", value=summary, inline=False)
                    
            if 'url' in detail_track:
                embed.add_field(name="Last.fm Link", value=f"[View on Last.fm]({detail_track['url']})", inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="book", description="Look up book information using Open Library")
    async def book_lookup(self, interaction: discord.Interaction, query: str):
        """Look up detailed book information from Open Library"""
        await interaction.response.defer()
        
        # Trigger search animation and set feature status
        if hasattr(self.bot, 'status_manager'):
            await self.bot.status_manager.trigger_search_animation()
            await self.bot.status_manager.set_feature_status('book')
        
        # Open Library search API
        url = f"https://openlibrary.org/search.json?q={quote(query)}&limit=1"
        
        data = await self._make_request(url)
        
        if not data or 'docs' not in data or not data['docs']:
            embed = create_embed(
                "📚 Book Not Found",
                f"No results found for '{query}'",
                discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
            
        book = data['docs'][0]
        
        title = book.get('title', 'Unknown Title')
        author = book.get('author_name', ['Unknown Author'])[0] if book.get('author_name') else 'Unknown Author'
        
        # Create animated title
        animated_title = f"📚 {title}"
        if hasattr(self.bot, 'status_manager'):
            animated_title = await self.bot.status_manager.create_animated_embed_title(title, 'books')
        
        embed = create_embed(
            animated_title,
            f"by **{author}**",
            discord.Color.green()
        )
        
        # Add publication info
        if 'first_publish_year' in book:
            embed.add_field(name="First Published", value=str(book['first_publish_year']), inline=True)
            
        if 'publisher' in book and book['publisher']:
            publisher = book['publisher'][0] if isinstance(book['publisher'], list) else book['publisher']
            embed.add_field(name="Publisher", value=publisher, inline=True)
            
        if 'number_of_pages_median' in book:
            embed.add_field(name="Pages", value=str(book['number_of_pages_median']), inline=True)
            
        if 'language' in book and book['language']:
            languages = ', '.join(book['language'][:3])  # Show first 3 languages
            embed.add_field(name="Language(s)", value=languages, inline=True)
            
        if 'subject' in book and book['subject']:
            subjects = ', '.join(book['subject'][:5])  # Show first 5 subjects
            if len(subjects) > 200:
                subjects = subjects[:197] + "..."
            embed.add_field(name="Subjects", value=subjects, inline=False)
            
        # Add cover image if available
        if 'cover_i' in book:
            cover_url = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-M.jpg"
            embed.set_thumbnail(url=cover_url)
            
        # Add Open Library link
        if 'key' in book:
            embed.add_field(name="Open Library Link", value=f"[View on Open Library](https://openlibrary.org{book['key']})", inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="comic", description="Look up comic information using Comic Vine API")
    async def comic_lookup(self, interaction: discord.Interaction, query: str):
        """Look up comic information using Comic Vine API"""
        await interaction.response.defer()
        
        # Note: Comic Vine API requires authentication, using a fallback approach
        # This is a placeholder that would need API key configuration
        embed = create_embed(
            "🦸 Comic Lookup",
            "Comic lookup requires Comic Vine API access. Please provide your Comic Vine API key to enable this feature.",
            discord.Color.orange()
        )
        
        embed.add_field(
            name="How to get API Key",
            value="1. Visit [Comic Vine](https://comicvine.gamespot.com/api/)\n2. Create an account\n3. Request API access\n4. Contact bot admin with your API key",
            inline=False
        )
        
        # Alternative: Use a simple search approach
        embed.add_field(
            name="Alternative",
            value=f"Search for '{query}' on [Comic Vine](https://comicvine.gamespot.com/search/?q={quote(query)})",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="manga", description="Look up manga information using Jikan API")
    async def manga_lookup(self, interaction: discord.Interaction, query: str):
        """Look up manga information using Jikan API (MyAnimeList)"""
        await interaction.response.defer()
        
        # Trigger search animation and set feature status
        if hasattr(self.bot, 'status_manager'):
            await self.bot.status_manager.trigger_search_animation()
            await self.bot.status_manager.set_feature_status('manga')
        
        # Jikan API for manga search
        url = f"https://api.jikan.moe/v4/manga?q={quote(query)}&limit=1"
        
        data = await self._make_request(url)
        
        if not data or 'data' not in data or not data['data']:
            embed = create_embed(
                "📖 Manga Not Found",
                f"No results found for '{query}'",
                discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
            
        manga = data['data'][0]
        
        title = manga.get('title', 'Unknown Title')
        
        # Create animated title
        animated_title = f"📖 {title}"
        if hasattr(self.bot, 'status_manager'):
            animated_title = await self.bot.status_manager.create_animated_embed_title(title, 'pulsing')
        
        embed = create_embed(
            animated_title,
            manga.get('synopsis', 'No synopsis available')[:200] + "..." if manga.get('synopsis') and len(manga.get('synopsis', '')) > 200 else manga.get('synopsis', 'No synopsis available'),
            discord.Color.purple()
        )
        
        # Add manga details
        if 'authors' in manga and manga['authors']:
            authors = ', '.join([author['name'] for author in manga['authors'][:3]])
            embed.add_field(name="Author(s)", value=authors, inline=True)
            
        if 'status' in manga:
            embed.add_field(name="Status", value=manga['status'], inline=True)
            
        if 'chapters' in manga and manga['chapters']:
            embed.add_field(name="Chapters", value=str(manga['chapters']), inline=True)
            
        if 'volumes' in manga and manga['volumes']:
            embed.add_field(name="Volumes", value=str(manga['volumes']), inline=True)
            
        if 'published' in manga and manga['published']:
            pub_info = manga['published']
            if pub_info.get('from'):
                start_year = pub_info['from'][:4] if pub_info['from'] else "Unknown"
                end_year = pub_info['to'][:4] if pub_info.get('to') else "Ongoing"
                embed.add_field(name="Published", value=f"{start_year} - {end_year}", inline=True)
                
        if 'score' in manga and manga['score']:
            embed.add_field(name="Score", value=f"{manga['score']}/10", inline=True)
            
        if 'genres' in manga and manga['genres']:
            genres = ', '.join([genre['name'] for genre in manga['genres'][:5]])
            embed.add_field(name="Genres", value=genres, inline=False)
            
        # Add cover image
        if 'images' in manga and manga['images'].get('jpg', {}).get('image_url'):
            embed.set_thumbnail(url=manga['images']['jpg']['image_url'])
            
        # Add MyAnimeList link
        if 'url' in manga:
            embed.add_field(name="MyAnimeList Link", value=f"[View on MyAnimeList]({manga['url']})", inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="lookup_help", description="Show help for lookup commands")
    async def lookup_help(self, interaction: discord.Interaction):
        """Show help information for lookup commands"""
        embed = create_embed(
            "🔍 Lookup Commands Help",
            "Search for detailed information about songs, books, comics, and manga",
            discord.Color.blue()
        )
        
        embed.add_field(
            name="📱 Available Commands",
            value="• `/song <query>` - Search for song information\n"
                  "• `/book <query>` - Search for book information\n"
                  "• `/comic <query>` - Search for comic information\n"
                  "• `/manga <query>` - Search for manga information",
            inline=False
        )
        
        embed.add_field(
            name="🎵 Song Lookup",
            value="Uses Last.fm to find song details including:\n"
                  "• Artist and album information\n"
                  "• Play count and listener statistics\n"
                  "• Song duration and description\n"
                  "• Direct link to Last.fm page",
            inline=False
        )
        
        embed.add_field(
            name="📚 Book Lookup",
            value="Uses Open Library to find book details including:\n"
                  "• Author and publication information\n"
                  "• Page count and language\n"
                  "• Book cover image\n"
                  "• Subject categories and themes",
            inline=False
        )
        
        embed.add_field(
            name="📖 Manga Lookup",
            value="Uses MyAnimeList to find manga details including:\n"
                  "• Author and status information\n"
                  "• Chapter and volume count\n"
                  "• Score and genre information\n"
                  "• Cover image and synopsis",
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value="• Use specific titles for better results\n"
                  "• Try different search terms if not found\n"
                  "• Some APIs may have rate limits\n"
                  "• Comic lookup requires additional setup",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="system_status", description="Check bot status and animated features")
    async def system_status_check(self, interaction: discord.Interaction):
        """Check bot status and animated features"""
        if hasattr(self.bot, 'status_manager') and self.bot.status_manager:
            # Trigger celebration animation
            await self.bot.status_manager.trigger_celebration_animation()
            
            embed = create_embed(
                "🤖 Bot Status",
                "All systems operational with animated status indicators",
                discord.Color.green()
            )
            
            embed.add_field(
                name="🎬 Animated Status",
                value="✅ Active - Bot status changes automatically every 3 seconds",
                inline=False
            )
            
            embed.add_field(
                name="🔍 Lookup Features",
                value="• 🎵 Song lookup (Last.fm)\n• 📚 Book lookup (Open Library)\n• 📖 Manga lookup (MyAnimeList)\n• 🦸 Comic lookup (requires API key)",
                inline=False
            )
            
            embed.add_field(
                name="✨ Animation Features",
                value="• Dynamic status rotation\n• Search animations\n• Feature-specific status themes\n• Animated embed titles\n• Celebration effects",
                inline=False
            )
            
            # Add current status info
            current_activity = self.bot.activity
            if current_activity:
                embed.add_field(
                    name="📊 Current Status",
                    value=f"{current_activity.name}",
                    inline=False
                )
            
            # Add server info
            embed.add_field(
                name="🌐 Server Info",
                value=f"Connected to {len(self.bot.guilds)} server(s)",
                inline=True
            )
            
            # Add uptime info
            embed.add_field(
                name="⏰ Uptime",
                value="24/7 with keep-alive system",
                inline=True
            )
            
        else:
            embed = create_embed(
                "🤖 Bot Status",
                "Basic status - Animated features not available",
                discord.Color.orange()
            )
            
            embed.add_field(
                name="⚠️ Status System",
                value="Animated status system not initialized",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LookupCog(bot))