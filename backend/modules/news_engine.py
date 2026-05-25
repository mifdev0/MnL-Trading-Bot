"""
News Engine - Fetch and process crypto news from multiple sources
"""
import requests
import logging
from typing import List, Dict
from datetime import datetime, timedelta
from config import settings
from database import SessionLocal
from models.news import News

logger = logging.getLogger(__name__)


class NewsEngine:
    def __init__(self):
        """Initialize news engine with API keys"""
        self.cryptopanic_key = settings.CRYPTOPANIC_API_KEY
        self.newsapi_key = settings.NEWSAPI_KEY
        self.coingecko_key = settings.COINGECKO_API_KEY
        self.session = requests.Session()
    
    def fetch_cryptopanic_news(self, coins: List[str] = None) -> List[Dict]:
        """
        Fetch news from CryptoPanic API
        
        Args:
            coins: List of coin symbols to filter (e.g., ['BTC', 'ETH'])
            
        Returns:
            List of news items
        """
        try:
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                'auth_token': self.cryptopanic_key,
                'public': 'true',
                'kind': 'news',
                'filter': 'hot'
            }
            
            if coins:
                params['currencies'] = ','.join(coins)
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_items = []
            
            for item in data.get('results', []):
                news_items.append({
                    'title': item.get('title', ''),
                    'source': item.get('source', {}).get('title', 'CryptoPanic'),
                    'url': item.get('url', ''),
                    'published_at': datetime.fromisoformat(item.get('published_at', '').replace('Z', '+00:00')),
                    'coins': [c['code'] for c in item.get('currencies', [])],
                    'sentiment': self._analyze_sentiment_simple(item.get('title', ''))
                })
            
            logger.info(f"Fetched {len(news_items)} news from CryptoPanic")
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching CryptoPanic news: {e}")
            return []
    
    def fetch_newsapi_news(self, query: str = "cryptocurrency") -> List[Dict]:
        """
        Fetch news from NewsAPI
        
        Args:
            query: Search query
            
        Returns:
            List of news items
        """
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': self.newsapi_key,
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 20,
                'from': (datetime.now() - timedelta(hours=24)).isoformat()
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_items = []
            
            for article in data.get('articles', []):
                news_items.append({
                    'title': article.get('title', ''),
                    'source': article.get('source', {}).get('name', 'NewsAPI'),
                    'url': article.get('url', ''),
                    'published_at': datetime.fromisoformat(article.get('publishedAt', '').replace('Z', '+00:00')),
                    'content': article.get('description', ''),
                    'coins': self._extract_coins(article.get('title', '') + ' ' + article.get('description', '')),
                    'sentiment': self._analyze_sentiment_simple(article.get('title', ''))
                })
            
            logger.info(f"Fetched {len(news_items)} news from NewsAPI")
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching NewsAPI news: {e}")
            return []
    
    def fetch_coingecko_news(self) -> List[Dict]:
        """
        Fetch trending news from CoinGecko
        
        Returns:
            List of news items
        """
        try:
            # CoinGecko doesn't have dedicated news endpoint, but we can get trending coins
            # and create "news" from trending data
            url = "https://api.coingecko.com/api/v3/search/trending"
            headers = {
                'x-cg-demo-api-key': self.coingecko_key
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_items = []
            
            # Convert trending coins to news format
            for item in data.get('coins', [])[:10]:
                coin = item.get('item', {})
                coin_id = coin.get('id', '')
                coin_symbol = coin.get('symbol', '').upper()
                coin_name = coin.get('name', '')
                market_cap_rank = coin.get('market_cap_rank', 'N/A')
                price_btc = coin.get('price_btc', 0)
                
                # Determine sentiment based on trending
                sentiment = 'bullish'  # Trending coins are generally bullish
                
                news_items.append({
                    'title': f"{coin_name} ({coin_symbol}) is Trending - Rank #{market_cap_rank}",
                    'source': 'CoinGecko Trending',
                    'url': f"https://www.coingecko.com/en/coins/{coin_id}",
                    'published_at': datetime.now(),
                    'content': f"{coin_name} is currently trending on CoinGecko. Market Cap Rank: #{market_cap_rank}. Price: {price_btc:.8f} BTC",
                    'coins': [coin_symbol],
                    'sentiment': sentiment
                })
            
            logger.info(f"Fetched {len(news_items)} trending coins from CoinGecko")
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching CoinGecko trending: {e}")
            return []
    
    def _extract_coins(self, text: str) -> List[str]:
        """
        Extract coin symbols from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of coin symbols found
        """
        # Common crypto symbols
        crypto_symbols = [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 
            'DOT', 'MATIC', 'LINK', 'UNI', 'ATOM', 'LTC', 'ETC', 'XLM',
            'ALGO', 'VET', 'ICP', 'FIL', 'TRX', 'NEAR', 'APT', 'ARB'
        ]
        
        text_upper = text.upper()
        found_coins = []
        
        for symbol in crypto_symbols:
            if symbol in text_upper:
                found_coins.append(symbol)
        
        return found_coins
    
    def _analyze_sentiment_simple(self, text: str) -> str:
        """
        Simple sentiment analysis based on keywords
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment: 'bullish', 'bearish', or 'neutral'
        """
        text_lower = text.lower()
        
        bullish_keywords = [
            'surge', 'rally', 'bullish', 'gain', 'rise', 'up', 'high', 
            'pump', 'moon', 'breakout', 'upgrade', 'partnership', 'adoption',
            'positive', 'growth', 'increase', 'soar', 'jump'
        ]
        
        bearish_keywords = [
            'crash', 'dump', 'bearish', 'fall', 'drop', 'down', 'low',
            'decline', 'plunge', 'sell-off', 'hack', 'scam', 'regulation',
            'negative', 'decrease', 'loss', 'fear', 'panic'
        ]
        
        bullish_count = sum(1 for word in bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in bearish_keywords if word in text_lower)
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'
    
    def save_news_to_db(self, news_items: List[Dict]):
        """
        Save news items to database
        
        Args:
            news_items: List of news dictionaries
        """
        db = SessionLocal()
        try:
            for item in news_items:
                # Check if news already exists (by title and source)
                existing = db.query(News).filter(
                    News.title == item['title'],
                    News.source == item['source']
                ).first()
                
                if not existing:
                    news = News(
                        title=item['title'],
                        source=item['source'],
                        sentiment=item['sentiment'],
                        coins=item.get('coins', []),
                        url=item.get('url', ''),
                        published_at=item['published_at'],
                        content=item.get('content', '')
                    )
                    db.add(news)
            
            db.commit()
            logger.info(f"Saved {len(news_items)} news items to database")
            
        except Exception as e:
            logger.error(f"Error saving news to database: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_news_for_pair(self, pair: str, hours: int = 24) -> List[Dict]:
        """
        Get relevant news for a trading pair from database
        """
        db = SessionLocal()
        try:
            # Extract base coin from pair
            base_coin = pair.split('/')[0]
            
            # Query news from last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Get news. We'll filter for the coin manually in memory to avoid SQL ARRAY type issues
            news_items = db.query(News).filter(
                News.published_at >= cutoff_time
            ).order_by(News.published_at.desc()).all()
            
            # Filter news that contains the base coin in its coins list or title
            relevant_news = []
            for n in news_items:
                if base_coin in (n.coins or []) or base_coin in n.title.upper():
                    relevant_news.append({
                        'title': n.title,
                        'source': n.source,
                        'sentiment': n.sentiment,
                        'published_at': n.published_at.isoformat(),
                        'content': n.content or ''
                    })
                    if len(relevant_news) >= 10:
                        break
            
            return relevant_news
            
        except Exception as e:
            logger.error(f"Error getting news for {pair}: {e}")
            return []
        finally:
            db.close()
    
    def fetch_and_save_all_news(self):
        """
        Fetch news from all sources and save to database
        """
        logger.info("Fetching news from all sources...")
        
        # Fetch from CoinGecko (trending coins)
        cg_news = self.fetch_coingecko_news()
        if cg_news:
            self.save_news_to_db(cg_news)
        
        # Fetch from CryptoPanic (will fail, but keep for future)
        cp_news = self.fetch_cryptopanic_news()
        if cp_news:
            self.save_news_to_db(cp_news)
        
        # Fetch from NewsAPI (optional, might be rate limited)
        try:
            na_news = self.fetch_newsapi_news("cryptocurrency OR bitcoin OR ethereum")
            if na_news:
                self.save_news_to_db(na_news)
        except Exception as e:
            logger.warning(f"NewsAPI skipped: {e}")
        
        logger.info("News fetch and save completed")


if __name__ == "__main__":
    # Test news engine
    logging.basicConfig(level=logging.INFO)
    engine = NewsEngine()
    engine.fetch_and_save_all_news()
