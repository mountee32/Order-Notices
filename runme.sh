#!/bin/bash

# Set the directory where you want to clone the repository
REPO_DIR="/home/andy/Order-Notices"

# Set the GitHub repository URL
REPO_URL="https://github.com/mountee32/Order-Notices.git"

screen_name="order-notices"

if screen -list | grep -q "$screen_name"; then
    echo "Screen session already exists, reattaching"
    screen -r "$screen_name"
else
    echo "Screen session doesn't exist, creating new"
    screen -dmS "$screen_name" bash -c '
        while true; do
            # Change to the repository directory
            cd "$REPO_DIR"

            # Check if the directory exists
            if [ ! -d "$REPO_DIR" ]; then
                # If the directory doesn't exist, clone the repository
                git clone "$REPO_URL" "$REPO_DIR"
            else
                # If the directory exists, pull the latest changes
                git pull
            fi
            chmod +x runme.sh
            # Install required Python modules (just needed the first time)
            # pip3 install -r  requirements.txt 

            # Run the Python program
            python3 main.py
            # python3 main.py excel

            # Sleep for 2 minutes (120 seconds)
            sleep 120
        done
    '
fi