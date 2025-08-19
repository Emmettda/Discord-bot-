import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.data_dir = "data"
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.warnings_file = os.path.join(self.data_dir, "warnings.json")
        self.favorites_file = os.path.join(self.data_dir, "favorites.json")
        self.automod_file = os.path.join(self.data_dir, "automod_violations.json")
        self.automod_settings_file = os.path.join(self.data_dir, "automod_settings.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_file(self.users_file, {})
        self._init_file(self.warnings_file, [])
        self._init_file(self.favorites_file, {})
        self._init_file(self.automod_file, [])
        self._init_file(self.automod_settings_file, {})
    
    def _init_file(self, file_path, default_data):
        """Initialize a JSON file with default data if it doesn't exist"""
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w') as f:
                    json.dump(default_data, f, indent=2)
                logger.info(f"Created {file_path}")
            except Exception as e:
                logger.error(f"Error creating {file_path}: {e}")
    
    def _read_json(self, file_path):
        """Read JSON data from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return {} if file_path != self.warnings_file else []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {file_path}")
            return {} if file_path != self.warnings_file else []
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return {} if file_path != self.warnings_file else []
    
    def _write_json(self, file_path, data):
        """Write JSON data to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing to {file_path}: {e}")
    
    # User management
    def get_user(self, user_id):
        """Get user data"""
        users = self._read_json(self.users_file)
        return users.get(str(user_id))
    
    def update_user(self, user_id, user_data):
        """Update user data"""
        users = self._read_json(self.users_file)
        users[str(user_id)] = user_data
        self._write_json(self.users_file, users)
    
    # Warning system
    def add_warning(self, warning_data):
        """Add a warning to the database"""
        warnings = self._read_json(self.warnings_file)
        warnings.append(warning_data)
        self._write_json(self.warnings_file, warnings)
        logger.info(f"Warning added for user {warning_data['user_id']}")
    
    def get_warnings(self, user_id, guild_id):
        """Get warnings for a user in a specific guild"""
        warnings = self._read_json(self.warnings_file)
        user_warnings = []
        
        for warning in warnings:
            if warning['user_id'] == user_id and warning['guild_id'] == guild_id:
                user_warnings.append(warning)
        
        return user_warnings
    
    def clear_warnings(self, user_id, guild_id):
        """Clear all warnings for a user in a specific guild"""
        warnings = self._read_json(self.warnings_file)
        updated_warnings = []
        
        for warning in warnings:
            if not (warning['user_id'] == user_id and warning['guild_id'] == guild_id):
                updated_warnings.append(warning)
        
        self._write_json(self.warnings_file, updated_warnings)
        logger.info(f"Warnings cleared for user {user_id} in guild {guild_id}")
    
    # Favorite character system
    def set_favorite_character(self, user_id, character_data):
        """Set user's favorite character"""
        favorites = self._read_json(self.favorites_file)
        favorites[str(user_id)] = character_data
        self._write_json(self.favorites_file, favorites)
        logger.info(f"Favorite character set for user {user_id}: {character_data['character_name']}")
    
    def get_favorite_character(self, user_id):
        """Get user's favorite character"""
        favorites = self._read_json(self.favorites_file)
        return favorites.get(str(user_id))
    
    def remove_favorite_character(self, user_id):
        """Remove user's favorite character"""
        favorites = self._read_json(self.favorites_file)
        if str(user_id) in favorites:
            del favorites[str(user_id)]
            self._write_json(self.favorites_file, favorites)
            logger.info(f"Favorite character removed for user {user_id}")
    
    # Statistics and analytics
    def get_user_stats(self, user_id, guild_id):
        """Get user statistics"""
        warnings = self.get_warnings(user_id, guild_id)
        favorite = self.get_favorite_character(user_id)
        
        return {
            "warning_count": len(warnings),
            "has_favorite_character": favorite is not None,
            "favorite_character": favorite
        }
    
    def get_guild_stats(self, guild_id):
        """Get guild statistics"""
        warnings = self._read_json(self.warnings_file)
        favorites = self._read_json(self.favorites_file)
        
        guild_warnings = [w for w in warnings if w['guild_id'] == guild_id]
        
        return {
            "total_warnings": len(guild_warnings),
            "total_users_with_favorites": len(favorites),
            "warning_users": len(set(w['user_id'] for w in guild_warnings))
        }
    
    # Backup and maintenance
    def backup_data(self):
        """Create a backup of all data"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.data_dir, f"backup_{timestamp}")
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy all data files
            import shutil
            shutil.copy2(self.users_file, backup_dir)
            shutil.copy2(self.warnings_file, backup_dir)
            shutil.copy2(self.favorites_file, backup_dir)
            
            logger.info(f"Data backup created: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def cleanup_old_warnings(self, days_old=30):
        """Remove warnings older than specified days"""
        warnings = self._read_json(self.warnings_file)
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        updated_warnings = []
        removed_count = 0
        
        for warning in warnings:
            try:
                warning_date = datetime.fromisoformat(warning['timestamp'])
                if warning_date > cutoff_date:
                    updated_warnings.append(warning)
                else:
                    removed_count += 1
            except (ValueError, KeyError):
                # Keep warnings with invalid timestamps
                updated_warnings.append(warning)
        
        if removed_count > 0:
            self._write_json(self.warnings_file, updated_warnings)
            logger.info(f"Cleaned up {removed_count} old warnings")
        
        return removed_count
    
    # Auto-moderation system
    def log_automod_violation(self, violation_data):
        """Log auto-moderation violation"""
        violations = self._read_json(self.automod_file)
        violations.append(violation_data)
        self._write_json(self.automod_file, violations)
        logger.info(f"Auto-mod violation logged for user {violation_data['user_id']}")
    
    def get_automod_violations(self, user_id=None, guild_id=None, days=30):
        """Get auto-moderation violations"""
        violations = self._read_json(self.automod_file)
        
        # Filter by date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_violations = []
        
        for violation in violations:
            try:
                violation_date = datetime.fromisoformat(violation['timestamp'])
                if violation_date > cutoff_date:
                    recent_violations.append(violation)
            except (ValueError, KeyError):
                continue
        
        # Filter by user and guild if specified
        if user_id:
            recent_violations = [v for v in recent_violations if v['user_id'] == user_id]
        if guild_id:
            recent_violations = [v for v in recent_violations if v['guild_id'] == guild_id]
        
        return recent_violations
    
    def get_automod_stats(self, guild_id, days=30):
        """Get auto-moderation statistics"""
        violations = self.get_automod_violations(guild_id=guild_id, days=days)
        
        violation_types = {}
        user_violations = {}
        
        for violation in violations:
            # Count violation types
            for v_type in violation['violations']:
                violation_types[v_type] = violation_types.get(v_type, 0) + 1
            
            # Count user violations
            user_id = violation['user_id']
            user_violations[user_id] = user_violations.get(user_id, 0) + 1
        
        return {
            'total_violations': len(violations),
            'violation_types': violation_types,
            'user_violations': user_violations,
            'top_violators': sorted(user_violations.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def save_automod_settings(self, guild_id, settings):
        """Save auto-moderation settings for a guild"""
        all_settings = self._read_json(self.automod_settings_file)
        all_settings[str(guild_id)] = settings
        self._write_json(self.automod_settings_file, all_settings)
        logger.info(f"Auto-mod settings saved for guild {guild_id}")
    
    def get_automod_settings(self, guild_id):
        """Get auto-moderation settings for a guild"""
        all_settings = self._read_json(self.automod_settings_file)
        return all_settings.get(str(guild_id), {})
    
    def cleanup_old_automod_violations(self, days_old=90):
        """Remove old auto-moderation violations"""
        violations = self._read_json(self.automod_file)
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        updated_violations = []
        removed_count = 0
        
        for violation in violations:
            try:
                violation_date = datetime.fromisoformat(violation['timestamp'])
                if violation_date > cutoff_date:
                    updated_violations.append(violation)
                else:
                    removed_count += 1
            except (ValueError, KeyError):
                updated_violations.append(violation)
        
        if removed_count > 0:
            self._write_json(self.automod_file, updated_violations)
            logger.info(f"Cleaned up {removed_count} old auto-mod violations")
        
        return removed_count
