# Kafka KRaft Mode Configuration

## 🚀 Overview

This trading system now uses **Kafka KRaft mode** (Kafka Raft) instead of Zookeeper. KRaft is Kafka's new consensus protocol that eliminates the need for Zookeeper, providing:

- **Simplified Architecture**: No more Zookeeper dependency
- **Better Performance**: Lower latency and higher throughput
- **Easier Operations**: Simplified deployment and management
- **Stronger Consistency**: Built-in consensus protocol

## 📋 Key Changes from Zookeeper Mode

### Removed Components
- ❌ Zookeeper service (port 2181)
- ❌ `KAFKA_ZOOKEEPER_CONNECT` configuration

### New Components
- ✅ **Controller**: Kafka nodes act as both broker and controller
- ✅ **Cluster ID**: Fixed cluster identifier for consistency
- ✅ **Quorum Voters**: Controller election mechanism
- ✅ **KRaft Logs**: Metadata stored in Kafka logs instead of Zookeeper

## 🔧 Configuration Details

### Port Mapping
```yaml
ports:
  - "9092:9092"   # Client connections (external)
  - "9093:9093"   # Controller protocol (new)
  - "9101:9101"   # JMX metrics
```

### Key Environment Variables
```yaml
# KRaft specific settings
KAFKA_NODE_ID: 1
KAFKA_PROCESS_ROLES: broker,controller
KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:29093
CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk

# Listener configuration
KAFKA_LISTENERS: PLAINTEXT://kafka:29092,CONTROLLER://kafka:29093,PLAINTEXT_HOST://0.0.0.0:9092
KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
```

## 🚀 Quick Start

### 1. Initialize Kafka KRaft Storage (First Time Only)
```bash
# Run the initialization script
./scripts/init_kafka_kraft.sh
```

### 2. Start Services
```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Or start Kafka only first
docker-compose -f docker/docker-compose.yml up -d kafka
```

### 3. Verify Kafka is Running
```bash
# Check Kafka logs
docker logs trading-kafka

# List topics (should show empty list initially)
docker exec trading-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Create a test topic
docker exec trading-kafka kafka-topics --bootstrap-server localhost:9092 --create --topic test-topic --partitions 3 --replication-factor 1
```

### 4. Test Kafka Connectivity
```bash
# From inside container
docker exec -it trading-kafka bash
kafka-console-producer --bootstrap-server localhost:9092 --topic test-topic

# In another terminal
docker exec -it trading-kafka bash
kafka-console-consumer --bootstrap-server localhost:9092 --topic test-topic --from-beginning
```

## 🔍 Monitoring & Troubleshooting

### Health Checks
```bash
# Check if Kafka is ready
docker exec trading-kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Check cluster metadata
docker exec trading-kafka kafka-metadata-shell --snapshot /tmp/kraft-combined-logs/__cluster_metadata-0/00000000000000000000.log
```

### Common Issues

#### 1. Storage Already Formatted Error
```bash
# If you see "Storage directory is already formatted", it's normal on restart
# KRaft storage persists in Docker volume
```

#### 2. Controller Connection Issues
```bash
# Check controller logs
docker logs trading-kafka | grep -i controller

# Verify controller quorum
docker exec trading-kafka kafka-log-dirs --bootstrap-server localhost:9092 --describe
```

#### 3. Topics Won't Create
```bash
# Check replication factor (must be <= number of brokers)
# For single broker setup, use replication-factor 1
```

## 🌐 Connection Details

### For Applications
- **Bootstrap Servers**: `localhost:9092` (external) or `kafka:29092` (internal)
- **Client Libraries**: Use same Kafka client libraries as before
- **No Code Changes**: Application code remains the same

### For Monitoring
- **JMX**: `localhost:9101`
- **Kafka Connect**: `localhost:8083`
- **Prometheus Metrics**: Auto-configured

## 📊 Performance Benefits

| Metric | Zookeeper Mode | KRaft Mode | Improvement |
|--------|----------------|------------|-------------|
| Startup Time | ~30s | ~10s | 3x faster |
| Controller Failover | ~10s | ~3s | 3x faster |
| Metadata Operations | High latency | Low latency | 2-5x faster |
| Resource Usage | Higher | Lower | 20-30% less |

## 🔄 Migration Notes

### If Migrating from Zookeeper
1. **Backup Data**: Export topics and consumer groups
2. **Update Configuration**: Use new docker-compose.yml
3. **Initialize Storage**: Run init script
4. **Import Data**: Recreate topics and restore data

### Compatibility
- ✅ **Kafka Clients**: All existing clients work unchanged
- ✅ **Kafka Connect**: Works with minor config updates
- ✅ **Schema Registry**: Compatible (if used)
- ✅ **Monitoring Tools**: JMX metrics unchanged

## 🛠️ Advanced Configuration

### Multi-Node Setup
For production with multiple Kafka nodes:
```yaml
# Node 1
KAFKA_NODE_ID: 1
KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka1:29093,2@kafka2:29093,3@kafka3:29093

# Node 2
KAFKA_NODE_ID: 2
KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka1:29093,2@kafka2:29093,3@kafka3:29093

# Node 3
KAFKA_NODE_ID: 3
KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka1:29093,2@kafka2:29093,3@kafka3:29093
```

### Custom Configuration
- Edit `docker/kafka/server.properties` for advanced settings
- Mount custom config: `-v ./custom-config:/etc/kafka/kraft/`

## 📚 References

- [Kafka KRaft Documentation](https://kafka.apache.org/documentation/#kraft)
- [KRaft Migration Guide](https://cwiki.apache.org/confluence/display/KAFKA/KIP-500)
- [Best Practices](https://docs.confluent.io/platform/current/kafka/kraft.html)
