"""Main application entry point for trading system."""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

from trading_system.utils.config import Config, load_config
from trading_system.utils.logger import configure_logging, get_logger


class TradingSystemApp:
    """Main trading system application."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize trading system application.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config: Optional[Config] = None
        self.logger = None
        self.running = False

        # Components
        self.kafka_producer = None
        self.kafka_consumer = None
        self.database = None
        self.strategy_engine = None
        self.order_manager = None
        self.monitor = None

    async def initialize(self) -> None:
        """Initialize application components."""
        try:
            # Load configuration
            self.config = (
                load_config(self.config_file)
                if self.config_file
                else load_config("config/development.yaml")
            )

            # Configure logging
            log_file = f"logs/trading-system-{self.config.environment}.log"
            configure_logging(
                level=self.config.monitoring.log_level,
                format_type="json"
                if self.config.environment == "production"
                else "console",
                log_file=log_file,
            )

            self.logger = get_logger("main", {"component": "application"})
            self.logger.info(
                "Starting trading system initialization",
                environment=self.config.environment,
            )

            # Initialize components
            await self._initialize_database()
            await self._initialize_kafka()
            await self._initialize_strategy_engine()
            await self._initialize_order_manager()
            await self._initialize_monitoring()

            self.logger.info("Trading system initialization completed successfully")

        except Exception as e:
            if self.logger:
                self.logger.exception(
                    "Failed to initialize trading system", error=str(e)
                )
            else:
                print(f"Failed to initialize trading system: {e}")
            raise

    async def _initialize_database(self) -> None:
        """Initialize database connections."""
        self.logger.info("Initializing database connections")

        # TODO: Initialize DatabaseManager
        # from trading_system.data.database import DatabaseManager
        # self.database = DatabaseManager(self.config.database)
        # await self.database.initialize()

        self.logger.info("Database connections initialized")

    async def _initialize_kafka(self) -> None:
        """Initialize Kafka producer and consumer."""
        self.logger.info("Initializing Kafka connections")

        # TODO: Initialize Kafka components
        # from trading_system.data.kafka_producer import KafkaProducer
        # from trading_system.data.kafka_consumer import KafkaConsumer
        #
        # self.kafka_producer = KafkaProducer(self.config.kafka)
        # self.kafka_consumer = KafkaConsumer(self.config.kafka)
        #
        # await self.kafka_producer.start()
        # await self.kafka_consumer.start()

        self.logger.info("Kafka connections initialized")

    async def _initialize_strategy_engine(self) -> None:
        """Initialize strategy engine."""
        self.logger.info("Initializing strategy engine")

        # TODO: Initialize TrendContinuationStrategy
        # from trading_system.core.strategy import TrendContinuationStrategy
        # self.strategy_engine = TrendContinuationStrategy(self.config.strategy)

        self.logger.info("Strategy engine initialized")

    async def _initialize_order_manager(self) -> None:
        """Initialize order manager."""
        self.logger.info("Initializing order manager")

        # TODO: Initialize OrderManager
        # from trading_system.execution.order_manager import OrderManager
        # self.order_manager = OrderManager(self.config)

        self.logger.info("Order manager initialized")

    async def _initialize_monitoring(self) -> None:
        """Initialize monitoring and metrics."""
        self.logger.info("Initializing monitoring system")

        # TODO: Initialize monitoring components
        # from trading_system.monitoring.performance_tracker import PerformanceTracker
        # self.monitor = PerformanceTracker(self.config.monitoring)
        # await self.monitor.start()

        self.logger.info("Monitoring system initialized")

    async def start(self) -> None:
        """Start the trading system."""
        try:
            self.logger.info("Starting trading system")
            self.running = True

            # Start main application loop
            await self._run_main_loop()

        except Exception as e:
            self.logger.exception("Error in trading system execution", error=str(e))
            raise

    async def _run_main_loop(self) -> None:
        """Main application loop."""
        self.logger.info("Trading system main loop started")

        try:
            while self.running:
                # Main processing logic will go here
                # For now, just maintain the loop
                await asyncio.sleep(1)

                # TODO: Add main processing logic
                # - Process market data
                # - Generate signals
                # - Execute trades
                # - Update monitoring metrics

        except asyncio.CancelledError:
            self.logger.info("Main loop cancelled")
        except Exception as e:
            self.logger.exception("Error in main loop", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop the trading system gracefully."""
        self.logger.info("Stopping trading system")
        self.running = False

        # Cleanup components
        if self.kafka_consumer:
            await self.kafka_consumer.stop()

        if self.kafka_producer:
            await self.kafka_producer.stop()

        if self.database:
            await self.database.close()

        if self.monitor:
            await self.monitor.stop()

        self.logger.info("Trading system stopped successfully")

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Trading System")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument(
        "--environment",
        type=str,
        choices=["development", "staging", "production"],
        default="development",
        help="Environment to run in",
    )

    args = parser.parse_args()

    # Determine config file
    config_file = args.config
    if not config_file:
        config_file = f"config/{args.environment}.yaml"

    # Create and run application
    app = TradingSystemApp(config_file)
    app.setup_signal_handlers()

    try:
        await app.initialize()
        await app.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)
    finally:
        await app.stop()


if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Run the application
    asyncio.run(main())
