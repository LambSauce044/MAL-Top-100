import requests
import time
from typing import List, Dict, Optional
import json

class MALAnimeFinder:
    def __init__(self, client_id: str):
        """
        Initialize the MAL API client
        
        Args:
            client_id: Your MyAnimeList API Client ID
        """
        self.client_id = client_id
        self.base_url = "https://api.myanimelist.net/v2"
        self.headers = {
            'X-MAL-CLIENT-ID': client_id
        }
        
    def search_top_anime(self, limit: int = 500, offset: int = 0) -> List[Dict]:
        """
        Search for top anime sorted by score
        
        Args:
            limit: Number of results to return (max 500)
            offset: Pagination offset
            
        Returns:
            List of anime data
        """
        url = f"{self.base_url}/anime/ranking"
        
        params = {
            'ranking_type': 'all',  # Get all anime sorted by score
            'limit': limit,
            'offset': offset,
            'fields': 'id,title,main_picture,mean,rank,popularity,num_scoring_users,rating'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()['data']
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return []
    
    def get_anime_details(self, anime_id: int) -> Optional[Dict]:
        """
        Get detailed information for a specific anime including rating distribution
        
        Args:
            anime_id: MAL anime ID
            
        Returns:
            Anime details with rating distribution
        """
        url = f"{self.base_url}/anime/{anime_id}"
        
        params = {
            'fields': 'id,title,main_picture,mean,rank,popularity,num_scoring_users,statistics'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching anime {anime_id}: {e}")
            return None
    
    def find_top_anime_with_high_10_ratings(self, min_10_ratings: int = 35, top_n: int = 100, 
                                            min_score: float = 0.0, min_users: int = 1000) -> List[Dict]:
        """
        Find top anime with high scores and minimum number of 10 ratings
        
        Args:
            min_10_ratings: Minimum number of "10" ratings required
            top_n: Number of top anime to return
            min_score: Minimum average score threshold
            min_users: Minimum number of users who rated
            
        Returns:
            List of anime sorted by score
        """
        all_anime = []
        offset = 0
        limit = 500
        
        print("Fetching top anime from MAL...")
        
        # Fetch multiple pages to get enough anime
        for page in range(5):  # Get up to 2500 anime
            print(f"Fetching page {page + 1}...")
            anime_batch = self.search_top_anime(limit=limit, offset=offset)
            
            if not anime_batch:
                break
                
            all_anime.extend(anime_batch)
            offset += limit
            
            # Be respectful to the API
            time.sleep(0.5)
        
        print(f"Total anime fetched: {len(all_anime)}")
        print("Fetching rating distributions...")
        
        qualified_anime = []
        
        # Check each anime for rating distribution
        for i, anime_item in enumerate(all_anime):
            anime = anime_item['node']
            
            # Skip if no mean score or too few users
            if ('mean' not in anime or anime['mean'] is None or 
                anime['mean'] < min_score or 
                'num_scoring_users' not in anime or 
                anime['num_scoring_users'] < min_users):
                continue
            
            # Get detailed statistics
            details = self.get_anime_details(anime['id'])
            
            if details and 'statistics' in details:
                stats = details['statistics']
                if 'scores' in stats:
                    # Find the count of "10" ratings
                    for score_data in stats['scores']:
                        if score_data['score'] == 10:
                            if score_data['votes'] >= min_10_ratings:
                                qualified_anime.append({
                                    'id': anime['id'],
                                    'title': anime['title'],
                                    'score': anime['mean'],
                                    '10_ratings': score_data['votes'],
                                    'total_ratings': anime.get('num_scoring_users', 0),
                                    'rank': anime.get('rank', 0),
                                    'popularity': anime.get('popularity', 0),
                                    'rating': anime.get('rating', 'N/A'),
                                    'statistics': stats
                                })
                            break
            
            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1} anime... Found {len(qualified_anime)} qualified")
            
            # Rate limiting
            time.sleep(0.1)
        
        # Sort by score (highest first)
        qualified_anime.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N
        return qualified_anime[:top_n]
    
    def save_results(self, anime_list: List[Dict], filename: str = "top_anime_results.json"):
        """
        Save results to JSON file
        
        Args:
            anime_list: List of anime data
            filename: Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(anime_list, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filename}")
    
    def print_results(self, anime_list: List[Dict], max_display: int = 20):
        """
        Print results in a readable format
        
        Args:
            anime_list: List of anime data
            max_display: Maximum number of results to display
        """
        print("\n" + "="*100)
        print(f"TOP {len(anime_list)} ANIME WITH HIGHEST SCORES (Minimum 35 '10' Ratings)")
        print("="*100)
        
        for i, anime in enumerate(anime_list[:max_display], 1):
            print(f"\n{i:3d}. {anime['title']}")
            print(f"     Score: {anime['score']:.2f} | 10 Ratings: {anime['10_ratings']:,} | "
                  f"Total Ratings: {anime['total_ratings']:,}")
            print(f"     Rank: #{anime.get('rank', 'N/A')} | Popularity: #{anime.get('popularity', 'N/A')} | "
                  f"Rating: {anime.get('rating', 'N/A')}")
        
        if len(anime_list) > max_display:
            print(f"\n... and {len(anime_list) - max_display} more")

# Alternative approach using Jikan API (Unofficial but more comprehensive)
class JikanAnimeFinder:
    """
    Alternative using Jikan API (Unofficial MyAnimeList API)
    This might have more detailed rating distribution data
    """
    
    def __init__(self):
        self.base_url = "https://api.jikan.moe/v4"
        self.headers = {
            'User-Agent': 'MAL Top Anime Finder/1.0'
        }
    
    def get_top_anime(self, page: int = 1, limit: int = 25) -> List[Dict]:
        """Get top anime from Jikan API"""
        url = f"{self.base_url}/top/anime"
        params = {
            'page': page,
            'limit': limit
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_anime_statistics(self, mal_id: int) -> Optional[Dict]:
        """Get statistics for a specific anime"""
        url = f"{self.base_url}/anime/{mal_id}/statistics"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Error getting stats for {mal_id}: {e}")
            return None


def main():
    """
    Main function to run the anime finder
    """
    
    # ===== OPTION 1: Using Official MAL API =====
    print("MYANIMELIST TOP ANIME FINDER")
    print("="*50)
    
    # Get your Client ID from https://myanimelist.net/apiconfig
    CLIENT_ID = input("Enter your MyAnimeList Client ID: ").strip()
    
    if not CLIENT_ID:
        print("Client ID is required for the official MAL API.")
        print("You can get one at: https://myanimelist.net/apiconfig")
        print("\nTrying Jikan API instead...")
        use_jikan = True
    else:
        use_jikan = False
    
    if not use_jikan:
        # Use Official MAL API
        finder = MALAnimeFinder(CLIENT_ID)
        
        # Find top 100 anime with minimum 35 "10" ratings
        print("\nSearching for top anime with at least 35 '10' ratings...")
        top_anime = finder.find_top_anime_with_high_10_ratings(
            min_10_ratings=35,
            top_n=100,
            min_score=7.0,  # Minimum score threshold
            min_users=5000   # Minimum number of users who rated
        )
        
        # Print and save results
        if top_anime:
            finder.print_results(top_anime, max_display=30)
            finder.save_results(top_anime, "mal_top_anime.json")
            
            # Summary statistics
            avg_score = sum(a['score'] for a in top_anime) / len(top_anime)
            avg_10_ratings = sum(a['10_ratings'] for a in top_anime) / len(top_anime)
            print(f"\nSUMMARY:")
            print(f"Average Score: {avg_score:.2f}")
            print(f"Average '10' Ratings per Anime: {avg_10_ratings:,.0f}")
            print(f"Total Anime Found: {len(top_anime)}")
        else:
            print("No anime found matching the criteria.")
    
    else:
        # ===== OPTION 2: Using Jikan API =====
        print("\nUsing Jikan API (unofficial)...")
        print("Note: This method might be slower due to rate limiting.")
        
        jikan_finder = JikanAnimeFinder()
        qualified_anime = []
        
        # Jikan has rate limits (60 requests/minute, 3 requests/second)
        # We'll be conservative
        pages_to_check = 10  # 10 pages * 25 items = 250 anime
        
        for page in range(1, pages_to_check + 1):
            print(f"Checking page {page}...")
            anime_list = jikan_finder.get_top_anime(page=page, limit=25)
            
            for anime in anime_list:
                try:
                    stats = jikan_finder.get_anime_statistics(anime['mal_id'])
                    
                    if stats and 'scores' in stats:
                        for score in stats['scores']:
                            if score['score'] == 10 and score['votes'] >= 35:
                                qualified_anime.append({
                                    'title': anime['title'],
                                    'score': anime['score'],
                                    '10_ratings': score['votes'],
                                    'total_ratings': stats['total'],
                                    'url': anime['url'],
                                    'episodes': anime.get('episodes', 'N/A'),
                                    'status': anime.get('status', 'N/A')
                                })
                                break
                    
                    # Rate limiting
                    time.sleep(0.34)  # ~3 requests per second
                    
                except Exception as e:
                    print(f"Error processing {anime.get('title', 'Unknown')}: {e}")
                    continue
        
        # Sort by score
        qualified_anime.sort(key=lambda x: x['score'], reverse=True)
        
        # Print results
        print("\n" + "="*100)
        print(f"TOP ANIME WITH MINIMUM 35 '10' RATINGS (Jikan API)")
        print("="*100)
        
        for i, anime in enumerate(qualified_anime[:50], 1):
            print(f"\n{i:3d}. {anime['title']}")
            print(f"     Score: {anime['score']:.2f} | 10 Ratings: {anime['10_ratings']:,} | "
                  f"Total: {anime['total_ratings']:,}")
            print(f"     URL: {anime['url']}")
        
        # Save results
        if qualified_anime:
            with open('jikan_top_anime.json', 'w', encoding='utf-8') as f:
                json.dump(qualified_anime, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to jikan_top_anime.json")
            print(f"Total found: {len(qualified_anime)}")


if __name__ == "__main__":
    main()