import discord
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)

def format_duration(seconds):
    """Format seconds into human readable duration"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hours"
    else:
        days = seconds // 86400
        return f"{days} days"

def parse_time(time_str):
    """Parse time string into seconds"""
    time_str = time_str.lower().strip()
    
    # Regular expression to match time format
    pattern = r'(\d+)\s*(s|sec|second|seconds|m|min|minute|minutes|h|hour|hours|d|day|days)'
    match = re.match(pattern, time_str)
    
    if not match:
        return None
    
    amount = int(match.group(1))
    unit = match.group(2)
    
    if unit in ['s', 'sec', 'second', 'seconds']:
        return amount
    elif unit in ['m', 'min', 'minute', 'minutes']:
        return amount * 60
    elif unit in ['h', 'hour', 'hours']:
        return amount * 3600
    elif unit in ['d', 'day', 'days']:
        return amount * 86400
    
    return None

def create_embed(title, description, color=discord.Color.blue(), **kwargs):
    """Create a standardized embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    
    for key, value in kwargs.items():
        if key == 'fields':
            for field in value:
                embed.add_field(
                    name=field.get('name', 'Field'),
                    value=field.get('value', 'Value'),
                    inline=field.get('inline', False)
                )
        elif key == 'thumbnail':
            embed.set_thumbnail(url=value)
        elif key == 'image':
            embed.set_image(url=value)
        elif key == 'footer':
            embed.set_footer(text=value)
        elif key == 'author':
            embed.set_author(name=value)
    
    return embed

def format_movie_info(movie_data):
    """Format movie data for display"""
    if not movie_data:
        return None
    
    title = movie_data.get('title', 'Unknown Title')
    overview = movie_data.get('overview', 'No description available')
    release_date = movie_data.get('release_date', 'Unknown')
    rating = movie_data.get('vote_average', 'N/A')
    
    # Truncate overview if too long
    if len(overview) > 500:
        overview = overview[:497] + "..."
    
    return {
        'title': title,
        'overview': overview,
        'release_date': release_date,
        'rating': rating,
        'poster_url': f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}" if movie_data.get('poster_path') else None
    }

def check_permissions(interaction, required_permissions):
    """Check if user has required permissions"""
    user_permissions = interaction.user.guild_permissions
    
    if isinstance(required_permissions, str):
        required_permissions = [required_permissions]
    
    for permission in required_permissions:
        if not getattr(user_permissions, permission, False):
            return False
    
    return True

def get_user_color(user):
    """Get user's color or default"""
    if user.color != discord.Color.default():
        return user.color
    return discord.Color.blue()

def sanitize_input(text, max_length=100):
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text

def format_list(items, max_items=10, separator=", "):
    """Format a list of items with truncation"""
    if not items:
        return "None"
    
    if len(items) <= max_items:
        return separator.join(items)
    else:
        visible_items = items[:max_items]
        remaining = len(items) - max_items
        return separator.join(visible_items) + f" (+{remaining} more)"

def get_relative_time(timestamp):
    """Get relative time string"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except ValueError:
            return "Unknown"
    
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "Just now"

def validate_user_input(input_type, value):
    """Validate user input based on type"""
    if input_type == 'username':
        if not value or len(value) < 2 or len(value) > 32:
            return False, "Username must be between 2 and 32 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            return False, "Username can only contain letters, numbers, and underscores"
    
    elif input_type == 'character_name':
        if not value or len(value) < 1 or len(value) > 100:
            return False, "Character name must be between 1 and 100 characters"
    
    elif input_type == 'anime_source':
        if len(value) > 100:
            return False, "Anime source must be less than 100 characters"
    
    elif input_type == 'reason':
        if len(value) > 500:
            return False, "Reason must be less than 500 characters"
    
    return True, "Valid"

def create_paginated_embed(items, page=1, items_per_page=10, title="Results"):
    """Create paginated embed"""
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]
    
    embed = discord.Embed(
        title=f"{title} (Page {page}/{total_pages})",
        description=f"Showing {len(page_items)} of {total_items} results",
        color=discord.Color.blue()
    )
    
    return embed, page_items, total_pages

def log_moderation_action(action, moderator, target, reason="No reason provided", guild_id=None):
    """Log moderation actions"""
    log_data = {
        'action': action,
        'moderator': str(moderator),
        'target': str(target),
        'reason': reason,
        'timestamp': datetime.utcnow().isoformat(),
        'guild_id': guild_id
    }
    
    logger.info(f"Moderation action: {action} | Moderator: {moderator} | Target: {target} | Reason: {reason}")
    return log_data

def generate_error_embed(error_message, title="Error"):
    """Generate a standardized error embed"""
    return discord.Embed(
        title=f"❌ {title}",
        description=error_message,
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )

def generate_success_embed(message, title="Success"):
    """Generate a standardized success embed"""
    return discord.Embed(
        title=f"✅ {title}",
        description=message,
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )

def generate_info_embed(message, title="Information"):
    """Generate a standardized info embed"""
    return discord.Embed(
        title=f"ℹ️ {title}",
        description=message,
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
