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
            # Use gemini-flash-latest confirmed available in list_models
            self.model_name = 'gemini-flash-latest'
            self.client = genai.GenerativeModel(self.model_name)
            self.model = self.model_name
        else:
            raise ValueError("No valid AI API key found. Set ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, or GEMINI_API_KEY")
    
    def _detect_provider(self) -> str:
        """Detect which AI provider to use based on available API keys"""
        gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
        deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        
        # Prioritize Gemini if available (fast & reliable)
        if gemini_key and gemini_key != "dummy_key" and gemini_key.strip():
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
            
            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Current price
            current_price = float(latest['close'])
            
            # Technical analysis summary
            indicators = {
                'price': current_price,
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
    
    def _is_market_interesting(self, indicators: Dict) -> tuple[bool, str]:
        """
        Pre-filter to check if market momentum is interesting enough for AI analysis.
        Returns (is_interesting, reason)
        """
        # 1. RSI Extreme (Overbought/Oversold or approaching)
        if indicators['rsi'] <= 40:
            return True, f"RSI is low ({indicators['rsi']})"
        if indicators['rsi'] >= 60:
            return True, f"RSI is high ({indicators['rsi']})"
            
        # 2. MACD Crossover
        if indicators['macd_cross'] != 'none':
            return True, f"MACD {indicators['macd_cross']} cross"
            
        # 3. Bollinger Band Pressure
        if indicators['bb_position'] != 'middle':
            return True, f"Price at {indicators['bb_position']} Bollinger Band"
            
        # 4. Strong EMA Trend
        if indicators['ema_trend'] != 'neutral':
            return True, f"Strong {indicators['ema_trend']} EMA trend"
            
        # 5. Volume Spike
        if indicators['volume'] > indicators['volume_avg'] * 1.5:
            return True, "Volume spike detected"
            
        return False, "Market is sideways/neutral (Boring)"

    def generate_signal(self, symbol: str) -> Optional[Dict]:
        """
        Generate trading signal using AI analysis
        """
        try:
            logger.info(f"Generating signal for {symbol}")
            
            # Get technical indicators
            indicators = self.calculate_technical_indicators(symbol)
            if not indicators:
                return None
            
            # PRE-FILTER: Only call AI if market is interesting
            interesting, reason = self._is_market_interesting(indicators)
            if not interesting:
                logger.info(f"Skipping AI for {symbol}: {reason}")
                return {
                    'pair': symbol,
                    'signal': 'SKIP',
                    'confidence': 0,
                    'reason': reason,
                    'skip_reason': reason,
                    'entry_price': float(indicators['price']),
                    'sl_price': 0,
                    'tp_price': 0
                }

            logger.info(f"Market interesting for {symbol}: {reason}. Calling AI...")
            
            # Get relevant news
            news = self.news_engine.get_news_for_pair(symbol, hours=24)
            
            # Prepare prompt
            prompt = self._build_analysis_prompt(symbol, indicators, news)
            
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
            
            # Parse response
            signal_data = self._parse_ai_response(content, symbol, indicators)
            
            return signal_data
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _build_analysis_prompt(self, symbol: str, indicators: Dict, news: List[Dict]) -> str:
        """
        Build analysis prompt for AI
        """
        # Format news
        news_text = "\n".join([
            f"- [{n['sentiment'].upper()}] {n['title']}"
            for n in news[:5]
        ]) if news else "None"
        
        prompt = f"""Trading analysis for {symbol}:
PRICE: ${indicators['price']}
RSI: {indicators['rsi']} ({indicators['rsi_zone']})
TREND: {indicators['ema_trend']}
MACD: {indicators['macd']} (Hist: {indicators['macd_hist']})
BB: {indicators['bb_position']}
NEWS: {news_text}

Respond ONLY with this JSON:
{{
  "signal": "LONG", "SHORT", or "SKIP",
  "confidence": 0-100,
  "news_sentiment": "bullish", "bearish", or "neutral",
  "technical_score": 0-100,
  "reason": "short explanation",
  "entry_price": {indicators['price']},
  "sl_price": SL price,
  "tp_price": TP price,
  "skip_reason": "if SKIP"
}}
Rule: Signal LONG/SHORT only if confidence >= 65.
"""
        return prompt
    
    def _parse_ai_response(self, response: str, symbol: str, indicators: Dict) -> Dict:
        """
        Parse AI response into structured signal data
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
            
            # Validate confidence threshold
            if signal['confidence'] < 65:
                signal['signal'] = 'SKIP'
                if not signal['skip_reason']:
                    signal['skip_reason'] = f"Confidence too low ({signal['confidence']}%)"
            
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
        Analyze multiple pairs and generate signals
        """
        signals = []
        
        for pair in pairs:
            try:
                signal = self.generate_signal(pair)
                if signal:
                    signals.append(signal)
                    logger.info(f"{pair}: {signal['signal']} (confidence: {signal['confidence']}%)")
            except Exception as e:
                logger.error(f"Error analyzing {pair}: {e}")
                continue
        
        return signals


if __name__ == "__main__":
    # Test AI signal engine
    logging.basicConfig(level=logging.INFO)
    
    engine = AISignalEngine()
    
    # Test with BTC
    signal = engine.generate_signal('BTC/USDT:USDT')
    if signal:
        print(json.dumps(signal, indent=2))
