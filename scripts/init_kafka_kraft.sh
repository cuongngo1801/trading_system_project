#!/bin/bash

# Kafka KRaft Initialization Script
# This script initializes Kafka in KRaft mode without Zookeeper

set -e

echo "🚀 Initializing Kafka in KRaft mode..."

# Define cluster ID (consistent across restarts)
CLUSTER_ID="MkU3OEVBNTcwNTJENDM2Qk"

# Create docker network if it doesn't exist
docker network create trading-network 2>/dev/null || true

# Create Kafka data directory
mkdir -p ./data/kafka

echo "📝 Cluster ID: $CLUSTER_ID"

# Format the storage directory (only needed on first run)
echo "🔧 Formatting Kafka storage directory..."

# Create volume first if it doesn't exist
docker volume create kafka_data 2>/dev/null || true

# Create a temporary config file for initialization
cat > /tmp/kafka-init.properties << EOF
# Temporary Kafka configuration for KRaft initialization
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@localhost:29093
listeners=PLAINTEXT://localhost:29092,CONTROLLER://localhost:29093
listener.security.protocol.map=PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
controller.listener.names=CONTROLLER
inter.broker.listener.name=PLAINTEXT
log.dirs=/tmp/kraft-combined-logs
EOF

# Run with proper user and permissions
docker run --rm \
  --user root \
  -v kafka_data:/tmp/kraft-combined-logs \
  -v /tmp/kafka-init.properties:/etc/kafka/kafka-init.properties \
  confluentinc/cp-kafka:latest \
  bash -c "
    mkdir -p /tmp/kraft-combined-logs && \
    chown -R appuser:appuser /tmp/kraft-combined-logs && \
    kafka-storage format \
      --config /etc/kafka/kafka-init.properties \
      --cluster-id=$CLUSTER_ID \
      --ignore-formatted
  "

# Clean up temporary file
rm -f /tmp/kafka-init.properties

echo "✅ Kafka KRaft initialization completed successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Run: docker-compose -f docker/docker-compose.yml up -d kafka"
echo "  2. Check logs: docker logs trading-kafka"
echo "  3. Test connection: docker exec trading-kafka kafka-topics --bootstrap-server localhost:9092 --list"
echo ""
echo "🌐 Kafka will be available at:"
echo "  - Internal: kafka:29092"
echo "  - External: localhost:9092"
echo "  - Controller: localhost:9093"
echo "  - JMX: localhost:9101"
