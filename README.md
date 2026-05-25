# MnL — AI Crypto Trading Bot System

<div align="center">

![MnL Logo](https://img.shields.io/badge/MnL-Trading%20Bot-FCD535?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Tagline:** *"AI that trades while you sleep."*

MnL adalah sistem auto trading crypto berbasis AI yang menggabungkan analisis berita realtime, sinyal teknikal, dan eksekusi order otomatis di Binance Futures. Sistem ini dilengkapi dashboard web untuk monitoring posisi, saldo, PnL, dan log keputusan AI secara realtime.

[Quick Start](#quick-start) • [Features](#features) • [Documentation](#documentation) • [Demo](#demo)

</div>

---

## 🎯 Features

- ✅ **Otomasi Penuh**: Scan → Analisis → Entry → Manage → Exit
- 📊 **Smart Filtering**: Filter pair dinamis berdasarkan volatilitas & likuiditas
- 🤖 **AI-Powered**: Keputusan entry didukung Claude AI + news sentiment + technical analysis
- 🛡️ **Risk Management**: Break Even, Partial TP, dan Trailing Stop otomatis
- 📱 **Real-time Dashboard**: Monitor posisi, PnL, dan performa secara realtime
- 💬 **Telegram Bot**: Kontrol dan monitoring via Telegram
- 📈 **Technical Analysis**: RSI, EMA, MACD, Bollinger Bands
- 📰 **News Integration**: CryptoPanic + NewsAPI untuk sentiment analysis
- 🔒 **Security First**: API key encryption, IP whitelist support
- 🐳 **Docker Ready**: Deploy dengan satu command

## Tech Stack

### Backend
- Python 3.11+
- ccxt (Binance Futures API)
- Anthropic API (Claude Sonnet 4)
- CryptoPanic API + NewsAPI.org
- pandas-ta (Technical Indicators)
- APScheduler
- PostgreSQL + SQLAlchemy
- FastAPI + WebSocket
- Telegram Bot API

### Frontend
- React + Vite
- Tailwind CSS
- TradingView Lightweight Charts
- Zustand
- Axios
- WebSocket

## Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone <repo-url>
cd mnl

# Copy environment template
cp .env.example .env

# Edit .env dengan kredensial Anda
nano .env
```

### 2. Setup Database

```bash
# Install PostgreSQL (Ubuntu)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE mnl;
CREATE USER mnluser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mnl TO mnluser;
\q

# Update DATABASE_URL di .env
DATABASE_URL=postgresql://mnluser:your_password@localhost:5432/mnl
```

### 3. Install Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### 4. Run Database Migration

```bash
cd backend
alembic upgrade head
cd ..
```

### 5. Start Backend

```bash
cd backend
python main.py
```

### 6. Start Frontend (terminal baru)

```bash
cd frontend
npm run dev
```

### 7. Access Dashboard

Buka browser: `http://localhost:3000`

## Configuration

Semua konfigurasi ada di file `.env`. Tidak perlu edit kode.

### Binance Setup

1. Buat API Key di [Binance Testnet](https://testnet.binancefuture.com)
2. Copy API Key & Secret ke `.env`
3. Set `BINANCE_TESTNET=true` untuk testing

### Anthropic Setup

1. Daftar di [Anthropic Console](https://console.anthropic.com)
2. Buat API Key
3. Copy ke `ANTHROPIC_API_KEY` di `.env`

### News APIs Setup

1. **CryptoPanic**: Daftar di [cryptopanic.com/developers/api](https://cryptopanic.com/developers/api/)
2. **NewsAPI**: Daftar di [newsapi.org](https://newsapi.org)
3. Copy API keys ke `.env`

### Telegram Bot Setup

1. Chat dengan [@BotFather](https://t.me/botfather)
2. Kirim `/newbot` dan ikuti instruksi
3. Copy token ke `TELEGRAM_BOT_TOKEN`
4. Dapatkan chat ID Anda dengan chat ke [@userinfobot](https://t.me/userinfobot)
5. Copy chat ID ke `TELEGRAM_CHAT_ID`

## Trading Configuration

Edit di `.env`:

```env
RISK_PER_TRADE=1.0           # Risk 1% per trade
MAX_OPEN_POSITIONS=5         # Max 5 posisi bersamaan
MIN_VOLUME_24H=50000000      # Min $50M volume
MIN_VOLATILITY=2.0           # Min 2% volatilitas
LEVERAGE=10                  # 10x leverage
```

## Risk Management

Sistem menggunakan risk management otomatis:

- **Break Even**: SL pindah ke entry setelah profit +1R
- **Partial TP**: Close 50% posisi di +2R
- **Trailing Stop**: Aktif setelah +2R, jarak 1R dari peak

## Telegram Commands

| Command | Deskripsi |
|---------|-----------|
| `/start` | Welcome message + daftar command |
| `/balance` | Cek saldo & margin |
| `/positions` | Lihat posisi aktif |
| `/pnl` | Lihat profit/loss |
| `/news` | Berita crypto terbaru |
| `/signals` | Sinyal AI terakhir |
| `/history` | Trade history |
| `/stats` | Win rate & statistik |
| `/status` | Status bot |
| `/pause` | Pause bot |
| `/resume` | Resume bot |
| `/closeall` | Emergency close semua posisi |
| `/help` | Daftar command |

## Development Phases

- [x] Phase 1: Core Backend (Week 1-2)
- [ ] Phase 2: Risk Management (Week 3)
- [ ] Phase 3: Dashboard (Week 4)
- [ ] Phase 4: Hardening (Week 5-6)
- [ ] Phase 5: Live Trading (After paper trading)

## Safety Features

1. Max posisi aktif terbatas
2. Risk per trade terbatas
3. SL wajib dipasang
4. Emergency close jika koneksi putus > 60 detik
5. Auto pause jika balance drop > 20%
6. Leverage dikunci di config

## Deployment

### VPS Requirements

- Ubuntu 22.04
- Min 1 CPU, 2GB RAM
- PostgreSQL
- Nginx (reverse proxy)
- PM2 atau Supervisor

### Production Checklist

- [ ] Set `BINANCE_TESTNET=false`
- [ ] Gunakan strong password untuk database
- [ ] Setup SSL certificate (Let's Encrypt)
- [ ] Configure firewall (UFW)
- [ ] Setup monitoring & alerts
- [ ] Backup database secara berkala
- [ ] Test dengan modal kecil ($50-100)

## 📸 Screenshots

### Dashboard
![Dashboard](https://via.placeholder.com/800x400/0b0e11/FCD535?text=MnL+Dashboard)

### Telegram Bot
![Telegram Bot](https://via.placeholder.com/400x600/0b0e11/FCD535?text=Telegram+Bot)

## 🎥 Demo

Coming soon...

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Setup dan running dalam 10 menit
- [Configuration Guide](CONFIGURATION.md) - Penjelasan lengkap semua parameter
- [Deployment Guide](DEPLOYMENT.md) - Deploy ke VPS production
- [PRD Document](MnL_PRD.md) - Product Requirements Document lengkap

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**IMPORTANT:** Trading cryptocurrencies carries a high level of risk and may not be suitable for all investors. The high degree of leverage can work against you as well as for you. Before deciding to trade cryptocurrencies you should carefully consider your investment objectives, level of experience, and risk appetite.

**The developers of this software are not responsible for any financial losses incurred through the use of this trading bot.**

Key points:
- Start with testnet (fake money) for at least 2-4 weeks
- Paper trade until consistently profitable
- Start live trading with small capital you can afford to lose
- Never invest more than you can afford to lose
- Past performance does not guarantee future results
- This is experimental software - use at your own risk

## 🙏 Acknowledgments

- [Binance](https://www.binance.com) - Exchange API
- [Anthropic](https://www.anthropic.com) - Claude AI
- [CryptoPanic](https://cryptopanic.com) - Crypto news aggregator
- [NewsAPI](https://newsapi.org) - News API
- [ccxt](https://github.com/ccxt/ccxt) - Cryptocurrency exchange trading library

## 📧 Contact

For questions, suggestions, or issues:
- Open an issue on GitHub
- Email: [your-email@example.com]
- Telegram: [@your_telegram]

---

<div align="center">

Made with ❤️ by the MnL Team

**⭐ Star this repo if you find it useful!**

</div>
