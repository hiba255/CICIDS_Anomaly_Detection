#!/bin/bash
API_URL="http://192.168.56.1:8000/predict-live"
echo "Starting live detection → $API_URL"
cicflowmeter -i enp0s8 -u $API_URL output