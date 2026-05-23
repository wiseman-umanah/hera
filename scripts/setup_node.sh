#!/bin/bash
# Hedera Localnet Setup Script (Docker Required)

ACTION=$1

case $ACTION in
  "start")
    echo "🚀 Starting Hedera Local Node..."
    npx @hashgraph/hedera-local start --network localnet --detaching
    ;;
  "stop")
    echo "🛑 Stopping Hedera Local Node..."
    npx @hashgraph/hedera-local stop
    ;;
  "restart")
    echo "♻️ Restarting Hedera Local Node..."
    npx @hashgraph/hedera-local stop
    npx @hashgraph/hedera-local start --network localnet --detaching
    ;;
  "clean")
    echo "🧹 Cleaning up Hedera Local Node..."
    npx @hashgraph/hedera-local stop
    # Optional: remove volumes if needed manually
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|clean}"
    exit 1
    ;;
esac
