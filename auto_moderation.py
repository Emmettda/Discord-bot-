import discord
from discord.ext import commands, tasks
import logging
import re
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict, deque
import aiohttp

logger = logging.getLogger(__name__)

class AutoModerationSystem:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        
        # Spam detection settings
        self.message_cache = defaultdict(lambda: deque(maxlen=10))  # Store last 10 messages per user
        self.user_violations = defaultdict(int)  # Track violations per user
        self.cooldowns = defaultdict(datetime)  # Track user cooldowns
        
        # Auto-moderation settings
        self.settings = {
            'spam_threshold': 5,  # Messages in time window
            'spam_window': 10,    # Seconds
            'duplicate_threshold': 3,  # Same message count
            'caps_threshold': 0.7,  # Percentage of caps
            'link_whitelist': ['discord.gg', 'youtube.com', 'youtu.be', 'twitch.tv'],
            'bad_words': [
                'spam', 'scam', 'hack', 'cheat', 'bot', 'fake', 'virus',
                'malware', 'phishing', 'stealing', 'account', 'password'
            ],
            'max_mentions': 5,  # Max mentions per message
            'max_emojis': 10,   # Max emojis per message
            'invite_filter': True,
            'link_filter': True,
            'caps_filter': True,
            'spam_filter': True,
            'duplicate_filter': True,
            'mention_filter': True,
            'emoji_filter': True,
            'automod_enabled': True
        }
        
        # Start background tasks
        self.cleanup_task.start()
    
    async def check_message(self, message):
        """Main auto-moderation check function"""
        if not self.settings['automod_enabled']:
            return False
            
        if message.author.bot:
            return False
            
        # Skip if user has admin permissions
        if message.author.guild_permissions.administrator:
            return False
            
        # Skip if user is in cooldown
        if self.is_user_in_cooldown(message.author.id):
            return False
        
        violations = []
        
        # Check for various violations
        if self.settings['spam_filter'] and await self.check_spam(message):
            violations.append("spam")
            
        if self.settings['duplicate_filter'] and await self.check_duplicate(message):
            violations.append("duplicate_message")
            
        if self.settings['caps_filter'] and await self.check_caps(message):
            violations.append("excessive_caps")
            
        if self.settings['link_filter'] and await self.check_links(message):
            violations.append("suspicious_link")
            
        if self.settings['invite_filter'] and await self.check_invites(message):
            violations.append("discord_invite")
            
        if self.settings['mention_filter'] and await self.check_mentions(message):
            violations.append("excessive_mentions")
            
        if self.settings['emoji_filter'] and await self.check_emojis(message):
            violations.append("excessive_emojis")
            
        if await self.check_bad_words(message):
            violations.append("inappropriate_content")
        
        # Take action if violations found
        if violations:
            await self.handle_violations(message, violations)
            return True
            
        # Store message for spam detection
        self.message_cache[message.author.id].append({
            'content': message.content,
            'timestamp': message.created_at,
            'channel': message.channel.id
        })
        
        return False
    
    async def check_spam(self, message):
        """Check for spam based on message frequency"""
        user_id = message.author.id
        now = message.created_at
        
        # Count recent messages
        recent_messages = [
            msg for msg in self.message_cache[user_id]
            if (now - msg['timestamp']).total_seconds() <= self.settings['spam_window']
        ]
        
        return len(recent_messages) >= self.settings['spam_threshold']
    
    async def check_duplicate(self, message):
        """Check for duplicate messages"""
        user_id = message.author.id
        content = message.content.lower().strip()
        
        if not content:
            return False
            
        # Count identical messages
        duplicate_count = sum(
            1 for msg in self.message_cache[user_id]
            if msg['content'].lower().strip() == content
        )
        
        return duplicate_count >= self.settings['duplicate_threshold']
    
    async def check_caps(self, message):
        """Check for excessive caps"""
        content = message.content
        if len(content) < 10:  # Skip short messages
            return False
            
        caps_count = sum(1 for char in content if char.isupper())
        caps_ratio = caps_count / len(content)
        
        return caps_ratio >= self.settings['caps_threshold']
    
    async def check_links(self, message):
        """Check for suspicious links"""
        content = message.content
        
        # Find URLs
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        urls = re.findall(url_pattern, content)
        
        if not urls:
            return False
        
        # Check against whitelist
        for url in urls:
            is_whitelisted = any(domain in url for domain in self.settings['link_whitelist'])
            if not is_whitelisted:
                # Additional checks for suspicious patterns
                if await self.is_suspicious_url(url):
                    return True
        
        return False
    
    async def check_invites(self, message):
        """Check for Discord invites"""
        content = message.content
        
        # Discord invite patterns
        invite_patterns = [
            r'discord\.gg/\w+',
            r'discordapp\.com/invite/\w+',
            r'discord\.com/invite/\w+'
        ]
        
        for pattern in invite_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    async def check_mentions(self, message):
        """Check for excessive mentions"""
        return len(message.mentions) > self.settings['max_mentions']
    
    async def check_emojis(self, message):
        """Check for excessive emojis"""
        content = message.content
        
        # Count Unicode emojis and custom emojis
        unicode_emoji_count = len(re.findall(r'[\U00010000-\U0010ffff]', content))
        custom_emoji_count = len(re.findall(r'<:\w+:\d+>', content))
        
        total_emojis = unicode_emoji_count + custom_emoji_count
        
        return total_emojis > self.settings['max_emojis']
    
    async def check_bad_words(self, message):
        """Check for inappropriate content"""
        content = message.content.lower()
        
        for word in self.settings['bad_words']:
            if word in content:
                return True
        
        return False
    
    async def is_suspicious_url(self, url):
        """Check if URL is suspicious"""
        suspicious_patterns = [
            r'bit\.ly',
            r'tinyurl\.com',
            r'goo\.gl',
            r't\.co',
            r'discord-gift',
            r'discordapp-gift',
            r'nitro-gift'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    async def handle_violations(self, message, violations):
        """Handle detected violations"""
        user_id = message.author.id
        self.user_violations[user_id] += len(violations)
        
        # Delete the message
        try:
            await message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            logger.warning(f"Cannot delete message from {message.author}")
        
        # Log violation
        violation_data = {
            'user_id': user_id,
            'guild_id': message.guild.id,
            'channel_id': message.channel.id,
            'violations': violations,
            'message_content': message.content[:500],  # Truncate long messages
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.db.log_automod_violation(violation_data)
        
        # Determine action based on violation count
        violation_count = self.user_violations[user_id]
        
        if violation_count >= 5:
            await self.apply_mute(message.author, message.guild, 60, "Repeated auto-moderation violations")
        elif violation_count >= 3:
            await self.apply_mute(message.author, message.guild, 30, "Multiple auto-moderation violations")
        else:
            # Send warning
            await self.send_warning(message.author, message.channel, violations)
    
    async def apply_mute(self, user, guild, duration_minutes, reason):
        """Apply mute to user"""
        try:
            unmute_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
            await user.timeout(unmute_time, reason=reason)
            
            # Log the mute
            logger.info(f"Auto-muted {user} for {duration_minutes} minutes: {reason}")
            
            # Reset violation count after mute
            self.user_violations[user.id] = 0
            
        except discord.Forbidden:
            logger.warning(f"Cannot mute {user} - insufficient permissions")
        except Exception as e:
            logger.error(f"Error muting {user}: {e}")
    
    async def send_warning(self, user, channel, violations):
        """Send warning message"""
        try:
            violation_text = ", ".join(violations)
            
            embed = discord.Embed(
                title="⚠️ Auto-Moderation Warning",
                description=f"{user.mention}, your message was removed for: {violation_text}",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="Guidelines",
                value="• Avoid spam and duplicate messages\n"
                      "• Keep caps usage reasonable\n"
                      "• Don't share suspicious links\n"
                      "• Limit mentions and emojis",
                inline=False
            )
            
            warning_msg = await channel.send(embed=embed)
            
            # Auto-delete warning after 30 seconds
            await asyncio.sleep(30)
            try:
                await warning_msg.delete()
            except discord.NotFound:
                pass
                
        except discord.Forbidden:
            logger.warning(f"Cannot send warning in {channel}")
    
    def is_user_in_cooldown(self, user_id):
        """Check if user is in cooldown"""
        if user_id in self.cooldowns:
            return datetime.utcnow() < self.cooldowns[user_id]
        return False
    
    def set_user_cooldown(self, user_id, seconds):
        """Set user cooldown"""
        self.cooldowns[user_id] = datetime.utcnow() + timedelta(seconds=seconds)
    
    @tasks.loop(minutes=30)
    async def cleanup_task(self):
        """Clean up old data"""
        now = datetime.utcnow()
        
        # Clean up old messages from cache
        for user_id in list(self.message_cache.keys()):
            messages = self.message_cache[user_id]
            # Keep only messages from last hour
            self.message_cache[user_id] = deque([
                msg for msg in messages
                if (now - msg['timestamp']).total_seconds() <= 3600
            ], maxlen=10)
        
        # Clean up old cooldowns
        expired_cooldowns = [
            user_id for user_id, cooldown_time in self.cooldowns.items()
            if now >= cooldown_time
        ]
        for user_id in expired_cooldowns:
            del self.cooldowns[user_id]
        
        # Reset violation counts periodically
        if now.minute == 0:  # Every hour
            self.user_violations.clear()
    
    def update_settings(self, new_settings):
        """Update auto-moderation settings"""
        self.settings.update(new_settings)
        logger.info("Auto-moderation settings updated")
    
    def get_settings(self):
        """Get current auto-moderation settings"""
        return self.settings.copy()
    
    def get_user_violations(self, user_id):
        """Get violation count for user"""
        return self.user_violations.get(user_id, 0)