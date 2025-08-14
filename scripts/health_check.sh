#!/bin/bash

# Trading System Health Check Script
# This script verifies all components are working correctly

set -e

echo "🔍 Trading System Health Check"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local host=$2
    local port=$3

    echo -n "Checking $service_name ($host:$port)... "

    if timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to check Docker service
check_docker_service() {
    local service_name=$1
    local container_name=$2

    echo -n "Checking Docker service $service_name... "

    if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
        local status=$(docker inspect --format="{{.State.Health.Status}}" "$container_name" 2>/dev/null || echo "unknown")
        if [[ "$status" == "healthy" ]] || [[ "$status" == "unknown" ]]; then
            echo -e "${GREEN}✓ Running${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Running but unhealthy${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Check if Docker is running
echo "Checking Docker daemon..."
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

echo ""
echo "📋 Checking Docker Services:"
echo "----------------------------"

# Check all Docker containers
services=(
    "Kafka:trading-kafka"
    "PostgreSQL:trading-postgres"
    "TimescaleDB:trading-timescaledb"
    "Redis:trading-redis"
    "Prometheus:trading-prometheus"
    "Grafana:trading-grafana"
    "Kafka Connect:trading-kafka-connect"
)

service_status=0
for service in "${services[@]}"; do
    IFS=':' read -r name container <<< "$service"
    if ! check_docker_service "$name" "$container"; then
        service_status=1
    fi
done

echo ""
echo "🌐 Checking Network Connectivity:"
echo "--------------------------------"

# Check network ports
ports=(
    "Kafka:localhost:9092"
    "PostgreSQL:localhost:5432"
    "TimescaleDB:localhost:5433"
    "Redis:localhost:6379"
    "Prometheus:localhost:9090"
    "Grafana:localhost:3000"
    "Kafka Connect:localhost:8083"
)

network_status=0
for port_check in "${ports[@]}"; do
    IFS=':' read -r name host port <<< "$port_check"
    if ! check_service "$name" "$host" "$port"; then
        network_status=1
    fi
done

echo ""
echo "🧪 Testing Service Functionality:"
echo "--------------------------------"

# Test Kafka
echo -n "Testing Kafka topics... "
if docker exec trading-kafka kafka-topics --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    service_status=1
fi

# Test PostgreSQL
echo -n "Testing PostgreSQL connection... "
if docker exec trading-postgres psql -U trading_user -d trading_db -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    service_status=1
fi

# Test TimescaleDB
echo -n "Testing TimescaleDB connection... "
if docker exec trading-timescaledb psql -U timescale_user -d trading_timescale -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    service_status=1
fi

# Test Redis
echo -n "Testing Redis connection... "
if docker exec trading-redis redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    service_status=1
fi

# Test Prometheus
echo -n "Testing Prometheus API... "
if curl -s http://localhost:9090/api/v1/status/config >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    service_status=1
fi

# Test Grafana
echo -n "Testing Grafana API... "
if curl -s http://localhost:3000/api/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    service_status=1
fi

echo ""
echo "📊 System Information:"
echo "---------------------"

# Show resource usage
echo "Docker containers resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10

echo ""
echo "💾 Volume Information:"
echo "---------------------"
docker volume ls | grep docker_

echo ""
echo "🔗 Service URLs:"
echo "---------------"
echo "• Grafana Dashboard: http://localhost:3000 (admin/admin123)"
echo "• Prometheus: http://localhost:9090"
echo "• Kafka Connect: http://localhost:8083"

echo ""
echo "==============================================="

# Final status
if [[ $service_status -eq 0 && $network_status -eq 0 ]]; then
    echo -e "${GREEN}🎉 All systems operational! Trading system is ready.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some issues detected. Please check the failed services.${NC}"
    echo ""
    echo "💡 Common fixes:"
    echo "• Wait a few more seconds for services to fully start"
    echo "• Run: docker-compose -f docker/docker-compose.yml restart <service-name>"
    echo "• Check logs: docker logs <container-name>"
    echo "• Initialize Kafka: ./scripts/init_kafka_kraft.sh"
    exit 1
fi
