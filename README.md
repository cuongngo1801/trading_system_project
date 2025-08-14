# Trading System Project

Production-Grade Session-Based Trend Continuation Analysis System

## Overview

This project implements a comprehensive trading system for session-based trend continuation analysis targeting forex markets (US30, XAUUSD). The system features real-time data processing, sophisticated backtesting capabilities, risk management, and live trading execution.

## Features

- **Real-time Data Pipeline**: Apache Kafka-based streaming architecture
- **Session-Based Analysis**: Trading sessions (Asian, European, US) with timezone handling
- **Trend Analysis**: EMA crossovers and ADX filters for trend detection
- **Risk Management**: ATR-based position sizing and comprehensive risk controls
- **Backtesting Framework**: Walk-forward analysis with statistical validation
- **Live Trading**: MetaTrader 5 integration for order execution
- **Monitoring**: Prometheus metrics with Grafana dashboards
- **Production Ready**: Docker containerization and Kubernetes deployment

## Architecture

The system follows a microservices architecture with the following components:

- **Data Layer**: PostgreSQL with TimescaleDB for time-series data
- **Streaming**: Apache Kafka in KRaft mode (no Zookeeper) for real-time data processing
- **Core Engine**: Python-based trading strategy implementation
- **Execution**: MetaTrader 5 integration for live trading
- **Monitoring**: Prometheus + Grafana for system observability
- **Caching**: Redis for session data and performance optimization

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- MetaTrader 5 (for live trading)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/trading-system-project.git
cd trading-system-project
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Build and start services:
```bash
make setup
make start
```

4. Install Python dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

### Development Setup

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

3. Run tests:
```bash
make test
```

## Configuration

The system uses YAML configuration files located in the `config/` directory:

- `development.yaml`: Development environment settings
- `production.yaml`: Production environment settings
- `kafka-topics.yaml`: Kafka topic configurations

## Usage

### Backtesting

Run a backtest analysis:
```bash
python scripts/run_backtest.py --config config/development.yaml --start-date 2023-01-01 --end-date 2023-12-31
```

### Live Trading

Start live trading (after thorough backtesting):
```bash
python scripts/live_trading.py --config config/production.yaml
```

### Monitoring

Access monitoring dashboards:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## Project Structure

```
trading-system-project/
├── trading_system/           # Main package
│   ├── core/                 # Core business logic
│   ├── data/                 # Data handling
│   ├── backtest/             # Backtesting framework
│   ├── execution/            # Live trading
│   ├── monitoring/           # System monitoring
│   └── utils/                # Utilities
├── tests/                    # Test suite
├── docker/                   # Docker configurations
├── config/                   # Configuration files
├── notebooks/                # Jupyter notebooks
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
└── .github/                  # GitHub Actions
```

## Testing

Run the test suite:
```bash
# Unit tests
make test-unit

# Integration tests
make test-integration

# Full test suite with coverage
make test-coverage
```

## Deployment

### Development
```bash
make deploy-dev
```

### Production
```bash
make deploy-prod
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Risk Disclaimer

This trading system is for educational and research purposes. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions, please open an issue on GitHub or contact the development team.
