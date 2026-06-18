#!/bin/bash
TARGET="192.168.56.20"
echo "Starting normal traffic..."
while true; do
  curl -s http://$TARGET > /dev/null
  sleep $((RANDOM % 5 + 1))
  ping -c 3 $TARGET > /dev/null
  sleep $((RANDOM % 3 + 1))
  wget -q http://$TARGET -O /dev/null
  sleep $((RANDOM % 4 + 2))
done