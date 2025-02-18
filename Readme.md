
# TheThinker - Solana Token Analytics Platform 🚀

A sophisticated platform for monitoring Solana tokens, tracking whale movements, and analyzing market trends in real-time.

## 🌟 Features

- **Real-time Token Monitoring**: Continuously tracks token data from DexScreener
- **Whale Movement Detection**: Identifies and monitors whale wallet activities
- **Telegram Alerts**: Instant notifications for significant whale transactions
- **Multi-Chain Support**: Primary focus on Solana with extensibility for other chains
- **Smart Data Processing**: Efficient handling of large datasets with batch processing
- **Automated Analysis**: Price movement detection and market trend analysis

## 🛠 Technology Stack

- **Backend**: Python 3.11
- **Framework**: AsyncIO for high-performance asynchronous operations
- **Database**: PostgreSQL
- **Caching**: Memcached
- **APIs**: 
  - Helius API for Solana data
  - DexScreener for market data
- **Messaging**: Telegram Bot API
- **Containerization**: Docker & Docker Compose

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Solana RPC endpoint
- Helius API key
- Telegram Bot token

### Installation

1. Clone the repository:
```bash
git clone https://github.com/MasterPo696/thethinker.git
cd thethinker
```

2. Create and configure your `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the services using Docker Compose:
```bash
docker-compose up -d
```

## 🔧 Configuration

Key environment variables:

```plaintext
HELIUS_API_KEY=your_helius_api_key
SOLANA_RPC=your_solana_rpc_endpoint
BOT_TOKEN=your_telegram_bot_token
MIN_WHALE_BALANCE_USD=5000
ALERT_AMOUNT=10000
```

## 🏗 Project Structure

```plaintext
backend/
├── app/
│   ├── parcing/         # Data collection and processing
│   ├── telegram/        # Telegram bot implementation
│   ├── utils/          # Utility functions and configs
│   └── main.py         # Application entry point
├── data/               # Data storage
│   ├── raw/           # Raw collected data
│   ├── clean/         # Processed data
│   └── pumped/        # Pumped tokens data
│   └── whales/        # Whale tracking data
└── docker/            # Docker configuration files
```

## 📊 Features in Detail

### Whale Tracking
- Monitors wallet addresses with significant holdings
- Tracks transactions above configurable thresholds
- Provides real-time alerts for whale movements

### Token Analysis
- Tracks price movements and market trends
- Identifies potential pump patterns
- Monitors liquidity changes

### Smart Logging
- Batch processing of log events
- Configurable logging levels
- Efficient storage and retrieval

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Helius](https://docs.helius.xyz/) for Solana data
- [DexScreener](https://docs.dexscreener.com/) for DEX data
- The Solana community

## ⚠️ Disclaimer

This project is for educational and research purposes only. Always do your own research before making any investment decisions.
