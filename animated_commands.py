import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import logging
from bot.utils.helpers import create_embed

logger = logging.getLogger(__name__)

class AnimatedCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="animate", description="Trigger specific animation sequences")
    @app_commands.describe(
        animation="Choose an animation type",
        duration="Duration in seconds (default: 10)"
    )
    @app_commands.choices(animation=[
        app_commands.Choice(name="🔍 Search", value="search"),
        app_commands.Choice(name="⏳ Loading", value="loading"),
        app_commands.Choice(name="🎉 Celebration", value="celebration"),
        app_commands.Choice(name="🎵 Music", value="music"),
        app_commands.Choice(name="📚 Books", value="books"),
        app_commands.Choice(name="📖 Manga", value="manga"),
        app_commands.Choice(name="🎮 Gaming", value="gaming"),
        app_commands.Choice(name="😴 Idle", value="idle"),
    ])
    async def animate_status(self, interaction: discord.Interaction, animation: str, duration: int = 10):
        """Trigger specific animation sequences"""
        if not hasattr(self.bot, 'status_manager') or not self.bot.status_manager:
            await interaction.response.send_message("❌ Animated status system not available", ephemeral=True)
            return
        
        # Validate duration
        if duration < 5 or duration > 300:
            await interaction.response.send_message("❌ Duration must be between 5 and 300 seconds", ephemeral=True)
            return
        
        # Trigger the animation
        await self.bot.status_manager.set_sequence(animation, duration)
        
        # Create response embed
        animation_names = {
            'search': '🔍 Search Animation',
            'loading': '⏳ Loading Animation',
            'celebration': '🎉 Celebration Animation',
            'music': '🎵 Music Animation',
            'books': '📚 Books Animation',
            'manga': '📖 Manga Animation',
            'gaming': '🎮 Gaming Animation',
            'idle': '😴 Idle Animation'
        }
        
        embed = create_embed(
            f"✨ {animation_names.get(animation, 'Animation')} Started",
            f"Running for {duration} seconds, then returning to default rotation",
            discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(name="status_info", description="View detailed status system information")
    async def status_info(self, interaction: discord.Interaction):
        """View detailed status system information"""
        if not hasattr(self.bot, 'status_manager') or not self.bot.status_manager:
            await interaction.response.send_message("❌ Animated status system not available", ephemeral=True)
            return
        
        status_mgr = self.bot.status_manager
        
        embed = create_embed(
            "📊 Status System Information",
            "Detailed information about the animated status system",
            discord.Color.blue()
        )
        
        # Current sequence info
        embed.add_field(
            name="🔄 Current Sequence",
            value=f"**{status_mgr.current_sequence.title()}**\nStep {status_mgr.current_status_index + 1} of {len(status_mgr.status_sequences[status_mgr.current_sequence])}",
            inline=True
        )
        
        # Animation speed
        embed.add_field(
            name="⏱️ Animation Speed",
            value=f"{status_mgr.animation_speed} seconds per status",
            inline=True
        )
        
        # System status
        embed.add_field(
            name="🟢 System Status",
            value="Running" if status_mgr.is_running else "Stopped",
            inline=True
        )
        
        # Available sequences
        sequences = list(status_mgr.status_sequences.keys())
        embed.add_field(
            name="🎬 Available Sequences",
            value=f"**{len(sequences)} sequences:**\n" + ", ".join(sequences),
            inline=False
        )
        
        # Current bot activity
        if self.bot.activity:
            embed.add_field(
                name="📱 Current Activity",
                value=f"**{self.bot.activity.type.name.title()}:** {self.bot.activity.name}",
                inline=False
            )
        
        # Animation types
        embed.add_field(
            name="✨ Animation Types",
            value="• **Musical**: 🎵 🎶 🎼 🎹 🎸 🥁\n• **Books**: 📚 📖 📝 📄 📜 📋\n• **Search**: 🔍 🔎 🕵️ 🔬 📡 ⚡\n• **Loading**: ⚪ 🔵 🔴 🟡 🟢 🟣\n• **Spinning**: ◐ ◓ ◑ ◒\n• **Pulsing**: 🔆 🔅 💫 ⭐ ✨ 🌟",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="status_control", description="Control the animated status system")
    @app_commands.describe(action="Action to perform")
    @app_commands.choices(action=[
        app_commands.Choice(name="▶️ Start", value="start"),
        app_commands.Choice(name="⏸️ Stop", value="stop"),
        app_commands.Choice(name="🔄 Restart", value="restart"),
        app_commands.Choice(name="🏠 Reset to Default", value="reset")
    ])
    @app_commands.default_permissions(administrator=True)
    async def status_control(self, interaction: discord.Interaction, action: str):
        """Control the animated status system (Admin only)"""
        if not hasattr(self.bot, 'status_manager') or not self.bot.status_manager:
            await interaction.response.send_message("❌ Animated status system not available", ephemeral=True)
            return
        
        status_mgr = self.bot.status_manager
        
        try:
            if action == "start":
                await status_mgr.start_animated_status()
                message = "▶️ Started animated status system"
                color = discord.Color.green()
                
            elif action == "stop":
                await status_mgr.stop_animated_status()
                message = "⏸️ Stopped animated status system"
                color = discord.Color.red()
                
            elif action == "restart":
                await status_mgr.stop_animated_status()
                await asyncio.sleep(1)
                await status_mgr.start_animated_status()
                message = "🔄 Restarted animated status system"
                color = discord.Color.blue()
                
            elif action == "reset":
                status_mgr.current_sequence = 'default'
                status_mgr.current_status_index = 0
                message = "🏠 Reset to default sequence"
                color = discord.Color.orange()
            
            embed = create_embed(
                "⚙️ Status Control",
                message,
                color
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error controlling status system: {e}")
            await interaction.response.send_message("❌ Error controlling status system", ephemeral=True)
    
    @app_commands.command(name="demo_animations", description="Demonstrate all animation types")
    async def demo_animations(self, interaction: discord.Interaction):
        """Demonstrate all animation types"""
        if not hasattr(self.bot, 'status_manager') or not self.bot.status_manager:
            await interaction.response.send_message("❌ Animated status system not available", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        status_mgr = self.bot.status_manager
        
        # Demo sequence
        demo_sequence = ['search', 'loading', 'music', 'books', 'manga', 'gaming', 'celebration']
        
        embed = create_embed(
            "🎬 Animation Demo Started",
            f"Demonstrating {len(demo_sequence)} animation types (5 seconds each)",
            discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Demo Sequence",
            value=" → ".join([seq.title() for seq in demo_sequence]),
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
        # Run demo
        for i, animation in enumerate(demo_sequence):
            await status_mgr.set_sequence(animation, 5)
            
            # Update progress
            progress_embed = create_embed(
                f"🎭 Demo Progress ({i+1}/{len(demo_sequence)})",
                f"Currently showing: **{animation.title()}** animation",
                discord.Color.blue()
            )
            
            try:
                await interaction.edit_original_response(embed=progress_embed)
            except:
                pass
            
            await asyncio.sleep(5)
        
        # Reset to default
        status_mgr.current_sequence = 'default'
        status_mgr.current_status_index = 0
        
        final_embed = create_embed(
            "✅ Demo Complete",
            "All animations demonstrated. Status reset to default rotation.",
            discord.Color.green()
        )
        
        try:
            await interaction.edit_original_response(embed=final_embed)
        except:
            pass

async def setup(bot):
    await bot.add_cog(AnimatedCommandsCog(bot))