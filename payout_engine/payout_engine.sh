#!/bin/sh

# Activate the virtual environment
source ~/myenv/bin/activate

# Run the Python script
sudo python3 -W ignore ~/banano-sports-pools/payout_engine/main.py

deactivate
