import random
import discord
from typing import Optional

class JarvisResponses:
    """Handle random Jarvis voice line responses"""
    
    def __init__(self):
        self.responses = [
            "Right away, sir.",
            "Of course, sir.",
            "Certainly, sir.",
            "At your service, sir.",
            "Consider it done, sir.",
            "Immediately, sir.",
            "Processing request, sir.",
            "Understood, sir.",
            "Very good, sir.",
            "Shall I render using the Mark VII armor?",
            "I'm sorry, I seem to have misplaced my invitation.",
            "Good morning, sir. How may I assist you?",
            "Systems online and ready, sir.",
            "Scanning for optimal solution, sir.",
            "Analysis complete, sir.",
            "Data retrieved successfully, sir.",
            "Task completed to specifications, sir.",
            "All systems are operational, sir.",
            "Initiating protocol, sir.",
            "Request acknowledged, sir.",
            "Working on it, sir.",
            "One moment please, sir.",
            "Accessing database, sir.",
            "Compiling results, sir.",
            "Mission parameters received, sir.",
            "Standing by for further instructions, sir.",
            "Shall I save this to your favorites, sir?",
            "Performing diagnostic scan, sir.",
            "Security protocols engaged, sir.",
            "Welcome home, sir.",
            "How may I be of assistance today, sir?",
            "Searching archives, sir.",
            "Calculating optimal response, sir.",
            "Systems are fully operational, sir.",
            "Recommend immediate action, sir.",
            "Threat assessment complete, sir.",
            "All clear, sir.",
            "Sensors indicate success, sir.",
            "Shall I prepare additional options, sir?",
            "Based on your previous preferences, sir...",
            "Might I suggest an alternative approach, sir?",
            "Analysis indicates this is the optimal choice, sir.",
            "Shall I continue monitoring, sir?",
            "Alert: New notification received, sir.",
            "Processing your request with priority, sir.",
            "Excellent choice, sir.",
            "That was surprisingly easy, sir.",
            "Mission accomplished, sir.",
            "Perhaps next time, sir.",
            "I'll put that on your calendar, sir."
        ]
        
        # Different response categories for different command types
        self.moderation_responses = [
            "Security protocols engaged, sir.",
            "Threat assessment complete, sir.",
            "Initiating defensive measures, sir.",
            "Order restored, sir.",
            "Compliance enforced, sir.",
            "Situation contained, sir."
        ]
        
        self.entertainment_responses = [
            "Shall I save this to your favorites, sir?",
            "Based on your previous preferences, sir...",
            "Accessing entertainment database, sir.",
            "Compiling recommendations, sir.",
            "Scanning for optimal content, sir."
        ]
        
        self.stats_responses = [
            "Analysis complete, sir.",
            "Data retrieved successfully, sir.",
            "Performing diagnostic scan, sir.",
            "Sensors indicate success, sir.",
            "Calculating optimal response, sir."
        ]
        
        self.fun_responses = [
            "That was surprisingly easy, sir.",
            "Excellent choice, sir.",
            "Perhaps next time, sir.",
            "Mission accomplished, sir.",
            "All clear, sir."
        ]
        
        self.music_responses = [
            "Now playing your selection, sir.",
            "Audio systems online, sir.",
            "Adjusting volume to optimal levels, sir.",
            "Playing your requested track, sir.",
            "Music library accessed, sir.",
            "Audio streaming initiated, sir.",
            "Sound quality optimized, sir.",
            "Playlist updated, sir.",
            "Connecting to audio systems, sir.",
            "Music controls ready, sir."
        ]
    
    def get_random_response(self, command_category: str = None) -> Optional[str]:
        """Get a random Jarvis response based on command category"""
        # 30% chance of responding (so it's not overwhelming)
        if random.random() > 0.3:
            return None
        
        if command_category == "moderation":
            responses = self.moderation_responses + self.responses
        elif command_category == "entertainment":
            responses = self.entertainment_responses + self.responses
        elif command_category == "stats":
            responses = self.stats_responses + self.responses
        elif command_category == "fun":
            responses = self.fun_responses + self.responses
        elif command_category == "music":
            responses = self.music_responses + self.responses
        else:
            responses = self.responses
        
        return random.choice(responses)
    
    def create_jarvis_embed(self, response: str) -> discord.Embed:
        """Create a styled embed for Jarvis responses"""
        embed = discord.Embed(
            description=f"*{response}*",
            color=discord.Color.blue()
        )
        embed.set_author(
            name="J.A.R.V.I.S.",
            icon_url="https://i.imgur.com/JvJgF7Y.png"  # Jarvis icon
        )
        return embed