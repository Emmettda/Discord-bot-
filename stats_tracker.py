import json
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class StatsTracker:
    def __init__(self):
        self.data_dir = "data"
        self.stats_file = os.path.join(self.data_dir, "user_stats.json")
        self.message_stats_file = os.path.join(self.data_dir, "message_stats.json")
        self.command_stats_file = os.path.join(self.data_dir, "command_stats.json")
        
        # Initialize data files
        self._init_file(self.stats_file, {})
        self._init_file(self.message_stats_file, {})
        self._init_file(self.command_stats_file, {})
        
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
    
    def track_message(self, user_id: int, guild_id: int, channel_id: int, message_length: int):
        """Track user message activity"""
        stats = self._read_json(self.message_stats_file)
        
        user_key = str(user_id)
        guild_key = str(guild_id)
        
        if user_key not in stats:
            stats[user_key] = {}
        
        if guild_key not in stats[user_key]:
            stats[user_key][guild_key] = {
                "total_messages": 0,
                "total_characters": 0,
                "channels": {},
                "daily_activity": {},
                "first_message": datetime.utcnow().isoformat(),
                "last_message": datetime.utcnow().isoformat()
            }
        
        guild_stats = stats[user_key][guild_key]
        
        # Update totals
        guild_stats["total_messages"] += 1
        guild_stats["total_characters"] += message_length
        guild_stats["last_message"] = datetime.utcnow().isoformat()
        
        # Track channel activity
        channel_key = str(channel_id)
        if channel_key not in guild_stats["channels"]:
            guild_stats["channels"][channel_key] = {"messages": 0, "characters": 0}
        
        guild_stats["channels"][channel_key]["messages"] += 1
        guild_stats["channels"][channel_key]["characters"] += message_length
        
        # Track daily activity
        today = datetime.utcnow().date().isoformat()
        if today not in guild_stats["daily_activity"]:
            guild_stats["daily_activity"][today] = {"messages": 0, "characters": 0}
        
        guild_stats["daily_activity"][today]["messages"] += 1
        guild_stats["daily_activity"][today]["characters"] += message_length
        
        self._write_json(self.message_stats_file, stats)
    
    def track_command_usage(self, user_id: int, guild_id: int, command_name: str):
        """Track command usage"""
        stats = self._read_json(self.command_stats_file)
        
        user_key = str(user_id)
        guild_key = str(guild_id)
        
        if user_key not in stats:
            stats[user_key] = {}
        
        if guild_key not in stats[user_key]:
            stats[user_key][guild_key] = {
                "total_commands": 0,
                "commands": {},
                "last_command": datetime.utcnow().isoformat()
            }
        
        guild_stats = stats[user_key][guild_key]
        
        # Update totals
        guild_stats["total_commands"] += 1
        guild_stats["last_command"] = datetime.utcnow().isoformat()
        
        # Track individual command usage
        if command_name not in guild_stats["commands"]:
            guild_stats["commands"][command_name] = 0
        
        guild_stats["commands"][command_name] += 1
        
        self._write_json(self.command_stats_file, stats)
    
    def get_user_stats(self, user_id: int, guild_id: int) -> Dict:
        """Get comprehensive stats for a user"""
        message_stats = self._read_json(self.message_stats_file)
        command_stats = self._read_json(self.command_stats_file)
        
        user_key = str(user_id)
        guild_key = str(guild_id)
        
        result = {
            "user_id": user_id,
            "guild_id": guild_id,
            "messages": message_stats.get(user_key, {}).get(guild_key, {}),
            "commands": command_stats.get(user_key, {}).get(guild_key, {})
        }
        
        return result
    
    def get_guild_leaderboard(self, guild_id: int, limit: int = 10) -> List[Tuple[int, Dict]]:
        """Get guild message leaderboard"""
        message_stats = self._read_json(self.message_stats_file)
        guild_key = str(guild_id)
        
        leaderboard = []
        
        for user_id, user_data in message_stats.items():
            if guild_key in user_data:
                guild_stats = user_data[guild_key]
                leaderboard.append((
                    int(user_id),
                    {
                        "total_messages": guild_stats.get("total_messages", 0),
                        "total_characters": guild_stats.get("total_characters", 0),
                        "last_message": guild_stats.get("last_message", ""),
                        "avg_message_length": guild_stats.get("total_characters", 0) / max(guild_stats.get("total_messages", 1), 1)
                    }
                ))
        
        # Sort by total messages
        leaderboard.sort(key=lambda x: x[1]["total_messages"], reverse=True)
        
        return leaderboard[:limit]
    
    def get_command_leaderboard(self, guild_id: int, limit: int = 10) -> List[Tuple[int, Dict]]:
        """Get command usage leaderboard"""
        command_stats = self._read_json(self.command_stats_file)
        guild_key = str(guild_id)
        
        leaderboard = []
        
        for user_id, user_data in command_stats.items():
            if guild_key in user_data:
                guild_stats = user_data[guild_key]
                leaderboard.append((
                    int(user_id),
                    {
                        "total_commands": guild_stats.get("total_commands", 0),
                        "last_command": guild_stats.get("last_command", ""),
                        "favorite_command": max(guild_stats.get("commands", {}).items(), key=lambda x: x[1], default=("None", 0))[0]
                    }
                ))
        
        # Sort by total commands
        leaderboard.sort(key=lambda x: x[1]["total_commands"], reverse=True)
        
        return leaderboard[:limit]
    
    def get_guild_stats(self, guild_id: int) -> Dict:
        """Get overall guild statistics"""
        message_stats = self._read_json(self.message_stats_file)
        command_stats = self._read_json(self.command_stats_file)
        guild_key = str(guild_id)
        
        total_messages = 0
        total_characters = 0
        total_commands = 0
        active_users = set()
        command_usage = defaultdict(int)
        
        # Calculate message stats
        for user_id, user_data in message_stats.items():
            if guild_key in user_data:
                guild_stats = user_data[guild_key]
                total_messages += guild_stats.get("total_messages", 0)
                total_characters += guild_stats.get("total_characters", 0)
                active_users.add(user_id)
        
        # Calculate command stats
        for user_id, user_data in command_stats.items():
            if guild_key in user_data:
                guild_stats = user_data[guild_key]
                total_commands += guild_stats.get("total_commands", 0)
                active_users.add(user_id)
                
                for command, count in guild_stats.get("commands", {}).items():
                    command_usage[command] += count
        
        return {
            "total_messages": total_messages,
            "total_characters": total_characters,
            "total_commands": total_commands,
            "active_users": len(active_users),
            "avg_message_length": total_characters / max(total_messages, 1),
            "popular_commands": dict(sorted(command_usage.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def get_user_activity_chart(self, user_id: int, guild_id: int, days: int = 30) -> Dict:
        """Get user activity for the last N days"""
        message_stats = self._read_json(self.message_stats_file)
        user_key = str(user_id)
        guild_key = str(guild_id)
        
        if user_key not in message_stats or guild_key not in message_stats[user_key]:
            return {}
        
        guild_stats = message_stats[user_key][guild_key]
        daily_activity = guild_stats.get("daily_activity", {})
        
        # Get last N days
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        activity_chart = {}
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            activity_chart[date_str] = daily_activity.get(date_str, {"messages": 0, "characters": 0})
            current_date += timedelta(days=1)
        
        return activity_chart
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Remove old daily activity data"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).date().isoformat()
        
        message_stats = self._read_json(self.message_stats_file)
        modified = False
        
        for user_id, user_data in message_stats.items():
            for guild_id, guild_stats in user_data.items():
                if "daily_activity" in guild_stats:
                    old_dates = [date for date in guild_stats["daily_activity"].keys() if date < cutoff_date]
                    for date in old_dates:
                        del guild_stats["daily_activity"][date]
                        modified = True
        
        if modified:
            self._write_json(self.message_stats_file, message_stats)
            logger.info(f"Cleaned up activity data older than {days_to_keep} days")