import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import discord
from collections import defaultdict, Counter
import asyncio
import re

logger = logging.getLogger(__name__)

class EngagementTracker:
    def __init__(self):
        self.engagement_file = "data/engagement_narratives.json"
        self.conversation_file = "data/conversation_threads.json"
        self.narrative_file = "data/community_narratives.json"
        
        # Initialize data structures
        self.engagement_data = self._load_data(self.engagement_file, {})
        self.conversation_threads = self._load_data(self.conversation_file, {})
        self.community_narratives = self._load_data(self.narrative_file, {})
        
        # Narrative tracking patterns
        self.narrative_patterns = {
            'story_start': [
                r"once upon a time", r"story time", r"let me tell you",
                r"i remember when", r"back in", r"there was this time"
            ],
            'emotional_moments': [
                r"i was so (happy|sad|excited|angry|proud|disappointed)",
                r"it made me (feel|cry|laugh|smile)", r"i couldn't believe",
                r"it was (amazing|terrible|incredible|awful)"
            ],
            'community_building': [
                r"we should", r"let's all", r"everyone", r"together we",
                r"our (server|community|group)", r"what if we"
            ],
            'questions': [
                r"\?", r"what do you think", r"does anyone know",
                r"has anyone", r"can someone", r"who here"
            ],
            'celebration': [
                r"congratulations", r"well done", r"good job", r"awesome",
                r"great work", r"proud of", r"celebrate"
            ],
            'support': [
                r"are you okay", r"hope you're", r"thinking of you",
                r"here if you need", r"support", r"help"
            ]
        }
        
        # Engagement metrics
        self.engagement_metrics = {
            'response_time': {},
            'conversation_depth': {},
            'narrative_continuity': {},
            'emotional_resonance': {},
            'community_involvement': {}
        }
        
    def _load_data(self, file_path: str, default: dict) -> dict:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default.copy()
    
    def _save_data(self, file_path: str, data: dict):
        """Save data to JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {e}")
    
    def analyze_message_narrative(self, message: discord.Message) -> dict:
        """Analyze a message for narrative elements"""
        content = message.content.lower()
        narrative_elements = {}
        
        # Check for narrative patterns
        for pattern_type, patterns in self.narrative_patterns.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    matches.append(pattern)
            if matches:
                narrative_elements[pattern_type] = matches
        
        # Analyze message characteristics
        analysis = {
            'user_id': str(message.author.id),
            'guild_id': str(message.guild.id),
            'channel_id': str(message.channel.id),
            'timestamp': message.created_at.isoformat(),
            'content_length': len(message.content),
            'word_count': len(message.content.split()),
            'has_mentions': len(message.mentions) > 0,
            'has_reactions': len(message.reactions) > 0,
            'narrative_elements': narrative_elements,
            'engagement_score': self._calculate_engagement_score(message, narrative_elements),
            'thread_potential': self._assess_thread_potential(message, narrative_elements)
        }
        
        return analysis
    
    def _calculate_engagement_score(self, message: discord.Message, narrative_elements: dict) -> float:
        """Calculate engagement score for a message"""
        score = 0.0
        
        # Base score from message characteristics
        score += min(len(message.content) / 100, 2.0)  # Length bonus (max 2.0)
        score += len(message.mentions) * 0.5  # Mention bonus
        score += len(message.reactions) * 0.3  # Reaction bonus
        
        # Narrative element bonuses
        narrative_bonuses = {
            'story_start': 3.0,
            'emotional_moments': 2.0,
            'community_building': 2.5,
            'questions': 1.5,
            'celebration': 1.0,
            'support': 1.5
        }
        
        for element_type, patterns in narrative_elements.items():
            if element_type in narrative_bonuses:
                score += narrative_bonuses[element_type] * len(patterns)
        
        return min(score, 10.0)  # Cap at 10.0
    
    def _assess_thread_potential(self, message: discord.Message, narrative_elements: dict) -> float:
        """Assess the potential for this message to start a conversation thread"""
        potential = 0.0
        
        # High potential patterns
        if 'questions' in narrative_elements:
            potential += 0.8
        if 'story_start' in narrative_elements:
            potential += 0.7
        if 'community_building' in narrative_elements:
            potential += 0.6
        if 'emotional_moments' in narrative_elements:
            potential += 0.5
        
        # Message characteristics
        if len(message.content) > 50:
            potential += 0.2
        if message.mentions:
            potential += 0.3
        
        return min(potential, 1.0)
    
    def track_conversation_thread(self, message: discord.Message, analysis: dict):
        """Track conversation threads and narrative development"""
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        
        if guild_id not in self.conversation_threads:
            self.conversation_threads[guild_id] = {}
        
        if channel_id not in self.conversation_threads[guild_id]:
            self.conversation_threads[guild_id][channel_id] = {
                'active_threads': {},
                'thread_history': [],
                'narrative_continuity': {}
            }
        
        channel_data = self.conversation_threads[guild_id][channel_id]
        
        # Check if this continues an existing thread
        thread_id = self._identify_thread(message, channel_data)
        
        if thread_id:
            # Continue existing thread
            thread = channel_data['active_threads'][thread_id]
            thread['messages'].append({
                'user_id': user_id,
                'timestamp': message.created_at.isoformat(),
                'analysis': analysis,
                'message_id': str(message.id)
            })
            thread['last_activity'] = message.created_at.isoformat()
            thread['participants'].add(user_id)
            thread['narrative_score'] += analysis['engagement_score']
            
        elif analysis['thread_potential'] > 0.3:
            # Start new thread
            thread_id = f"thread_{message.id}"
            channel_data['active_threads'][thread_id] = {
                'starter': user_id,
                'start_time': message.created_at.isoformat(),
                'last_activity': message.created_at.isoformat(),
                'participants': {user_id},
                'messages': [{
                    'user_id': user_id,
                    'timestamp': message.created_at.isoformat(),
                    'analysis': analysis,
                    'message_id': str(message.id)
                }],
                'narrative_score': analysis['engagement_score'],
                'thread_type': self._classify_thread_type(analysis['narrative_elements'])
            }
        
        # Clean up old threads
        self._cleanup_old_threads(channel_data)
        
        # Save updated data
        self._save_data(self.conversation_file, self.conversation_threads)
    
    def _identify_thread(self, message: discord.Message, channel_data: dict) -> Optional[str]:
        """Identify if a message continues an existing thread"""
        current_time = message.created_at
        
        # Check recent messages and replies
        for thread_id, thread in channel_data['active_threads'].items():
            last_activity = datetime.fromisoformat(thread['last_activity'])
            
            # Thread is still active if last activity was within 10 minutes
            if current_time - last_activity < timedelta(minutes=10):
                # Check if message is a reply or mentions thread participants
                if (message.reference and 
                    any(msg['message_id'] == str(message.reference.message_id) 
                        for msg in thread['messages'])):
                    return thread_id
                
                # Check if message mentions thread participants
                mentioned_users = {str(user.id) for user in message.mentions}
                if mentioned_users.intersection(thread['participants']):
                    return thread_id
        
        return None
    
    def _classify_thread_type(self, narrative_elements: dict) -> str:
        """Classify the type of conversation thread"""
        if 'story_start' in narrative_elements:
            return 'storytelling'
        elif 'questions' in narrative_elements:
            return 'discussion'
        elif 'emotional_moments' in narrative_elements:
            return 'emotional_sharing'
        elif 'community_building' in narrative_elements:
            return 'community_planning'
        elif 'celebration' in narrative_elements:
            return 'celebration'
        elif 'support' in narrative_elements:
            return 'support'
        else:
            return 'general'
    
    def _cleanup_old_threads(self, channel_data: dict):
        """Clean up old inactive threads"""
        current_time = datetime.now()
        inactive_threads = []
        
        for thread_id, thread in channel_data['active_threads'].items():
            last_activity = datetime.fromisoformat(thread['last_activity'])
            if current_time - last_activity > timedelta(hours=1):
                inactive_threads.append(thread_id)
        
        # Move inactive threads to history
        for thread_id in inactive_threads:
            thread = channel_data['active_threads'].pop(thread_id)
            thread['end_time'] = current_time.isoformat()
            thread['participants'] = list(thread['participants'])  # Convert set to list
            channel_data['thread_history'].append(thread)
        
        # Keep only last 50 historical threads
        if len(channel_data['thread_history']) > 50:
            channel_data['thread_history'] = channel_data['thread_history'][-50:]
    
    def update_community_narrative(self, guild_id: str, analysis: dict):
        """Update community-wide narrative tracking"""
        if guild_id not in self.community_narratives:
            self.community_narratives[guild_id] = {
                'narrative_themes': defaultdict(int),
                'active_storytellers': defaultdict(int),
                'engagement_trends': [],
                'community_mood': defaultdict(int),
                'narrative_milestones': []
            }
        
        guild_data = self.community_narratives[guild_id]
        
        # Update narrative themes
        for theme in analysis['narrative_elements'].keys():
            guild_data['narrative_themes'][theme] += 1
        
        # Track active storytellers
        guild_data['active_storytellers'][analysis['user_id']] += analysis['engagement_score']
        
        # Update engagement trends
        guild_data['engagement_trends'].append({
            'timestamp': analysis['timestamp'],
            'score': analysis['engagement_score'],
            'user_id': analysis['user_id']
        })
        
        # Keep only last 100 engagement points
        if len(guild_data['engagement_trends']) > 100:
            guild_data['engagement_trends'] = guild_data['engagement_trends'][-100:]
        
        # Update community mood based on narrative elements
        mood_mapping = {
            'emotional_moments': 'emotional',
            'celebration': 'positive',
            'support': 'supportive',
            'community_building': 'collaborative',
            'questions': 'curious',
            'story_start': 'creative'
        }
        
        for element_type in analysis['narrative_elements'].keys():
            if element_type in mood_mapping:
                guild_data['community_mood'][mood_mapping[element_type]] += 1
        
        # Save updated data
        self._save_data(self.narrative_file, self.community_narratives)
    
    def get_engagement_summary(self, guild_id: str, days: int = 7) -> dict:
        """Get engagement summary for a guild"""
        guild_data = self.community_narratives.get(guild_id, {})
        
        if not guild_data:
            return {'error': 'No engagement data found for this server'}
        
        # Calculate timeframe
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Filter recent engagement trends
        recent_trends = [
            trend for trend in guild_data.get('engagement_trends', [])
            if datetime.fromisoformat(trend['timestamp']) > cutoff_time
        ]
        
        # Calculate statistics
        total_engagement = sum(trend['score'] for trend in recent_trends)
        avg_engagement = total_engagement / len(recent_trends) if recent_trends else 0
        
        # Top storytellers
        storyteller_scores = guild_data.get('active_storytellers', {})
        top_storytellers = sorted(
            storyteller_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Most common narrative themes
        narrative_themes = dict(guild_data.get('narrative_themes', {}))
        top_themes = sorted(
            narrative_themes.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Community mood
        community_mood = dict(guild_data.get('community_mood', {}))
        
        return {
            'period_days': days,
            'total_engagement': total_engagement,
            'average_engagement': round(avg_engagement, 2),
            'engagement_events': len(recent_trends),
            'top_storytellers': top_storytellers,
            'top_narrative_themes': top_themes,
            'community_mood': community_mood,
            'narrative_milestones': guild_data.get('narrative_milestones', [])
        }
    
    def get_conversation_threads(self, guild_id: str, channel_id: str = None) -> dict:
        """Get conversation thread information"""
        guild_data = self.conversation_threads.get(guild_id, {})
        
        if channel_id:
            channel_data = guild_data.get(channel_id, {})
            return {
                'active_threads': len(channel_data.get('active_threads', {})),
                'thread_history': len(channel_data.get('thread_history', [])),
                'threads': channel_data.get('active_threads', {})
            }
        else:
            # Guild-wide thread summary
            total_active = sum(
                len(channel.get('active_threads', {}))
                for channel in guild_data.values()
            )
            total_history = sum(
                len(channel.get('thread_history', []))
                for channel in guild_data.values()
            )
            
            return {
                'total_active_threads': total_active,
                'total_historical_threads': total_history,
                'channels_with_threads': len(guild_data)
            }
    
    async def track_message(self, message: discord.Message):
        """Main entry point for tracking a message"""
        if message.author.bot:
            return
        
        try:
            # Analyze message for narrative elements
            analysis = self.analyze_message_narrative(message)
            
            # Track conversation threads
            self.track_conversation_thread(message, analysis)
            
            # Update community narrative
            self.update_community_narrative(str(message.guild.id), analysis)
            
            # Update engagement data
            guild_id = str(message.guild.id)
            if guild_id not in self.engagement_data:
                self.engagement_data[guild_id] = {
                    'total_messages': 0,
                    'total_engagement': 0,
                    'users': {}
                }
            
            self.engagement_data[guild_id]['total_messages'] += 1
            self.engagement_data[guild_id]['total_engagement'] += analysis['engagement_score']
            
            user_id = str(message.author.id)
            if user_id not in self.engagement_data[guild_id]['users']:
                self.engagement_data[guild_id]['users'][user_id] = {
                    'messages': 0,
                    'engagement_score': 0,
                    'narrative_contributions': 0
                }
            
            user_data = self.engagement_data[guild_id]['users'][user_id]
            user_data['messages'] += 1
            user_data['engagement_score'] += analysis['engagement_score']
            if analysis['narrative_elements']:
                user_data['narrative_contributions'] += 1
            
            # Save engagement data
            self._save_data(self.engagement_file, self.engagement_data)
            
        except Exception as e:
            logger.error(f"Error tracking message engagement: {e}")