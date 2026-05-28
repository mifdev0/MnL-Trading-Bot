"""
AI Signal Engine - Generate trading signals using AI (Claude or DeepSeek)
"""
import logging
import json
import re
import pandas as pd
from typing import Dict, List, Optional
from config import settings
from modules.scanner import MarketScanner
from modules.news_engine import NewsEngine

logger = logging.getLogger(__name__)


def calculate_rsi(series, period=14):
    """Calculate RSI manually"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_ema(series, period):
    """Calculate EMA manually"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_macd(series, fast=12, slow=26, signal=9):
    """Calculate MACD manually"""
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd = ema_fast - ema_slow
    macd_signal = calculate_ema(macd, signal)
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist


def calculate_bollinger_bands(series, period=20, std=2):
    """Calculate Bollinger Bands manually"""
    sma = series.rolling(window=period).mean()
    std_dev = series.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper, sma, lower


class AISignalEngine:
    def __init__(self):
        """Initialize AI Signal Engine with Claude, DeepSeek, or Gemini API"""
        self.scanner = MarketScanner()
        self.news_engine = NewsEngine()
        
        # Detect which AI provider to use
        self.provider = self._detect_provider()
        
        if self.provider == "claude":
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = "claude-sonnet-4-20250514"
        elif self.provider == "deepseek":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
            self.model = "deepseek-chat"
        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use gemini-flash-latest confirmed available
            self.model_name = 'gemini-flash-latest'
            self.client = genai.GenerativeModel(self.model_name)
            self.model = self.model_name
        elif self.provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            # Use Llama 4 Scout for top-tier analysis
            self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
        else:
            raise ValueError("No valid AI API key found. Set ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, GEMINI_API_KEY or GROQ_API_KEY")
    
    def _detect_provider(self) -> str:
        """Detect which AI provider to use based on available API keys"""
        groq_key = getattr(settings, 'GROQ_API_KEY', None)
        gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
        deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        
        # Prioritize Groq (Super fast and reliable)
        if groq_key and groq_key != "dummy_key" and groq_key.strip():
            logger.info("Using Groq AI (Llama 3.1)")
            return "groq"
        # Prioritize Gemini if available (fast & reliable)
        elif gemini_key and gemini_key != "dummy_key" and gemini_key.strip():
            logger.info("Using Gemini AI")
            return "gemini"
        # Prioritize DeepSeek if available (cheaper)
        elif deepseek_key and deepseek_key != "dummy_key" and deepseek_key.strip():
            logger.info("Using DeepSeek AI")
            return "deepseek"
        elif anthropic_key and anthropic_key != "dummy_key" and anthropic_key.strip():
            logger.info("Using Claude AI")
            return "claude"
        else:
            return None
    
    def calculate_technical_indicators(self, symbol: str) -> Optional[Dict]:
        """
        Calculate technical indicators for a symbol
        """
        try:
            # Fetch OHLCV data for shorter timeframe (15m)
            ohlcv = self.scanner.get_ohlcv(symbol, timeframe='15m', limit=200)
            
            if not ohlcv or len(ohlcv) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculate indicators using custom functions
            df['rsi'] = calculate_rsi(df['close'], period=14)
            df['ema_20'] = calculate_ema(df['close'], period=20)
            df['ema_50'] = calculate_ema(df['close'], period=50)
            df['ema_200'] = calculate_ema(df['close'], period=200)
            
            # MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = calculate_macd(df['close'])
            
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = calculate_bollinger_bands(df['close'], period=20)
            df['bb_width'] = df['bb_upper'] - df['bb_lower']
            df['bb_width_avg'] = df['bb_width'].rolling(window=20).mean()
            
            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Current price
            current_price = float(latest['close'])
            
            # Technical analysis summary
            indicators = {
                'price': current_price,
                'open': float(latest['open']),
                'rsi': round(float(latest['rsi']), 2),
                'ema_20': round(float(latest['ema_20']), 2),
                'ema_50': round(float(latest['ema_50']), 2),
                'ema_200': round(float(latest['ema_200']), 2),
                'macd': round(float(latest['macd']), 4),
                'macd_signal': round(float(latest['macd_signal']), 4),
                'macd_hist': round(float(latest['macd_hist']), 4),
                'bb_upper': round(float(latest['bb_upper']), 2),
                'bb_middle': round(float(latest['bb_middle']), 2),
                'bb_lower': round(float(latest['bb_lower']), 2),
                'bb_width': round(float(latest['bb_width']), 4),
                'bb_width_avg': round(float(latest['bb_width_avg']), 4),
                'volume': float(latest['volume']),
                'volume_avg': float(df['volume'].tail(20).mean()),
                
                # Trend signals
                'ema_trend': 'bullish' if latest['ema_20'] > latest['ema_50'] > latest['ema_200'] else 
                            'bearish' if latest['ema_20'] < latest['ema_50'] < latest['ema_200'] else 'neutral',
                'macd_cross': 'bullish' if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal'] else
                             'bearish' if latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal'] else 'none',
                'rsi_zone': 'oversold' if latest['rsi'] < 30 else 'overbought' if latest['rsi'] > 70 else 'neutral',
                'bb_position': 'upper' if current_price > latest['bb_upper'] else 
                              'lower' if current_price < latest['bb_lower'] else 'middle'
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            return None
    
    def get_htf_trend(self, symbol: str) -> str:
        """Fetch 1H data and return EMA trend (bullish/bearish/neutral)"""
        try:
            ohlcv = self.scanner.get_ohlcv(symbol, timeframe='1h', limit=100)
            if not ohlcv or len(ohlcv) < 50:
                return "neutral"
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            ema_20 = calculate_ema(df['close'], 20).iloc[-1]
            ema_50 = calculate_ema(df['close'], 50).iloc[-1]
            if ema_20 > ema_50: return "bullish"
            if ema_20 < ema_50: return "bearish"
            return "neutral"
        except Exception as e:
            logger.error(f"Error getting HTF trend for {symbol}: {e}")
            return "neutral"

    def get_combined_sentiment(self, symbol: str) -> str:
        """Combine 4h and 24h sentiment with 70/30 weight"""
        try:
            news_4h = self.news_engine.get_news_for_pair(symbol, hours=4)
            news_24h = self.news_engine.get_news_for_pair(symbol, hours=24)
            
            def get_score(news_list):
                if not news_list: return 0
                scores = []
                for n in news_list:
                    s = n.get('sentiment', 'neutral').lower()
                    if s == 'bullish': scores.append(1)
                    elif s == 'bearish': scores.append(-1)
                    else: scores.append(0)
                return sum(scores) / len(scores)
            
            score_4h = get_score(news_4h)
            score_24h = get_score(news_24h)
            
            combined_score = (score_4h * 0.7) + (score_24h * 0.3)
            
            if combined_score > 0.1: return "bullish"
            if combined_score < -0.1: return "bearish"
            return "neutral"
        except Exception as e:
            logger.error(f"Error getting combined sentiment for {symbol}: {e}")
            return "neutral"

    def _is_market_interesting(self, indicators: Dict) -> tuple[bool, str, str]:
        """
        Pre-filter to check if market momentum is interesting enough for AI analysis.
        Requires confluence (multiple indicators) to reduce API calls.
        """
        rsi = indicators['rsi']
        macd_cross = indicators['macd_cross']
        bb_pos = indicators['bb_position']
        ema_trend = indicators['ema_trend']
        vol_spike = indicators['volume'] > indicators['volume_avg'] * 1.5
        
        # 1. Trend Following Confluence (Trend + BB/Volume Pullback)
        if ema_trend == 'bullish':
            if bb_pos == 'lower' or vol_spike:
                return True, f"Bullish Trend + {'BB Pullback' if bb_pos == 'lower' else 'Vol Spike'}", "LONG"
        if ema_trend == 'bearish':
            if bb_pos == 'upper' or vol_spike:
                return True, f"Bearish Trend + {'BB Pullback' if bb_pos == 'upper' else 'Vol Spike'}", "SHORT"
                
        # 2. Reversal Confluence (RSI Extreme + MACD Cross)
        if rsi <= 30 and macd_cross == 'bullish':
            return True, "Oversold RSI (<=30) + MACD Bullish Cross", "LONG"
        if rsi >= 70 and macd_cross == 'bearish':
            return True, "Overbought RSI (>=70) + MACD Bearish Cross", "SHORT"
            
        # 3. BB Extreme + MACD Cross
        if bb_pos == 'lower' and macd_cross == 'bullish':
            return True, "BB Lower + MACD Bullish Cross", "LONG"
        if bb_pos == 'upper' and macd_cross == 'bearish':
            return True, "BB Upper + MACD Bearish Cross", "SHORT"
            
        # 4. Vol Spike + MACD Cross
        if vol_spike and macd_cross != 'none':
            direction = "LONG" if macd_cross == 'bullish' else "SHORT"
            return True, f"Volume Spike + MACD {direction} Cross", direction

        return False, "No technical confluence found (Boring)", "NONE"

    def generate_signal(self, symbol: str) -> Optional[Dict]:
        """
        Generate trading signal using AI analysis with HTF filter and dynamic sentiment
        """
        try:
            logger.info(f"Generating signal for {symbol}")
            
            # Get technical indicators
            indicators = self.calculate_technical_indicators(symbol)
            if not indicators:
                return None
            
            # PRE-FILTER: Only call AI if market is interesting
            interesting, reason, potential_dir = self._is_market_interesting(indicators)
            if not interesting:
                logger.info(f"Skipping AI for {symbol}: {reason}")
                return {
                    'pair': symbol, 'signal': 'SKIP', 'confidence': 0, 'reason': reason,
                    'skip_reason': reason, 'entry_price': float(indicators['price']), 'sl_price': 0, 'tp_price': 0
                }

            # HTF Filter: Check 1H trend before calling AI
            htf_trend = self.get_htf_trend(symbol)
            if (potential_dir == "LONG" and htf_trend == "bearish") or \
               (potential_dir == "SHORT" and htf_trend == "bullish"):
                skip_msg = f"HTF Trend Filter: Candidate {potential_dir} blocked by 1H {htf_trend} trend"
                logger.info(f"Skipping AI for {symbol}: {skip_msg}")
                return {
                    'pair': symbol, 'signal': 'SKIP', 'confidence': 0, 'reason': skip_msg,
                    'skip_reason': skip_msg, 'entry_price': float(indicators['price']), 'sl_price': 0, 'tp_price': 0
                }

            logger.info(f"Market interesting for {symbol} ({potential_dir}). HTF: {htf_trend}. Calling AI...")
            
            # Get news for the pair to provide context to AI
            recent_news = self.news_engine.get_news_for_pair(symbol, hours=24)
            news_headlines = [f"- {n['title']} ({n['sentiment']})" for n in recent_news[:5]]
            news_context = "\n".join(news_headlines) if news_headlines else "No recent specific news found."
            
            # Get combined news sentiment (4h weight 70%, 24h weight 30%)
            combined_sentiment = self.get_combined_sentiment(symbol)
            
            # Prepare prompt with HTF, Combined Sentiment, and Headlines context
            prompt = self._build_analysis_prompt(symbol, indicators, combined_sentiment, htf_trend, news_context)
            
            # Call AI API based on provider
            if self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                content = response.content[0].text
            elif self.provider == "deepseek":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.3
                )
                content = response.choices[0].message.content
            elif self.provider == "gemini":
                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 2000,
                    }
                )
                content = response.text
            elif self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
            
            # Parse response
            signal_data = self._parse_ai_response(content, symbol, indicators)
            
            return signal_data
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate_limit" in error_msg.lower():
                logger.warning(f"Rate limit hit for {symbol}: {error_msg}. Skipping AI analysis.")
                return {
                    'pair': symbol, 'signal': 'SKIP', 'confidence': 0, 
                    'reason': 'API Rate Limit Reached', 'skip_reason': 'Rate limit (429)',
                    'entry_price': float(indicators['price']), 'sl_price': 0, 'tp_price': 0
                }
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _build_analysis_prompt(self, symbol: str, indicators: Dict, sentiment: str, htf_trend: str, news_context: str) -> str:
        """
        Build analysis prompt for AI including HTF, Combined Sentiment and News Headlines
        """
        prompt = f"""Trading analysis for {symbol}:
PRICE: ${indicators['price']}
RSI: {indicators['rsi']} ({indicators['rsi_zone']})
TREND (15m): {indicators['ema_trend']}
TREND (1H HTF): {htf_trend}
MACD: {indicators['macd']} (Hist: {indicators['macd_hist']})
BB: {indicators['bb_position']} (Width: {indicators['bb_width']})
OVERALL SENTIMENT: {sentiment}

RECENT NEWS HEADLINES:
{news_context}

Respond ONLY with this JSON:
{{
  "signal": "LONG", "SHORT", or "SKIP",
  "confidence": 0-100,
  "news_sentiment": "{sentiment}",
  "technical_score": 0-100,
  "reason": "short explanation based on technicals and news headlines context",
  "entry_price": {indicators['price']},
  "sl_price": SL price,
  "tp_price": TP price,
  "skip_reason": "if SKIP"
}}
Rule: Signal LONG/SHORT only if confidence >= 70.
"""
        return prompt
    
    def _parse_ai_response(self, response: str, symbol: str, indicators: Dict) -> Dict:
        """
        Parse AI response into structured signal data with DYNAMIC CONFIDENCE THRESHOLD
        """
        try:
            # Deeply clean and extract JSON
            content = response.strip()
            
            # Find the first { and last }
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1:
                raise ValueError("No JSON object found in AI response")
                
            # If no ending brace found (truncated response), try to fix it
            if end_idx == 0:
                logger.warning("AI response truncated, attempting to fix JSON")
                json_str = content[start_idx:]
                # Add enough closing braces to potentially make it valid
                # This is a bit hacky but helps with truncated AI outputs
                for _ in range(5):
                    try:
                        data = json.loads(json_str)
                        break
                    except json.JSONDecodeError:
                        json_str += "}"
                else:
                    raise ValueError("Could not fix truncated JSON")
            else:
                json_str = content[start_idx:end_idx]
            
            # Try to parse
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # Try harder - fix common trailing commas or minor syntax issues
                json_str = re.sub(r',\s*\}', '}', json_str)
                json_str = re.sub(r',\s*\]', ']', json_str)
                data = json.loads(json_str)
            
            # Reference price
            price = float(indicators['price'])
            
            # Robust mapping with safe defaults
            # Ensure signal is upper case string
            raw_signal = str(data.get('signal', 'SKIP')).upper()
            if raw_signal not in ['LONG', 'SHORT', 'SKIP']:
                raw_signal = 'SKIP'
                
            # Helper to safely get float
            def get_safe_float(key, default):
                val = data.get(key)
                if val is None: return default
                try: return float(val)
                except (ValueError, TypeError): return default

            entry_price = get_safe_float('entry_price', price)
            sl_price = get_safe_float('sl_price', 0)
            tp_price = get_safe_float('tp_price', 0)
            
            # If SL or TP are missing but signal is LONG/SHORT, calculate them
            if raw_signal == 'LONG':
                if sl_price == 0: sl_price = entry_price * 0.985 # 1.5% SL
                if tp_price == 0: tp_price = entry_price * 1.03 # 3% TP
            elif raw_signal == 'SHORT':
                if sl_price == 0: sl_price = entry_price * 1.015 # 1.5% SL
                if tp_price == 0: tp_price = entry_price * 0.97 # 3% TP

            signal = {
                'pair': symbol,
                'signal': raw_signal,
                'confidence': int(get_safe_float('confidence', 0)),
                'news_sentiment': data.get('news_sentiment', 'neutral'),
                'technical_score': int(get_safe_float('technical_score', 0)),
                'reason': data.get('reason', 'AI analysis'),
                'entry_price': entry_price,
                'sl_price': sl_price,
                'tp_price': tp_price,
                'skip_reason': data.get('skip_reason'),
                'current_price': price
            }
            
            # DYNAMIC CONFIDENCE THRESHOLD
            threshold = 70
            
            # 1. BB Width Spike (Volatility check)
            if indicators.get('bb_width', 0) > 2 * indicators.get('bb_width_avg', 0):
                threshold = 75
                
            # 2. Opposite News Sentiment check
            news_sent = str(signal['news_sentiment']).lower()
            if (signal['signal'] == 'LONG' and news_sent == 'bearish') or \
               (signal['signal'] == 'SHORT' and news_sent == 'bullish'):
                threshold = 80
                
            # Validate confidence threshold
            if signal['confidence'] < threshold:
                orig_signal = signal['signal']
                signal['signal'] = 'SKIP'
                if not signal['skip_reason'] or signal['skip_reason'] == "if SKIP":
                    signal['skip_reason'] = f"Confidence {signal['confidence']}% below dynamic threshold {threshold}% (Signal was {orig_signal})"
            
            return signal
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}. Raw: {response[:100]}...")
            return {
                'pair': symbol,
                'signal': 'SKIP',
                'confidence': 0,
                'reason': 'Failed to parse AI response',
                'skip_reason': f'Parse error: {str(e)}',
                'entry_price': float(indicators['price']),
                'sl_price': 0,
                'tp_price': 0
            }
    
    def analyze_multiple_pairs(self, pairs: List[str]) -> List[Dict]:
        """
        Analyze multiple pairs and generate signals in parallel
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        signals = []
        max_workers = min(len(pairs), 5) # Limit concurrent calls to 5
        
        logger.info(f"Analyzing {len(pairs)} pairs in parallel (max_workers={max_workers})...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_pair = {executor.submit(self.generate_signal, pair): pair for pair in pairs}
            
            for future in as_completed(future_to_pair):
                pair = future_to_pair[future]
                try:
                    signal = future.result()
                    if signal:
                        signals.append(signal)
                        logger.info(f"{pair}: {signal['signal']} (confidence: {signal['confidence']}%)")
                except Exception as e:
                    logger.error(f"Error analyzing {pair}: {e}")
                    continue
        
        time.sleep(0.5)
        return signals


if __name__ == "__main__":
    # Test AI signal engine
    logging.basicConfig(level=logging.INFO)
    
    engine = AISignalEngine()
    
    # Test with BTC
    signal = engine.generate_signal('BTC/USDT:USDT')
    if signal:
        print(json.dumps(signal, indent=2))
