import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import discord
from collections import defaultdict, deque
import asyncio
import re
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class FlowType(Enum):
    LINEAR = "linear"
    BRANCHING = "branching"
    CIRCULAR = "circular"
    CONVERGENT = "convergent"
    PARALLEL = "parallel"

@dataclass
class ConversationNode:
    message_id: str
    user_id: str
    timestamp: str
    content_preview: str
    response_count: int
    branch_factor: int
    influence_score: float
    narrative_elements: Dict[str, List[str]]
    connections: List[str]  # Connected message IDs
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ConversationFlow:
    flow_id: str
    start_node: str
    end_nodes: List[str]
    flow_type: FlowType
    participants: Set[str]
    duration_minutes: int
    narrative_coherence: float
    engagement_intensity: float
    branch_points: List[str]
    convergence_points: List[str]
    nodes: List[ConversationNode]
    
    def to_dict(self):
        result = asdict(self)
        result['flow_type'] = self.flow_type.value
        result['participants'] = list(self.participants)
        return result

class ConversationFlowMapper:
    def __init__(self, engagement_tracker):
        self.engagement_tracker = engagement_tracker
        self.flow_file = "data/conversation_flows.json"
        self.mapping_file = "data/flow_mappings.json"
        self.patterns_file = "data/flow_patterns.json"
        
        # Load existing data
        self.conversation_flows = self._load_data(self.flow_file, {})
        self.flow_mappings = self._load_data(self.mapping_file, {})
        self.flow_patterns = self._load_data(self.patterns_file, {})
        
        # Flow analysis parameters
        self.max_flow_duration = 120  # 2 hours max
        self.min_flow_participants = 2
        self.response_timeout = 15  # 15 minutes
        self.influence_threshold = 0.3
        
        # Conversation flow patterns
        self.flow_indicators = {
            'topic_shift': [
                r"speaking of", r"that reminds me", r"on a different note",
                r"changing the subject", r"by the way", r"also"
            ],
            'agreement': [
                r"exactly", r"i agree", r"you're right", r"that's true",
                r"absolutely", r"definitely", r"precisely"
            ],
            'disagreement': [
                r"actually", r"but", r"however", r"i disagree",
                r"on the contrary", r"not really", r"i think differently"
            ],
            'building_on': [
                r"and also", r"furthermore", r"in addition", r"plus",
                r"adding to that", r"building on", r"expanding on"
            ],
            'questioning': [
                r"what do you mean", r"can you explain", r"how so",
                r"why", r"what if", r"have you considered"
            ],
            'conclusion': [
                r"so in conclusion", r"to summarize", r"overall",
                r"in the end", r"finally", r"to wrap up"
            ]
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
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {e}")
    
    def analyze_message_connections(self, message: discord.Message) -> Dict[str, float]:
        """Analyze how a message connects to previous messages"""
        connections = {}
        content = message.content.lower()
        
        # Direct reply connection
        if message.reference and message.reference.message_id:
            connections[str(message.reference.message_id)] = 1.0
        
        # Mention connections
        for mention in message.mentions:
            # Find recent messages from mentioned users
            # This would require message history analysis
            connections[f"mention_{mention.id}"] = 0.7
        
        # Topic continuity analysis
        topic_indicators = self._analyze_topic_continuity(content)
        for indicator_type, strength in topic_indicators.items():
            connections[f"topic_{indicator_type}"] = strength
        
        return connections
    
    def _analyze_topic_continuity(self, content: str) -> Dict[str, float]:
        """Analyze topic continuity indicators in message content"""
        continuity_scores = {}
        
        for indicator_type, patterns in self.flow_indicators.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    score += 0.2
            
            if score > 0:
                continuity_scores[indicator_type] = min(score, 1.0)
        
        return continuity_scores
    
    def calculate_influence_score(self, message: discord.Message, analysis: dict) -> float:
        """Calculate the influence score of a message in conversation flow"""
        score = 0.0
        
        # Base engagement score
        score += analysis.get('engagement_score', 0) * 0.3
        
        # Reply potential
        score += analysis.get('thread_potential', 0) * 0.4
        
        # Narrative elements bonus
        narrative_bonus = {
            'questions': 0.3,
            'story_start': 0.4,
            'emotional_moments': 0.2,
            'community_building': 0.3
        }
        
        for element_type in analysis.get('narrative_elements', {}):
            if element_type in narrative_bonus:
                score += narrative_bonus[element_type]
        
        # Message characteristics
        if len(message.content) > 100:
            score += 0.1
        if message.mentions:
            score += 0.1 * len(message.mentions)
        
        return min(score, 1.0)
    
    def create_conversation_node(self, message: discord.Message, analysis: dict) -> ConversationNode:
        """Create a conversation node from message analysis"""
        connections = self.analyze_message_connections(message)
        influence_score = self.calculate_influence_score(message, analysis)
        
        # Calculate branch factor (how many responses this might generate)
        branch_factor = int(analysis.get('thread_potential', 0) * 5)
        
        return ConversationNode(
            message_id=str(message.id),
            user_id=str(message.author.id),
            timestamp=message.created_at.isoformat(),
            content_preview=message.content[:100] + "..." if len(message.content) > 100 else message.content,
            response_count=0,  # Will be updated as responses come in
            branch_factor=branch_factor,
            influence_score=influence_score,
            narrative_elements=analysis.get('narrative_elements', {}),
            connections=list(connections.keys())
        )
    
    def detect_flow_type(self, nodes: List[ConversationNode]) -> FlowType:
        """Detect the type of conversation flow"""
        if len(nodes) < 2:
            return FlowType.LINEAR
        
        # Analyze connection patterns
        connection_counts = defaultdict(int)
        for node in nodes:
            connection_counts[len(node.connections)] += 1
        
        # Check for branching (multiple responses to single message)
        high_connection_nodes = sum(1 for count in connection_counts.keys() if count > 2)
        if high_connection_nodes > len(nodes) * 0.3:
            return FlowType.BRANCHING
        
        # Check for circular patterns (references to earlier messages)
        timestamps = [datetime.fromisoformat(node.timestamp) for node in nodes]
        sorted_nodes = sorted(zip(timestamps, nodes), key=lambda x: x[0])
        
        circular_refs = 0
        for i, (timestamp, node) in enumerate(sorted_nodes):
            for connection in node.connections:
                # Check if connection refers to much earlier message
                for j, (other_timestamp, other_node) in enumerate(sorted_nodes[:i-2]):
                    if other_node.message_id == connection:
                        circular_refs += 1
        
        if circular_refs > len(nodes) * 0.2:
            return FlowType.CIRCULAR
        
        # Check for convergent patterns (multiple threads leading to same topic)
        convergence_indicators = sum(
            1 for node in nodes
            if 'conclusion' in node.narrative_elements or 'agreement' in node.narrative_elements
        )
        if convergence_indicators > len(nodes) * 0.4:
            return FlowType.CONVERGENT
        
        # Check for parallel discussions
        unique_topics = set()
        for node in nodes:
            for element_type in node.narrative_elements:
                unique_topics.add(element_type)
        
        if len(unique_topics) > len(nodes) * 0.6:
            return FlowType.PARALLEL
        
        return FlowType.LINEAR
    
    def calculate_narrative_coherence(self, nodes: List[ConversationNode]) -> float:
        """Calculate narrative coherence score for a conversation flow"""
        if not nodes:
            return 0.0
        
        coherence_score = 0.0
        
        # Topic consistency
        topic_transitions = 0
        smooth_transitions = 0
        
        for i in range(1, len(nodes)):
            prev_node = nodes[i-1]
            curr_node = nodes[i]
            
            # Check for topic continuity indicators
            has_transition_indicator = False
            for indicator_type in ['building_on', 'agreement', 'questioning']:
                if indicator_type in curr_node.narrative_elements:
                    has_transition_indicator = True
                    smooth_transitions += 1
                    break
            
            if not has_transition_indicator:
                # Check for topic shift indicators
                if 'topic_shift' in curr_node.narrative_elements:
                    topic_transitions += 1
        
        # Calculate coherence based on smooth transitions
        if len(nodes) > 1:
            coherence_score = smooth_transitions / (len(nodes) - 1)
        
        # Penalty for too many abrupt topic shifts
        if topic_transitions > len(nodes) * 0.3:
            coherence_score *= 0.7
        
        return min(coherence_score, 1.0)
    
    def calculate_engagement_intensity(self, nodes: List[ConversationNode]) -> float:
        """Calculate engagement intensity for a conversation flow"""
        if not nodes:
            return 0.0
        
        total_influence = sum(node.influence_score for node in nodes)
        avg_influence = total_influence / len(nodes)
        
        # Factor in participant diversity
        unique_participants = len(set(node.user_id for node in nodes))
        participation_bonus = min(unique_participants / 5, 1.0)  # Bonus for up to 5 participants
        
        # Factor in response speed and continuity
        timestamps = [datetime.fromisoformat(node.timestamp) for node in nodes]
        if len(timestamps) > 1:
            avg_response_time = sum(
                (timestamps[i] - timestamps[i-1]).total_seconds() / 60
                for i in range(1, len(timestamps))
            ) / (len(timestamps) - 1)
            
            # Bonus for faster responses (up to 5 minutes)
            speed_bonus = max(0, 1.0 - (avg_response_time / 5))
        else:
            speed_bonus = 0
        
        intensity = (avg_influence * 0.5) + (participation_bonus * 0.3) + (speed_bonus * 0.2)
        return min(intensity, 1.0)
    
    def create_conversation_flow(self, nodes: List[ConversationNode], guild_id: str, channel_id: str) -> ConversationFlow:
        """Create a conversation flow from nodes"""
        if not nodes:
            return None
        
        # Sort nodes by timestamp
        sorted_nodes = sorted(nodes, key=lambda x: datetime.fromisoformat(x.timestamp))
        
        # Determine flow characteristics
        flow_type = self.detect_flow_type(sorted_nodes)
        participants = set(node.user_id for node in sorted_nodes)
        
        # Calculate duration
        start_time = datetime.fromisoformat(sorted_nodes[0].timestamp)
        end_time = datetime.fromisoformat(sorted_nodes[-1].timestamp)
        duration_minutes = int((end_time - start_time).total_seconds() / 60)
        
        # Calculate metrics
        narrative_coherence = self.calculate_narrative_coherence(sorted_nodes)
        engagement_intensity = self.calculate_engagement_intensity(sorted_nodes)
        
        # Identify branch and convergence points
        branch_points = [
            node.message_id for node in sorted_nodes
            if node.branch_factor > 2 or node.influence_score > 0.7
        ]
        
        convergence_points = [
            node.message_id for node in sorted_nodes
            if 'conclusion' in node.narrative_elements or 'agreement' in node.narrative_elements
        ]
        
        flow_id = f"flow_{guild_id}_{channel_id}_{start_time.timestamp()}"
        
        return ConversationFlow(
            flow_id=flow_id,
            start_node=sorted_nodes[0].message_id,
            end_nodes=[sorted_nodes[-1].message_id],
            flow_type=flow_type,
            participants=participants,
            duration_minutes=duration_minutes,
            narrative_coherence=narrative_coherence,
            engagement_intensity=engagement_intensity,
            branch_points=branch_points,
            convergence_points=convergence_points,
            nodes=sorted_nodes
        )
    
    def update_flow_mapping(self, message: discord.Message, analysis: dict):
        """Update conversation flow mapping with new message"""
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        
        # Initialize guild data if needed
        if guild_id not in self.flow_mappings:
            self.flow_mappings[guild_id] = {}
        
        if channel_id not in self.flow_mappings[guild_id]:
            self.flow_mappings[guild_id][channel_id] = {
                'active_flows': {},
                'completed_flows': [],
                'flow_statistics': {
                    'total_flows': 0,
                    'avg_duration': 0,
                    'most_common_type': 'linear',
                    'highest_engagement': 0
                }
            }
        
        channel_data = self.flow_mappings[guild_id][channel_id]
        
        # Create conversation node
        node = self.create_conversation_node(message, analysis)
        
        # Determine if this continues an existing flow or starts a new one
        active_flow_id = self._find_active_flow(node, channel_data['active_flows'])
        
        if active_flow_id:
            # Add to existing flow
            flow_data = channel_data['active_flows'][active_flow_id]
            flow_data['nodes'].append(node.to_dict())
            flow_data['last_activity'] = node.timestamp
            flow_data['participants'].add(node.user_id)
            
            # Update response counts for connected messages
            for connection in node.connections:
                for existing_node in flow_data['nodes']:
                    if existing_node['message_id'] == connection:
                        existing_node['response_count'] += 1
                        break
                        
        elif node.influence_score > self.influence_threshold:
            # Start new flow
            flow_id = f"flow_{guild_id}_{channel_id}_{message.created_at.timestamp()}"
            channel_data['active_flows'][flow_id] = {
                'flow_id': flow_id,
                'start_time': node.timestamp,
                'last_activity': node.timestamp,
                'participants': {node.user_id},
                'nodes': [node.to_dict()]
            }
        
        # Clean up old flows and create completed flow objects
        self._cleanup_and_complete_flows(channel_data)
        
        # Save updated mappings
        self._save_data(self.mapping_file, self.flow_mappings)
    
    def _find_active_flow(self, node: ConversationNode, active_flows: dict) -> Optional[str]:
        """Find which active flow this node belongs to"""
        current_time = datetime.fromisoformat(node.timestamp)
        
        for flow_id, flow_data in active_flows.items():
            last_activity = datetime.fromisoformat(flow_data['last_activity'])
            
            # Check if within time window
            if current_time - last_activity < timedelta(minutes=self.response_timeout):
                # Check connections
                for connection in node.connections:
                    if any(n['message_id'] == connection for n in flow_data['nodes']):
                        return flow_id
                
                # Check if same participant continuing
                if node.user_id in flow_data['participants']:
                    return flow_id
        
        return None
    
    def _cleanup_and_complete_flows(self, channel_data: dict):
        """Clean up old flows and move them to completed"""
        current_time = datetime.now()
        completed_flows = []
        
        for flow_id, flow_data in list(channel_data['active_flows'].items()):
            last_activity = datetime.fromisoformat(flow_data['last_activity'])
            
            # Complete flow if inactive for too long or too long duration
            should_complete = (
                current_time - last_activity > timedelta(minutes=self.response_timeout) or
                current_time - datetime.fromisoformat(flow_data['start_time']) > timedelta(minutes=self.max_flow_duration)
            )
            
            if should_complete and len(flow_data['nodes']) >= self.min_flow_participants:
                # Convert to ConversationFlow object
                nodes = [ConversationNode(**node_data) for node_data in flow_data['nodes']]
                completed_flow = self.create_conversation_flow(nodes, flow_id.split('_')[1], flow_id.split('_')[2])
                
                if completed_flow:
                    completed_flows.append(completed_flow.to_dict())
                    
                del channel_data['active_flows'][flow_id]
        
        # Add completed flows
        channel_data['completed_flows'].extend(completed_flows)
        
        # Update statistics
        if completed_flows:
            stats = channel_data['flow_statistics']
            stats['total_flows'] += len(completed_flows)
            
            # Update average duration
            total_duration = sum(flow['duration_minutes'] for flow in completed_flows)
            if stats['total_flows'] > 0:
                stats['avg_duration'] = (stats['avg_duration'] * (stats['total_flows'] - len(completed_flows)) + total_duration) / stats['total_flows']
            
            # Update most common type
            flow_types = [flow['flow_type'] for flow in channel_data['completed_flows']]
            if flow_types:
                stats['most_common_type'] = max(set(flow_types), key=flow_types.count)
            
            # Update highest engagement
            max_engagement = max(flow['engagement_intensity'] for flow in completed_flows)
            stats['highest_engagement'] = max(stats['highest_engagement'], max_engagement)
        
        # Keep only last 20 completed flows
        if len(channel_data['completed_flows']) > 20:
            channel_data['completed_flows'] = channel_data['completed_flows'][-20:]
    
    def get_flow_analytics(self, guild_id: str, channel_id: str = None) -> dict:
        """Get conversation flow analytics"""
        guild_data = self.flow_mappings.get(guild_id, {})
        
        if channel_id:
            # Channel-specific analytics
            channel_data = guild_data.get(channel_id, {})
            return {
                'active_flows': len(channel_data.get('active_flows', {})),
                'completed_flows': len(channel_data.get('completed_flows', [])),
                'statistics': channel_data.get('flow_statistics', {}),
                'recent_flows': channel_data.get('completed_flows', [])[-5:]
            }
        else:
            # Guild-wide analytics
            total_active = sum(len(channel.get('active_flows', {})) for channel in guild_data.values())
            total_completed = sum(len(channel.get('completed_flows', [])) for channel in guild_data.values())
            
            # Aggregate statistics
            all_flows = []
            for channel in guild_data.values():
                all_flows.extend(channel.get('completed_flows', []))
            
            if all_flows:
                avg_duration = sum(flow['duration_minutes'] for flow in all_flows) / len(all_flows)
                avg_engagement = sum(flow['engagement_intensity'] for flow in all_flows) / len(all_flows)
                avg_coherence = sum(flow['narrative_coherence'] for flow in all_flows) / len(all_flows)
                
                # Flow type distribution
                flow_types = [flow['flow_type'] for flow in all_flows]
                type_distribution = {
                    flow_type: flow_types.count(flow_type) for flow_type in set(flow_types)
                }
            else:
                avg_duration = avg_engagement = avg_coherence = 0
                type_distribution = {}
            
            return {
                'total_active_flows': total_active,
                'total_completed_flows': total_completed,
                'channels_with_flows': len(guild_data),
                'average_duration_minutes': round(avg_duration, 2),
                'average_engagement_intensity': round(avg_engagement, 2),
                'average_narrative_coherence': round(avg_coherence, 2),
                'flow_type_distribution': type_distribution,
                'recent_flows': sorted(all_flows, key=lambda x: x['start_node'])[-10:]
            }
    
    async def track_message_flow(self, message: discord.Message):
        """Main entry point for tracking message in conversation flow"""
        if message.author.bot:
            return
        
        try:
            # Get analysis from engagement tracker
            analysis = self.engagement_tracker.analyze_message_narrative(message)
            
            # Update flow mapping
            self.update_flow_mapping(message, analysis)
            
        except Exception as e:
            logger.error(f"Error tracking conversation flow: {e}")