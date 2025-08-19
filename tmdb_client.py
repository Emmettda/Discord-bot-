import aiohttp
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TMDBClient:
    def __init__(self):
        self.api_key = os.getenv("TMDB_API_KEY", "7ae43574dd2a908845eb5b1b7c5c2464")
        self.base_url = "https://api.themoviedb.org/3"
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to TMDB API"""
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        
        try:
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    logger.error("TMDB API: Unauthorized - Check your API key")
                    return None
                elif response.status == 404:
                    logger.warning(f"TMDB API: Not found - {endpoint}")
                    return None
                else:
                    logger.error(f"TMDB API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error making TMDB request: {e}")
            return None
    
    async def search_movie(self, query: str) -> Optional[Dict]:
        """Search for a movie"""
        params = {
            'query': query,
            'include_adult': False,
            'page': 1
        }
        
        result = await self._make_request('search/movie', params)
        if result and result.get('results'):
            return result['results'][0]  # Return first result
        return None
    
    async def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """Get detailed movie information"""
        return await self._make_request(f'movie/{movie_id}')
    
    async def get_movie_cast(self, movie_id: int) -> Optional[List[Dict]]:
        """Get movie cast information"""
        result = await self._make_request(f'movie/{movie_id}/credits')
        if result:
            return result.get('cast', [])
        return None
    
    async def get_popular_movies(self, page: int = 1) -> Optional[List[Dict]]:
        """Get popular movies"""
        params = {
            'page': page,
            'region': 'US'
        }
        
        result = await self._make_request('movie/popular', params)
        if result:
            return result.get('results', [])
        return None
    
    async def get_upcoming_movies(self, page: int = 1) -> Optional[List[Dict]]:
        """Get upcoming movies"""
        params = {
            'page': page,
            'region': 'US'
        }
        
        result = await self._make_request('movie/upcoming', params)
        if result:
            return result.get('results', [])
        return None
    
    async def get_top_rated_movies(self, page: int = 1) -> Optional[List[Dict]]:
        """Get top rated movies"""
        params = {
            'page': page,
            'region': 'US'
        }
        
        result = await self._make_request('movie/top_rated', params)
        if result:
            return result.get('results', [])
        return None
    
    async def get_now_playing_movies(self, page: int = 1) -> Optional[List[Dict]]:
        """Get now playing movies"""
        params = {
            'page': page,
            'region': 'US'
        }
        
        result = await self._make_request('movie/now_playing', params)
        if result:
            return result.get('results', [])
        return None
    
    async def get_movie_recommendations(self, movie_id: int, page: int = 1) -> Optional[List[Dict]]:
        """Get movie recommendations"""
        params = {'page': page}
        
        result = await self._make_request(f'movie/{movie_id}/recommendations', params)
        if result:
            return result.get('results', [])
        return None
    
    async def get_movie_videos(self, movie_id: int) -> Optional[List[Dict]]:
        """Get movie videos (trailers, etc.)"""
        result = await self._make_request(f'movie/{movie_id}/videos')
        if result:
            return result.get('results', [])
        return None
    
    async def discover_movies(self, **kwargs) -> Optional[List[Dict]]:
        """Discover movies with filters"""
        params = {
            'sort_by': 'popularity.desc',
            'include_adult': False,
            'page': 1,
            **kwargs
        }
        
        result = await self._make_request('discover/movie', params)
        if result:
            return result.get('results', [])
        return None
    
    async def get_genres(self) -> Optional[List[Dict]]:
        """Get list of movie genres"""
        result = await self._make_request('genre/movie/list')
        if result:
            return result.get('genres', [])
        return None
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
