# PRD — MnL Crypto Trading Bot System
**Version:** 1.0.0  
**Status:** Ready for Development  
**Author:** mifdev0  

---

## 1. Overview

MnL adalah sistem auto trading crypto berbasis AI yang menggabungkan analisis berita realtime, sinyal teknikal, dan eksekusi order otomatis di Binance Futures. Sistem ini dilengkapi dashboard web untuk monitoring posisi, saldo, PnL, dan log keputusan AI secara realtime.

**Tagline:** *"AI that trades while you sleep."*

---

## 2. Goals

- Otomasi penuh siklus trading: scan → analisis → entry → manage → exit
- Filter pair secara dinamis berdasarkan volatilitas & likuiditas
- Keputusan entry didukung oleh kombinasi news sentiment + technical analysis
- Proteksi modal via Break Even, Partial TP, dan Trailing Stop
- Dashboard monitoring realtime yang bisa diakses dari browser

---

## 3. Tech Stack

### Backend
| Layer | Teknologi |
|---|---|
| Runtime | Python 3.11+ |
| Exchange | `ccxt` (unified Binance Futures API) |
| AI Analysis | Gemini, DeepSeek, or Anthropic (Claude) |
| News Feed | CryptoPanic API + NewsAPI.org |
| Technical Indicators | `pandas-ta` |
| Scheduler | `APScheduler` |
| Database | PostgreSQL (via `SQLAlchemy`) |
| API Server | FastAPI |
| Realtime | WebSocket (FastAPI native) |
| Notification | Telegram Bot API |

### Frontend (Dashboard)
| Layer | Teknologi |
|---|---|
| Framework | React + Vite |
| Styling | Tailwind CSS |
| Charts | TradingView Lightweight Charts |
| State | Zustand |
| HTTP Client | Axios |
| Realtime | WebSocket native |

### Infrastructure
| Layer | Teknologi |
|---|---|
| VPS | Ubuntu 22.04 (min 1 CPU, 2GB RAM) |
| Process Manager | PM2 atau Supervisor |
| Reverse Proxy | Nginx |
| Environment | `.env` file (via `python-dotenv`) |

---

## 4. Environment Variables (.env)

Semua kredensial dikonfigurasi di satu file `.env` di root project. Developer tidak perlu menyentuh kode untuk mengkonfigurasi sistem.

```env
# ─── Binance ───────────────────────────────
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
BINANCE_TESTNET=true         # true = testnet | false = live

# ─── AI Providers ──────────────────────────
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=

# ─── News APIs ─────────────────────────────
CRYPTOPANIC_API_KEY=
NEWSAPI_KEY=

# ─── Telegram ──────────────────────────────
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=              # hanya chat ID ini yang bisa akses bot

# ─── Database ──────────────────────────────
DATABASE_URL=postgresql://user:pass@localhost:5432/mnl

# ─── Trading Config ────────────────────────
RISK_PER_TRADE=1.0           # % dari balance per trade
MAX_OPEN_POSITIONS=5         # maksimal posisi aktif
MIN_VOLUME_24H=50000000      # minimum volume 24h (USD)
MIN_VOLATILITY=2.0           # minimum volatilitas % dalam 24h
LEVERAGE=10                  # default leverage

# ─── Risk Management ───────────────────────
BE_TRIGGER_R=1.0             # aktifkan BE setelah +1R
PARTIAL_TP_R=2.0             # partial close 50% di +2R
TRAILING_ACTIVATION_R=2.0   # aktifkan trailing setelah +2R
TRAILING_DISTANCE_R=1.0      # jarak trailing stop (dalam R)
BE_BUFFER_PCT=0.1            # buffer BE dari entry (%)

# ─── Dashboard ─────────────────────────────
DASHBOARD_PORT=3000
API_PORT=8000
```

---

## 5. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                      MnL System                         │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │  News Engine │    │ Market Scanner│                  │
│  │  (CryptoPanic│    │ (ccxt - filter│                  │
│  │   NewsAPI)   │    │  volume+volatl│                  │
│  └──────┬───────┘    └──────┬────────┘                  │
│         │                  │                            │
│         └────────┬─────────┘                            │
│                  ▼                                      │
│         ┌────────────────┐                              │
│         │  AI Signal     │                              │
│         │  Engine        │                              │
│         │  (Claude API)  │                              │
│         │  news+technical│                              │
│         └───────┬────────┘                              │
│                 │                                       │
│                 ▼                                       │
│        ┌─────────────────┐                              │
│        │ Decision Engine  │                              │
│        │ entry/skip/side  │                              │
│        └───────┬──────────┘                              │
│                │                                        │
│                ▼                                        │
│       ┌──────────────────┐                              │
│       │  Order Executor  │                              │
│       │  (Binance Futures│                              │
│       │   via ccxt)      │                              │
│       └───────┬──────────┘                              │
│               │                                         │
│               ▼                                         │
│      ┌─────────────────────┐                            │
│      │  Position Manager   │                            │
│      │  BE + Partial TP    │                            │
│      │  + Trailing Stop    │                            │
│      └───────┬─────────────┘                            │
│              │                                          │
│              ▼                                          │
│     ┌──────────────────────┐                            │
│     │  PostgreSQL + FastAPI│◄──── React Dashboard       │
│     │  (logging + WS feed) │                            │
│     └──────────────────────┘                            │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Modules & Features

### 6.1 Market Scanner
- Fetch semua pair dari Binance Futures via ccxt
- Filter berdasarkan:
  - Volume 24h > `MIN_VOLUME_24H` (configurable di .env)
  - Volatilitas > `MIN_VOLATILITY` dalam 24h
  - Exclude stablecoin pairs (USDC/USDT, BUSD/USDT, dll)
- Output: list pair kandidat yang akan dianalisis
- Jadwal: setiap 15 menit

### 6.2 News Engine
- Fetch berita terbaru dari CryptoPanic + NewsAPI
- Filter berita relevan berdasarkan keyword pair kandidat
- Deduplikasi berita yang sudah diproses
- Output: list berita terstruktur per coin dengan timestamp
- Jadwal: setiap 5 menit

### 6.3 AI Signal Engine
- Input: data teknikal (RSI, EMA 20/50/200, MACD, BB, volume) + berita relevan
- Proses via Claude API dengan structured prompt
- Output JSON per pair:
```json
{
  "pair": "SOLUSDT",
  "signal": "LONG",
  "confidence": 82,
  "news_sentiment": "bullish",
  "technical_score": 75,
  "reason": "RSI oversold di 28, EMA 20 cross EMA 50, berita upgrade jaringan Solana",
  "entry_price": 142.50,
  "sl_price": 138.00,
  "tp_price": 151.50,
  "skip_reason": null
}
```
- Jika confidence < 70, posisi diskip otomatis
- Jadwal: triggered setelah Market Scanner selesai

### 6.4 Order Executor
- Validasi jumlah posisi aktif < `MAX_OPEN_POSITIONS`
- Set leverage sesuai config
- Place market order + SL + TP sekaligus (bracket order)
- Simpan detail posisi ke database
- Kirim notifikasi Telegram saat order masuk

### 6.5 Position Manager
- Monitor semua posisi aktif setiap 30 detik via WebSocket Binance
- Implementasi logika:
  ```
  Jika unrealized PnL >= +1R → pindah SL ke entry + buffer 0.1%
  Jika unrealized PnL >= +2R → close 50% posisi (partial TP)
  Jika unrealized PnL >= +2R → aktifkan trailing stop
  Trailing stop: update SL setiap harga baru tertinggi/terendah
  ```
- Update status posisi di database realtime
- Kirim notifikasi Telegram setiap perubahan status (BE aktif, partial TP, close)

### 6.6 FastAPI Backend
**Endpoints:**

| Method | Path | Deskripsi |
|---|---|---|
| GET | `/api/balance` | Saldo exchange |
| GET | `/api/positions` | Semua posisi aktif |
| GET | `/api/trades` | History semua trade |
| GET | `/api/performance` | PnL harian/mingguan/bulanan |
| GET | `/api/news` | Berita terbaru yang diproses |
| GET | `/api/signals` | Log sinyal AI |
| POST | `/api/bot/pause` | Pause bot |
| POST | `/api/bot/resume` | Resume bot |
| WS | `/ws/live` | Realtime feed posisi + berita |

### 6.7 React Dashboard
**Halaman utama berisi:**
- Metric cards: Total Balance, Unrealized PnL, Win Rate, Open Positions
- Tabel posisi aktif dengan kolom: Pair, Side, Entry, Current, PnL, Status (BE/Active/Trailing), AI Reason
- Feed berita realtime dengan label Bullish/Bearish/Neutral
- Grafik equity curve (Chart.js/TradingView)
- Trade history table dengan filter
- Bot status indicator + tombol Pause/Resume

### 6.8 Telegram Bot (Interactive + Notifications)

Bot Telegram berfungsi dua arah — notifikasi otomatis **dan** kontrol/monitoring penuh layaknya dashboard via chat.

#### Auto Notifications (Push)
- ✅ Order masuk (pair, side, entry, SL, TP, reason AI)
- 🔒 Break Even aktif
- 💰 Partial TP tereksekusi
- 🎯 Posisi closed (profit/loss + summary)
- ⚠️ Error sistem
- 🚨 Emergency: balance drop >20%, koneksi putus, bot pause

#### Interactive Commands (Pull)
User kirim command ke bot, bot balas dengan data realtime:

| Command | Respons |
|---|---|
| `/start` | Welcome message + daftar semua command |
| `/balance` | Saldo total, available margin, used margin |
| `/positions` | Semua posisi aktif: pair, side, entry, PnL, status (BE/Trailing) |
| `/pnl` | PnL hari ini, minggu ini, bulan ini, all-time |
| `/news` | 5 berita crypto terbaru + label sentiment |
| `/signals` | 5 sinyal AI terakhir + confidence score |
| `/history` | 10 trade terakhir yang sudah closed |
| `/stats` | Win rate, average RR, total trade, best/worst trade |
| `/status` | Status bot (active/paused), jumlah posisi, uptime |
| `/pause` | Pause bot (tidak buka posisi baru) |
| `/resume` | Resume bot |
| `/closeall` | Emergency close semua posisi aktif (konfirmasi dulu) |
| `/help` | Daftar semua command |

#### Inline Keyboard
Beberapa command dilengkapi tombol interaktif:
- `/positions` → tiap posisi ada tombol **[Close]** untuk manual close
- `/pause` → ada tombol konfirmasi **[Yes, Pause] [Cancel]**
- `/closeall` → wajib konfirmasi **[CONFIRM CLOSE ALL] [Cancel]**

#### Security
- Bot hanya merespons `TELEGRAM_CHAT_ID` yang terdaftar di `.env`
- Command destructive (`/closeall`, `/pause`) butuh konfirmasi inline keyboard
- Semua aksi via Telegram dicatat di database sebagai audit trail

#### Library
```
python-telegram-bot==20.x    # async, support inline keyboard
```

---

## 7. Database Schema

```sql
-- Posisi trading
CREATE TABLE positions (
  id            SERIAL PRIMARY KEY,
  pair          VARCHAR(20),
  side          VARCHAR(5),        -- LONG / SHORT
  entry_price   DECIMAL(18,8),
  sl_price      DECIMAL(18,8),
  tp_price      DECIMAL(18,8),
  quantity      DECIMAL(18,8),
  leverage      INTEGER,
  status        VARCHAR(20),       -- OPEN / BE / TRAILING / CLOSED
  ai_reason     TEXT,
  news_used     TEXT,
  confidence    INTEGER,
  pnl           DECIMAL(18,8),
  opened_at     TIMESTAMP,
  closed_at     TIMESTAMP
);

-- Log sinyal AI
CREATE TABLE signals (
  id            SERIAL PRIMARY KEY,
  pair          VARCHAR(20),
  signal        VARCHAR(5),
  confidence    INTEGER,
  reason        TEXT,
  executed      BOOLEAN,
  skip_reason   TEXT,
  created_at    TIMESTAMP
);

-- Berita yang diproses
CREATE TABLE news (
  id            SERIAL PRIMARY KEY,
  title         TEXT,
  source        VARCHAR(50),
  sentiment     VARCHAR(10),       -- bullish / bearish / neutral
  coins         TEXT[],
  published_at  TIMESTAMP,
  fetched_at    TIMESTAMP
);
```

---

## 8. Folder Structure

```
mnl/
├── .env                        # ← isi ini saja
├── .env.example                # template env
├── requirements.txt
├── README.md
│
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # load .env
│   ├── database.py             # SQLAlchemy setup
│   │
│   ├── modules/
│   │   ├── scanner.py          # Market Scanner
│   │   ├── news_engine.py      # News fetching
│   │   ├── ai_signal.py        # Claude AI analysis
│   │   ├── order_executor.py   # Binance order execution
│   │   ├── position_manager.py # BE + trailing logic
│   │   └── telegram.py         # Telegram interactive bot + notifications
│   │
│   ├── models/
│   │   ├── position.py
│   │   ├── signal.py
│   │   └── news.py
│   │
│   ├── routers/
│   │   ├── balance.py
│   │   ├── positions.py
│   │   ├── trades.py
│   │   ├── performance.py
│   │   └── bot_control.py
│   │
│   └── scheduler.py            # APScheduler jobs
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       │   ├── MetricCards.jsx
│       │   ├── PositionsTable.jsx
│       │   ├── NewsFeed.jsx
│       │   ├── EquityChart.jsx
│       │   ├── TradeHistory.jsx
│       │   └── BotStatus.jsx
│       ├── store/
│       │   └── useStore.js     # Zustand
│       └── hooks/
│           └── useWebSocket.js
│
└── docker-compose.yml          # optional: untuk deployment mudah
```

---

## 9. Development Phases

### Phase 1 — Core Backend (Week 1-2)
- [ ] Setup project structure + database
- [ ] Market Scanner module
- [ ] News Engine module
- [ ] AI Signal Engine (Claude integration)
- [ ] Order Executor (Binance Testnet)
- [ ] Basic Telegram notifications

### Phase 2 — Risk Management (Week 3)
- [ ] Position Manager (BE logic)
- [ ] Partial TP implementation
- [ ] Trailing Stop implementation
- [ ] Full end-to-end test di Testnet

### Phase 3 — Dashboard (Week 4)
- [ ] FastAPI endpoints + WebSocket
- [ ] React dashboard semua komponen
- [ ] Realtime feed integration
- [ ] Performance chart

### Phase 4 — Hardening (Week 5-6)
- [ ] Error handling & retry logic
- [ ] Rate limit handling (API throttling)
- [ ] Logging system lengkap
- [ ] VPS deployment + Nginx setup
- [ ] Paper trading 2-4 minggu

### Phase 5 — Live (After paper trading profitable)
- [ ] Switch `BINANCE_TESTNET=false` di .env
- [ ] Start dengan modal kecil ($50-100)
- [ ] Monitor intensif minggu pertama

---

## 10. Risk Management Rules (Hardcoded)

Aturan ini **tidak bisa dioverride** oleh AI — selalu dijalankan di level kode:

1. Max posisi aktif = `MAX_OPEN_POSITIONS` (default 5)
2. Risk per trade = `RISK_PER_TRADE`% dari balance (default 1%)
3. SL wajib dipasang bersamaan dengan entry order
4. Jika koneksi internet putus > 60 detik → semua posisi di-close otomatis (emergency close)
5. Jika balance turun > 20% dari balance awal hari ini → bot pause otomatis + notif Telegram
6. Leverage maksimal dikunci di .env, AI tidak bisa override

---

## 11. Notes untuk AI Agent

- Semua secrets dan config ada di `.env` — jangan hardcode apapun di kode
- Gunakan `python-dotenv` untuk load `.env`
- Setiap module harus punya error handling dengan logging yang jelas
- Test setiap module secara independent sebelum integrate
- Binance Testnet URL: `https://testnet.binancefuture.com`
- Claude model yang digunakan: `claude-sonnet-4-20250514`
- Semua keputusan AI harus disimpan ke tabel `signals` untuk audit trail
- Frontend dan backend komunikasi via REST + WebSocket (bukan SSE)
- Jangan install library yang tidak ada di `requirements.txt`
