# Discord Bot - replit.md

## Overview

This is a comprehensive Discord bot built with Python that provides moderation, movie information, anime recommendations, and user management features. The bot uses a modular architecture with separate command cogs for different functionalities and includes a simple JSON-based database system for data persistence.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture
- **Framework**: Discord.py with slash commands support
- **Architecture Pattern**: Modular cog-based system
- **Database**: File-based JSON storage
- **API Integration**: TMDB (The Movie Database) API for movie data
- **Logging**: Comprehensive logging to both file and console

### Key Design Decisions

**Modular Cog System**: The bot uses Discord.py's cog system to separate functionality into logical modules (moderation, movies, anime, user management). This promotes code organization and maintainability.

**JSON File Storage**: Simple file-based JSON storage was chosen for simplicity and ease of deployment. Files are stored in a `data/` directory with separate files for users, warnings, and favorites.

**Slash Commands**: The bot implements Discord's modern slash command system for better user experience and discoverability.

## Key Components

### 1. Main Bot Class (`main.py`)
- **ModeratorBot**: Main bot class that inherits from `commands.Bot`
- Handles bot initialization, cog loading, and startup hooks
- Configures Discord intents for message content, members, and guilds

### 2. Command Cogs
- **ModerationCog**: Handles server moderation (kick, ban, mute, warnings) + Auto-moderation system
- **MoviesCog**: Provides movie information via TMDB API
- **AnimeCog**: Offers anime recommendations from a curated database
- **UserManagementCog**: Manages user preferences and favorite characters

### 3. Utilities
- **Database**: Simple JSON-based data persistence layer
- **TMDBClient**: Async HTTP client for The Movie Database API
- **Helpers**: Common utility functions for time parsing and embed creation
- **AutoModerationSystem**: Advanced auto-moderation with spam detection and content filtering

## Data Flow

### Command Processing
1. User issues slash command
2. Discord.py routes to appropriate cog method
3. Cog processes command, potentially accessing database or external APIs
4. Response sent back to user via Discord embed

### Data Persistence
1. User actions trigger database operations
2. Database class handles JSON file read/write operations
3. Data stored in structured format in `data/` directory

### External API Integration
1. Movie commands trigger TMDB API requests
2. TMDBClient handles async HTTP requests with error handling
3. Movie data formatted and returned as Discord embeds

## External Dependencies

### Required Packages
- `discord.py`: Discord API wrapper
- `aiohttp`: Async HTTP client for API requests
- Standard library: `json`, `os`, `logging`, `datetime`, `asyncio`

### External APIs
- **TMDB API**: Movie and TV show information
  - Requires API key (provided in code)
  - Used for movie search and detailed information

### Data Storage
- **JSON Files**: Local file-based storage
  - `data/users.json`: User data and preferences
  - `data/warnings.json`: Moderation warnings
  - `data/favorites.json`: User favorite characters
  - `data/automod_violations.json`: Auto-moderation violation logs
  - `data/automod_settings.json`: Auto-moderation configuration per guild

## Deployment Strategy

### Environment Setup
- Python 3.8+ required
- Discord bot token needed (stored in environment variables)
- TMDB API key (hardcoded but should be moved to environment variables)

### File Structure
```
/
├── main.py                 # Bot entry point
├── bot/
│   ├── commands/          # Command cogs
│   │   ├── moderation.py
│   │   ├── movies.py
│   │   ├── anime.py
│   │   └── user_management.py
│   └── utils/             # Utility modules
│       ├── database.py
│       ├── tmdb_client.py
│       └── helpers.py
└── data/                  # JSON data files
    ├── users.json
    ├── warnings.json
    └── favorites.json
```

### Scalability Considerations
- Current JSON storage is suitable for small to medium servers
- For larger deployments, consider migrating to a proper database (PostgreSQL with Drizzle ORM would be a good choice)
- Bot is designed to be easily extensible with additional cogs

### Security Notes
- Bot requires specific Discord permissions for moderation features
- Permission checking implemented for administrative commands
- API keys should be moved to environment variables for production

## Recent Changes (July 14, 2025)

### Latest Updates (July 14, 2025 - Phase 4)

#### 1. Music System Removed
- **Complete Removal**: All music functionality removed due to persistent WebSocket connection issues
- **Voice System Disabled**: Voice states intents disabled, all voice-related commands removed
- **Clean Architecture**: Bot now focuses on core lookup and information retrieval features
- **Stable Operation**: Eliminated connection loops and WebSocket timeouts

#### 2. Comprehensive Lookup System
- **Song Lookup**: Last.fm API integration for detailed song information including play counts, listeners, duration, and descriptions
- **Book Lookup**: Open Library API integration for book details including authors, publication info, page counts, and cover images
- **Manga Lookup**: MyAnimeList (Jikan API) integration for manga information including synopsis, scores, genres, and cover art
- **Comic Lookup**: Placeholder system ready for Comic Vine API integration (requires API key)
- **Unified Interface**: All lookups use consistent embed formatting with rich information display

#### 3. Animated Status Indicators System
- **Dynamic Status Rotation**: Bot status changes automatically every 3 seconds through predefined sequences
- **8 Animation Sequences**: Default, search, loading, music, books, manga, gaming, idle, and celebration themes
- **Smart Status Triggering**: Lookup commands automatically trigger appropriate status animations
- **Visual Emoji Animations**: 6 different emoji animation types (loading dots, spinning, bouncing, pulsing, musical, books, search)
- **Contextual Status Updates**: Status reflects current bot activity and server statistics
- **24/7 Continuous Animation**: Seamless status updates with proper error handling and recovery

#### 4. Community Engagement Narrative Tracker
- **Message Analysis**: Real-time analysis of messages for narrative elements (stories, emotions, questions, celebrations)
- **Conversation Threads**: Intelligent tracking of conversation continuity and thread development
- **Narrative Patterns**: Detection of 6 narrative types (story_start, emotional_moments, community_building, questions, celebration, support)
- **Engagement Scoring**: Sophisticated scoring system for message influence and community impact
- **Community Mood Tracking**: Real-time community mood analysis and trend monitoring
- **Historical Analytics**: Comprehensive data persistence and trend analysis over time

#### 5. Intelligent Conversation Flow Mapper
- **Flow Detection**: Automatic detection of 5 conversation flow types (linear, branching, circular, convergent, parallel)
- **Connection Analysis**: Advanced analysis of message connections, replies, and topic continuity
- **Narrative Coherence**: Calculation of conversation coherence and narrative consistency
- **Influence Scoring**: Sophisticated influence scoring for message impact on conversation flow
- **Branch Point Detection**: Identification of conversation branch points and convergence areas
- **Flow Completion**: Automatic flow completion and historical archival with metrics

### New Lookup Commands Added (5 total)
- `/song <query>` - Search for detailed song information using Last.fm
- `/book <query>` - Search for book information using Open Library
- `/manga <query>` - Search for manga information using MyAnimeList
- `/comic <query>` - Search for comic information (requires API key setup)
- `/lookup_help` - Show comprehensive help for all lookup commands

### New Animation Commands Added (4 total)
- `/animate <type> [duration]` - Trigger specific animation sequences manually
- `/status_info` - View detailed information about the animated status system
- `/status_control <action>` - Control the animated status system (Admin only)
- `/demo_animations` - Demonstrate all available animation types

### New Status Command Added (1 total)
- `/system_status` - Check bot status and animated features with celebration animation

### New Engagement Analytics Commands Added (4 total)
- `/engagement_summary [days]` - View comprehensive community engagement summary with storytelling metrics
- `/conversation_flows [channel]` - Analyze conversation flow patterns and types (linear, branching, circular, convergent, parallel)
- `/narrative_insights [period]` - Get deep narrative insights with community characteristics and growth recommendations
- `/engagement_leaderboard [category]` - View engagement rankings by overall engagement, storytelling, conversation starters, or participation

### Technical Implementation Details

#### Lookup System Architecture
- **Last.fm Integration**: Public API for song search and detailed track information
- **Open Library Integration**: Book search with comprehensive metadata and cover images
- **MyAnimeList Integration**: Manga search via Jikan API with ratings and detailed information
- **Unified Request System**: Common HTTP request handling with error recovery
- **Rich Embed Display**: Consistent formatting with thumbnails, fields, and external links

#### Animated Status System
- **Status Manager Class**: Centralized management of all status animations and sequences
- **Task-Based Updates**: Discord.py tasks for reliable 3-second status rotation
- **Animation Sequences**: Pre-defined status sequences for different bot activities
- **Visual Indicators**: Random emoji selection for enhanced visual appeal
- **State Management**: Proper tracking of current sequence and animation step
- **Error Handling**: Comprehensive error recovery and logging for status updates

#### Enhanced Data Persistence
- **No Additional Storage**: Lookup system uses APIs without local caching
- **Status State**: In-memory status management with automatic recovery
- **Session Management**: Proper HTTP session handling for API requests

#### Community Engagement System
- **EngagementTracker Class**: Real-time message analysis and narrative pattern detection
- **ConversationFlowMapper Class**: Intelligent conversation flow analysis and mapping
- **Narrative Pattern Recognition**: 6 narrative types with sophisticated scoring algorithms
- **Flow Type Detection**: 5 conversation flow patterns with coherence and engagement metrics
- **Community Analytics**: Comprehensive mood tracking and storytelling insights
- **Historical Data**: Persistent storage for engagement trends and flow analytics

#### Enhanced Data Storage
- **engagement_narratives.json**: Community engagement scores and narrative tracking
- **conversation_threads.json**: Active conversation threads and historical data
- **community_narratives.json**: Guild-wide narrative themes and storytelling metrics
- **conversation_flows.json**: Completed conversation flows with analytics
- **flow_mappings.json**: Active flow tracking and statistics
- **flow_patterns.json**: Pattern recognition and flow analysis data

### Bot Statistics (Updated)
- **Total Commands**: 95 slash commands (4 new engagement analytics commands added)
- **Lookup Commands**: 5 commands (song, book, manga, comic, help)
- **Animation Commands**: 4 commands (animate, status_info, status_control, demo)
- **Status Commands**: 1 command (system_status)
- **Engagement Analytics Commands**: 4 commands (engagement_summary, conversation_flows, narrative_insights, engagement_leaderboard)
- **Music System**: Completely removed (0 commands)
- **All Other Categories**: Unchanged from previous count

### Performance & Reliability Improvements
- **Eliminated Connection Issues**: No more WebSocket timeouts or rapid join/leave behavior
- **Stable API Integration**: Reliable external API connections with proper error handling
- **Enhanced Visual Experience**: Animated status indicators provide engaging user experience
- **Reduced Resource Usage**: Removed resource-intensive voice processing and audio streaming
- **Improved Error Recovery**: Better handling of API failures and network issues

### Latest Music System Fixes (July 14, 2025 - Phase 3) - REMOVED

#### 1. Fixed Music Player Connection Issues
- **Resolved Rapid Join/Leave Problem**: Fixed the bot repeatedly joining and leaving voice channels
- **Enhanced Connection Stability**: Improved voice client management with proper cleanup and state tracking
- **Better Error Handling**: Added comprehensive error handling for connection failures and timeouts
- **Force Disconnect Logic**: Implemented proper disconnection with force flag to prevent hanging connections

#### 2. Improved Audio Streaming
- **Enhanced YT-DL Configuration**: Added timeout settings, retry logic, and better error handling
- **Optimized FFmpeg Options**: Improved audio streaming parameters for better quality and stability
- **Retry System**: Added 3-attempt retry logic for failed audio extractions
- **Connection Delays**: Added strategic delays to ensure stable connections

#### 3. Voice State Management
- **Voice State Listener**: Added automatic cleanup when bot is disconnected from voice channels
- **Connection Validation**: Proper checking of voice client connection states
- **Queue Management**: Automatic queue clearing when disconnected
- **Memory Cleanup**: Prevents memory leaks from orphaned voice clients

#### 4. Enhanced Music Commands
- **Improved Join Command**: Better connection handling with timeout and error recovery
- **Fixed Leave Command**: Proper cleanup with force disconnect to prevent hanging
- **Enhanced Play Command**: Better connection establishment with stability delays
- **New Voice Status Command**: `/voice_status` - Check connection status and queue information

#### 5. 24/7 Uptime Verification
- **Keep-Alive System Confirmed**: Flask server running on port 8080 with health monitoring
- **Auto-Ping Mechanism**: Self-pinging every 5 minutes to prevent Replit sleep
- **Health Endpoint**: `/health` endpoint responding properly for monitoring
- **Continuous Operation**: Bot stays online 24/7 without interruption



## Recent Changes (July 14, 2025)

### Major Feature Updates

#### 1. Advanced Auto-Moderation System
- **Real-time Message Monitoring**: Automatically scans all messages for policy violations
- **Spam Detection**: Configurable thresholds for message frequency and duplicate content
- **Content Filtering**: Detects excessive caps, suspicious links, Discord invites, mentions, and emojis
- **Intelligent Response**: Automatic warning system with escalating punishments (warnings → mutes)
- **Comprehensive Logging**: Detailed violation tracking with statistics and user history
- **Configurable Settings**: Per-guild customization of all moderation parameters

#### 2. Anime Streaming Recommendations
- **Streaming Platform Integration**: Added streaming platform information to anime database
- **Platform-Specific Search**: Find anime available on specific platforms (Netflix, Crunchyroll, etc.)
- **Where to Watch**: Quickly find where to stream any anime in the database
- **Visual Platform Indicators**: Emoji-based platform identification for easy recognition

#### 3. Comprehensive Statistics System
- **Message Tracking**: Detailed message statistics including count, character count, and activity patterns
- **Command Usage Tracking**: Monitor which commands are used most frequently
- **Leaderboards**: Server-wide rankings for most active users and command usage
- **Activity Charts**: Visual representation of user activity over time periods
- **Server Analytics**: Overall server statistics and popular command insights

#### 4. Fun & Entertainment Features
- **Quote Collection System**: Automatically collects memorable quotes from users and randomly shares them
- **Meme Integration**: Fetches fresh memes from Reddit with various subreddit options
- **Gambling System**: Complete casino with coinflip, dice, and slot machines
- **Daily Rewards**: Users can claim daily coins for gambling activities
- **Balance Management**: Track wins, losses, and gambling statistics

#### 5. Server Status System
- **Custom Status Messages**: Users can set personalized server statuses (sleeping, afk, busy, etc.)
- **Status Tracking**: View anyone's current status and when it was set
- **Server Status Overview**: See all current user statuses in one place
- **Timeout Information**: Check timeout details for muted users

### New Commands Added (17 total)

#### Statistics Commands (4)
- `/stats` - View your server statistics
- `/leaderboard` - View server leaderboards
- `/server_stats` - View overall server statistics
- `/activity_chart` - View your activity chart

#### Fun & Games Commands (7)
- `/quote` - Get a random quote from members
- `/meme` - Get a random meme
- `/balance` - Check your gambling balance
- `/daily` - Claim daily coins
- `/coinflip` - Flip a coin and bet
- `/dice` - Roll dice and bet
- `/slots` - Play slot machine

#### Status Commands (4)
- `/set_status` - Set your server status
- `/status` - Check someone's status
- `/server_statuses` - View all server statuses
- `/timeout_info` - Check timeout information

#### Anime Streaming Commands (3)
- `/anime_streaming` - Find anime by platform
- `/anime_platforms` - View all platforms
- `/anime_where_to_watch` - Find where to watch anime

### Technical Implementation Details
- **StatsTracker Class**: Comprehensive statistics tracking with JSON persistence
- **Quote Collection**: Intelligent quote harvesting with rare random responses
- **Reddit API Integration**: Real-time meme fetching from multiple subreddits
- **Gambling Engine**: Fair gambling system with house edge and balance management
- **Status Management**: Persistent status tracking with timestamps
- **Enhanced Message Handling**: Integrated stats tracking, quote collection, and auto-moderation

### Database Extensions
- **user_stats.json**: Message statistics and activity tracking
- **message_stats.json**: Detailed message analytics
- **command_stats.json**: Command usage tracking
- **quotes.json**: Collected user quotes with metadata
- **gambling.json**: User gambling balances and statistics
- **user_status.json**: Server status messages and timestamps

#### 6. Welcome System
- **Automatic Role Assignment**: New members automatically receive "laylas e-kitten" role
- **Full Mod Permissions**: Welcome role has complete administrator access
- **Personalized Welcome Messages**: Custom embeds with server info and bot features
- **Role Creation**: Automatically creates welcome role if it doesn't exist
- **Welcome Testing**: Commands to test and manage the welcome system

### New Welcome Commands Added (2 total)
- `/welcome_test` - Test the welcome system with any user
- `/welcome_role_info` - View detailed information about the welcome role

#### 7. Jarvis Response System
- **Random AI Responses**: Bot randomly responds with iconic Jarvis quotes after command usage
- **Contextual Responses**: Different quote categories based on command type (moderation, entertainment, stats, fun)
- **30% Response Rate**: Balanced frequency to avoid overwhelming users
- **Styled Embeds**: Professional blue embeds with Jarvis branding
- **Manual Trigger**: Direct `/jarvis` command for on-demand responses

### New Jarvis Command Added (1 total)
- `/jarvis` - Get a random Jarvis response

#### 8. Music Player System
- **Voice Channel Integration**: Full voice channel support for music playback
- **Multi-Platform Support**: Works with YouTube, Spotify, and Apple Music links
- **Advanced Queue Management**: Queue system with shuffle, loop, and skip functionality
- **Volume Control**: Adjustable volume from 0-100% with persistent settings
- **Smart URL Processing**: Automatically detects and processes different music platform URLs
- **Search Functionality**: Can search for songs by name or artist
- **Playlist Support**: Supports Spotify playlists (when credentials provided)
- **Real-time Controls**: Pause, resume, skip, and stop functionality
- **Now Playing Display**: Shows current song information and queue status

### New Music Commands Added (12 total)
- `/join` - Join voice channel
- `/leave` - Leave voice channel  
- `/play` - Play from YouTube/Spotify/Apple Music URLs or search
- `/pause` - Pause current song
- `/resume` - Resume current song
- `/stop` - Stop music and clear queue
- `/skip` - Skip to next song
- `/queue` - Show current music queue
- `/volume` - Set volume (0-100%)
- `/loop` - Toggle loop mode
- `/shuffle` - Shuffle queue
- `/now_playing` - Show currently playing song

### Latest Improvements (July 14, 2025 - Phase 2)

#### 1. Enhanced Music System
- **Fixed Audio Streaming**: Improved YouTube-DL configuration for better audio quality and reliability
- **Real-time Audio**: Enhanced streaming capabilities with proper FFmpeg options and reconnection handling
- **Better Format Support**: Optimized for M4A/best audio formats with proper buffering
- **Error Handling**: Comprehensive error handling for failed audio extraction and streaming

#### 2. Meme System Overhaul  
- **Google-Only Integration**: Switched from Reddit to Google-based meme APIs for better reliability
- **Enhanced API Sources**: Multiple backup meme services for consistent content delivery
- **Improved Response Time**: Faster meme fetching with better error handling

#### 3. Streaming Sites Directory
- **Comprehensive Database**: 25+ best streaming sites across all categories
- **Content Categories**: Movies, TV shows, anime, live TV, sports, documentaries
- **Safety Information**: Built-in safety tips and usage guidelines
- **Random Recommendations**: Smart random streaming site suggestions
- **Platform-Specific Search**: Find content by streaming platform

#### 4. 24/7 Uptime System
- **Keep-Alive Integration**: Flask-based health monitoring system
- **Auto-Ping Mechanism**: Self-pinging every 5 minutes to prevent sleep
- **Health Endpoints**: `/health` endpoint for monitoring bot status
- **Continuous Operation**: Never sleeps or shuts down on Replit

#### 5. Advanced Statistics System
- **Detailed User Analytics**: Comprehensive tracking of user behavior patterns
- **Activity Heatmaps**: Hourly activity tracking and peak usage analysis
- **Command Usage Statistics**: Track most-used commands per user and server
- **Daily Streak System**: Track consecutive daily activity streaks
- **Channel Activity**: Monitor most active channels and user engagement
- **Comparative Analytics**: Compare statistics between users
- **Server-Wide Analytics**: Comprehensive server metrics and insights

#### 6. RPG Adventure System
- **Character Classes**: 5 unique classes (Warrior, Mage, Archer, Rogue, Paladin)
- **Equipment System**: Weapons and armor with stat bonuses
- **Quest System**: Monster battles with EXP and gold rewards
- **Leveling System**: Character progression with stat increases
- **PvP Combat**: Player vs player battles with rankings
- **Shop System**: Buy equipment to improve character stats
- **Leaderboards**: Multiple ranking categories (level, gold, PvP wins)
- **Combat Simulation**: Turn-based battle system with detailed logs

### New Commands Added (11 total)

#### Streaming Commands (2)
- `/streaming_sites` - Get best streaming sites by category
- `/random_streaming` - Random streaming site recommendation

#### Enhanced Analytics Commands (3)  
- `/detailed_stats` - Comprehensive user statistics with activity patterns
- `/server_analytics` - Server-wide analytics and insights
- `/compare_stats` - Compare your stats with another user

#### RPG Adventure Commands (6)
- `/rpg_start` - Begin RPG adventure by choosing character class
- `/rpg_profile` - View detailed character profile and stats
- `/rpg_quest` - Go on quests to fight monsters and gain EXP
- `/rpg_shop` - Browse and buy weapons/armor
- `/rpg_buy` - Purchase equipment from the shop
- `/rpg_battle` - Challenge other players to PvP combat
- `/rpg_leaderboard` - View rankings by level, gold, or PvP wins

### Technical Implementation Details

#### Keep-Alive System
- **Flask Server**: Runs on port 8080 with health monitoring
- **Background Threading**: Separate threads for server and ping system
- **Environment Detection**: Smart URL detection for Replit deployments
- **Logging Integration**: Comprehensive logging for monitoring uptime

#### Enhanced Data Persistence
- **detailed_stats.json**: Advanced user analytics and activity tracking
- **rpg_data.json**: Complete RPG character data and progression
- **dungeon_sessions.json**: Active dungeon instances (future expansion)
- **guild_battles.json**: Guild-based battle tournaments (future expansion)

#### Advanced Music Integration
- **Improved YT-DL**: Better format selection and audio quality
- **Stream Optimization**: Enhanced buffering and reconnection handling
- **Error Recovery**: Robust error handling for failed extractions

#### 7. Advanced Music Recommendation Engine
- **Spotify API Integration**: Full Spotify API support for track recommendations and artist discovery
- **Collaborative Filtering**: AI-powered user similarity matching for personalized recommendations
- **Mood-Based Recommendations**: 8 different mood categories with genre-specific suggestions
- **Music Profile System**: Comprehensive user preference tracking and listening history
- **Multi-Source Discovery**: Spotify, Last.FM, and community-based recommendation algorithms
- **Smart Playlist Generation**: Auto-generated playlists based on user behavior and preferences
- **Listening Activity Tracking**: Real-time tracking of music listening patterns for improved suggestions
- **Artist Discovery Engine**: Find similar artists and songs based on listening history

### New Music Recommendation Commands Added (5 total)
- `/music_preferences` - Set your music preferences for better recommendations
- `/music_recommend` - Get personalized recommendations (mixed, spotify, collaborative, lastfm)
- `/music_mood` - Get mood-based music recommendations (8 moods available)
- `/music_discover` - Discover similar artists and songs based on search input
- `/music_profile` - View comprehensive music profile and listening statistics

### Technical Implementation Details

#### Music Recommendation Engine
- **Spotify Integration**: Full API support with track analysis and audio features
- **Collaborative Filtering Algorithm**: Calculates user similarity based on genres, artists, and mood preferences
- **Last.FM API**: Secondary music discovery service for enhanced recommendations
- **Listening History Tracking**: Real-time activity monitoring integrated with music player
- **Preference Learning**: Machine learning-style preference updates based on listening behavior
- **Multi-Modal Recommendations**: Combines multiple algorithms for balanced suggestions

#### Enhanced Data Persistence
- **music_preferences.json**: User music preferences and taste profiles
- **listening_history.json**: Comprehensive listening activity and statistics
- **user_playlists.json**: Custom user playlists and favorites
- **recommendations_cache.json**: Cached recommendations for performance optimization

#### 8. Interactive User Profile Badges System
- **Achievement Tracking**: 30+ unique badges across 6 categories (Activity, Music, Gaming, Social, Commands, Special)
- **Rarity System**: 5 rarity tiers (Common, Uncommon, Rare, Epic, Legendary) with different point values
- **Progress Tracking**: Real-time progress monitoring for badge requirements
- **Database Integration**: PostgreSQL-backed system for reliable data persistence
- **Level System**: Experience points and leveling based on badge collection and activity
- **Leaderboards**: Server rankings by total badges, points, and user level
- **Visual Profiles**: Rich embed profiles showcasing badges, progress, and achievements
- **Auto-Detection**: Automatic badge awarding based on user activity and milestones
- **Admin Controls**: Manual badge awarding system for special recognition

### New Profile Badge Commands Added (4 total)
- `/profile` - View comprehensive user profile with badges and statistics
- `/badges` - Browse all available badges with filtering by category and rarity
- `/badge_leaderboard` - View server badge rankings and competition
- `/award_badge` - Manually award special badges (Administrator only)

### Technical Implementation Details

#### Badge System Architecture
- **PostgreSQL Database**: Three main tables for badges, progress tracking, and user statistics
- **Real-time Tracking**: Automatic progress updates based on message activity and command usage
- **Achievement Engine**: Smart requirement checking for milestone-based badge awarding
- **Pagination System**: Interactive badge browsing with previous/next navigation
- **Integration Layer**: Connected to existing stats, music, and gaming systems

#### Badge Categories & Requirements
- **Activity Badges**: Message count milestones, daily streaks, time-based activity
- **Music Badges**: Song plays, music preferences setup, playlist creation
- **Gaming Badges**: RPG progression, gambling achievements, quest completion
- **Social Badges**: Community interaction, helping behavior, time-based activity
- **Command Badges**: Specific command usage thresholds and feature exploration
- **Special Badges**: Manual awards for exceptional community contribution

#### Enhanced Data Persistence
- **user_badges**: Badge ownership and earning timestamps
- **badge_progress**: Real-time requirement progress tracking
- **user_profile_stats**: Comprehensive profile statistics and level progression

#### 9. Message Scheduling & Farewell System
- **Scheduled Messages**: Plan and send messages at specific times (up to 1 week in advance)
- **Farewell Messages**: Automatic goodbye messages when members leave the server
- **Custom Templates**: Support for embed formatting and variable placeholders
- **Permission Controls**: Manage Messages permission required for scheduling
- **Testing System**: Built-in farewell message testing for admins

#### 10. Roblox Integration (Bloxbat-style)
- **Account Linking**: Connect Discord accounts to Roblox profiles
- **Live Status Tracking**: See who's currently playing what Roblox games
- **Profile Viewing**: Display Roblox avatars, stats, and account information
- **Group Integration**: Search and view Roblox group information and membership
- **User Search**: Find Roblox users and view their profiles
- **Server Activity**: Track Roblox activity across all linked server members

#### 11. Gaming Platform Integration
- **Multi-Platform Support**: Xbox Live, PlayStation, Nintendo, Steam, Epic Games, Destiny 2
- **Account Linking**: Connect multiple gaming platform accounts per user
- **Profile Viewing**: Display gaming statistics and account information
- **API Integration Ready**: Structured for Destiny 2 (Bungie API), Xbox Live, and Steam APIs
- **Gaming Leaderboards**: Server rankings by number of linked platforms
- **Cross-Platform Community**: View all gaming activity in one place

### New Commands Added (20 total)

#### Message Scheduling Commands (4)
- `/schedule_message` - Schedule messages to send at specific times
- `/list_scheduled` - View all scheduled messages for the server
- `/setup_farewell` - Configure farewell messages for departing members
- `/test_farewell` - Test the farewell message system

#### Roblox Integration Commands (7)
- `/roblox_link` - Link Discord account to Roblox profile
- `/roblox_profile` - View comprehensive Roblox profile information
- `/roblox_search` - Search for Roblox users by username
- `/roblox_group` - Get detailed Roblox group information
- `/roblox_group_search` - Search for Roblox groups by name
- `/roblox_status` - Check who's currently playing Roblox games

#### Gaming Platform Commands (9)
- `/link_gaming_account` - Link Xbox, PlayStation, Steam, etc. accounts
- `/gaming_profile` - View all linked gaming platform accounts
- `/destiny_stats` - View Destiny 2 player statistics (requires Bungie API)
- `/xbox_profile` - View Xbox Live profile information (requires Xbox API)
- `/steam_profile` - View Steam profile and game library (requires Steam API)
- `/gaming_leaderboard` - Server leaderboard by linked gaming platforms
- `/unlink_gaming` - Remove linked gaming platform accounts

### Technical Implementation Details

#### Message Scheduling System
- **Task-Based Scheduler**: Runs every minute to check for due messages
- **Persistent Storage**: JSON-based storage for scheduled messages
- **Embed Support**: Rich embed formatting with title and description options
- **Variable Substitution**: Dynamic content with user/server placeholders
- **Time Management**: Support for relative and absolute time scheduling

#### Roblox API Integration
- **Real-Time Data**: Live status checking and game activity monitoring
- **Profile Caching**: Efficient avatar and profile data retrieval
- **Group Management**: Complete group search and information display
- **Presence Detection**: Real-time game playing status and activity tracking

#### Gaming Platform Architecture
- **Multi-API Ready**: Structured for Bungie API, Xbox Live, Steam API integration
- **Account Management**: Secure linking and storage of gaming platform accounts
- **Platform Detection**: Automatic platform identification and validation
- **Statistics Aggregation**: Cross-platform gaming activity tracking

#### Enhanced Data Persistence
- **scheduled_messages.json**: Timed message queue and delivery tracking
- **farewell_settings.json**: Per-server farewell configuration
- **roblox_users.json**: Discord-to-Roblox account mappings
- **gaming_accounts.json**: Multi-platform gaming account links

### Bot Statistics (Updated)
- **Total Commands**: 100 slash commands across 17 categories
- **Moderation**: 13 commands (8 basic + 5 auto-moderation)
- **Entertainment**: 10 commands (4 movies + 6 anime)
- **Statistics**: 4 commands
- **Fun & Games**: 7 commands
- **Status & Info**: 4 commands
- **User Management**: 5 commands
- **Welcome System**: 2 commands
- **Music Player**: 12 commands
- **Music Recommendations**: 5 commands
- **Streaming Sites**: 2 commands
- **Enhanced Analytics**: 3 commands
- **RPG Adventures**: 7 commands
- **Profile & Badges**: 4 commands
- **Message Scheduling**: 4 commands
- **Roblox Integration**: 6 commands
- **Gaming Platforms**: 7 commands
- **Special**: 1 command (Jarvis responses)

### Performance & Reliability
- **24/7 Uptime**: Never sleeps with automated keep-alive system
- **Enhanced Error Handling**: Comprehensive error recovery across all systems
- **Improved Music Streaming**: Better audio quality and connection stability
- **Optimized Data Storage**: Efficient JSON-based persistence with backup systems
- **Real-time Analytics**: Live tracking of user activity and engagement patterns