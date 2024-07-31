#!/bin/bash

# Improved variable naming (lowercase with underscores)
packets=$(sed -n 's/packets_file= //p' conf.ini)
interface=$(sed -n 's/interface= //p' conf.ini)
filter=$(sed -n 's/filter= //p' conf.ini)

# Trap SIGINT (Ctrl+C) and exit cleanly
trap 'echo "Capture interrupted. Exiting..."; exit 0' SIGINT

while true; do
    tshark -f "$filter" -i $interface  -a "packets:$packets" -T ek  > cap_json/capture_$(date +%Y-%m-%d_%H-%M-%S).json
done

