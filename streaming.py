import discord
from discord.ext import commands
from discord import app_commands
import logging
import random

logger = logging.getLogger(__name__)

class StreamingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Best streaming sites for different content types
        self.streaming_sites = {
            "movies": [
                "🎬 **FMovies** - fmovies.to (HD movies, latest releases)",
                "🎬 **SolarMovie** - solarmovie.pe (extensive movie library)",
                "🎬 **123Movies** - 123movies.gs (popular movies and TV)",
                "🎬 **GoMovies** - gomovies.sx (high quality streams)",
                "🎬 **PutLocker** - putlocker.vip (reliable streaming)",
                "🎬 **Movies7** - movies7.to (newest movies)",
                "🎬 **WatchSeries** - watchseries.mn (movies and series)"
            ],
            "tv_shows": [
                "📺 **WatchSeries** - watchseries.mn (all TV shows)",
                "📺 **TVMuse** - tvmuse.cc (TV series database)",
                "📺 **Series9** - series9.la (TV shows and episodes)",
                "📺 **WatchEpisodes** - watchepisodes4.com (episode streaming)",
                "📺 **CouchTuner** - couchtuner.show (TV series)",
                "📺 **ProjectFreeTV** - projectfreetv.fun (free TV shows)",
                "📺 **StreamM4U** - streamm4u.ws (TV and movies)"
            ],
            "anime": [
                "🌸 **9Anime** - 9anime.pe (largest anime collection)",
                "🌸 **GogoAnime** - gogoanime3.co (HD anime streaming)",
                "🌸 **AnimeFLV** - animeflv.net (Spanish and English anime)",
                "🌸 **KissAnime** - kissanime.ru (classic anime site)",
                "🌸 **AnimeDao** - animedao.to (anime movies and series)",
                "🌸 **Zoro** - zoro.to (high quality anime)",
                "🌸 **AnimeSuge** - animesuge.to (fast streaming)"
            ],
            "all": [
                "🌟 **Soap2Day** - soap2day.ac (movies, TV, anime)",
                "🌟 **FlixHQ** - flixhq.to (all content types)",
                "🌟 **FBox** - fbox.to (movies, series, anime)",
                "🌟 **HDToday** - hdtoday.tv (HD content)",
                "🌟 **Movie4K** - movie4k.pe (comprehensive library)",
                "🌟 **AZMovies** - azmovies.net (all entertainment)",
                "🌟 **YesMovies** - yesmovies.ag (everything in one place)"
            ]
        }
        
        # Additional specialized sites
        self.specialized_sites = {
            "live_tv": [
                "📡 **USTVGO** - ustvgo.tv (US live TV channels)",
                "📡 **Stream2Watch** - stream2watch.ws (live sports and TV)",
                "📡 **LiveTV** - livetv.sx (international live TV)"
            ],
            "sports": [
                "⚽ **CrackStreams** - crackstreams.biz (live sports)",
                "⚽ **StreamEast** - streameast.xyz (sports streaming)",
                "⚽ **VIPLeague** - vipleague.lc (sports events)"
            ],
            "documentaries": [
                "🎓 **Documentary Heaven** - documentaryheaven.com",
                "🎓 **Top Documentary Films** - topdocumentaryfilms.com",
                "🎓 **DocuBay** - alternative documentary sources"
            ]
        }

    @app_commands.command(name="streaming_sites", description="Get the best streaming sites for movies, TV shows, and anime")
    @app_commands.describe(content_type="Type of content (movies/tv_shows/anime/all/live_tv/sports/documentaries)")
    async def streaming_sites(self, interaction: discord.Interaction, content_type: str = "all"):
        """Get the best streaming sites for different content types"""
        content_type = content_type.lower().replace(" ", "_")
        
        # Create embed based on content type
        if content_type in self.streaming_sites:
            sites = self.streaming_sites[content_type]
            title = f"🎯 Best Streaming Sites - {content_type.replace('_', ' ').title()}"
            color = discord.Color.purple()
        elif content_type in self.specialized_sites:
            sites = self.specialized_sites[content_type]
            title = f"🎯 Best Streaming Sites - {content_type.replace('_', ' ').title()}"
            color = discord.Color.orange()
        else:
            # Show all categories
            embed = discord.Embed(
                title="🎯 Premium Streaming Sites Directory",
                description="Choose a category to see the best streaming sites:",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="🎬 Movies",
                value="Use: `/streaming_sites movies`",
                inline=True
            )
            embed.add_field(
                name="📺 TV Shows",
                value="Use: `/streaming_sites tv_shows`",
                inline=True
            )
            embed.add_field(
                name="🌸 Anime",
                value="Use: `/streaming_sites anime`",
                inline=True
            )
            embed.add_field(
                name="🌟 All Content",
                value="Use: `/streaming_sites all`",
                inline=True
            )
            embed.add_field(
                name="📡 Live TV",
                value="Use: `/streaming_sites live_tv`",
                inline=True
            )
            embed.add_field(
                name="⚽ Sports",
                value="Use: `/streaming_sites sports`",
                inline=True
            )
            
            embed.set_footer(text="⚠️ Use these sites responsibly. Consider legal alternatives when available.")
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=title,
            description=f"Here are the top streaming sites for {content_type.replace('_', ' ')}:",
            color=color
        )
        
        # Add sites to embed
        sites_text = "\n".join(sites)
        embed.add_field(
            name="🔗 Recommended Sites",
            value=sites_text,
            inline=False
        )
        
        # Add safety tips
        embed.add_field(
            name="🛡️ Safety Tips",
            value="• Use a VPN for privacy\n• Enable ad-blocker\n• Don't download suspicious files\n• Check site legitimacy",
            inline=False
        )
        
        embed.set_footer(text="⚠️ These sites are for informational purposes. Use responsibly and consider legal alternatives.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="random_streaming", description="Get a random streaming site recommendation")
    async def random_streaming(self, interaction: discord.Interaction):
        """Get a random streaming site from all categories"""
        all_sites = []
        for category, sites in self.streaming_sites.items():
            all_sites.extend(sites)
        for category, sites in self.specialized_sites.items():
            all_sites.extend(sites)
        
        random_site = random.choice(all_sites)
        
        embed = discord.Embed(
            title="🎲 Random Streaming Site",
            description=f"Here's a random streaming recommendation:\n\n{random_site}",
            color=discord.Color.random()
        )
        embed.set_footer(text="🎯 Try /streaming_sites [category] for more options!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(StreamingCog(bot))