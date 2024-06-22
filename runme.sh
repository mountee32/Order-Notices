#!/bin/bash

# Function to print quick tips
print_quick_tips() {
    echo "Quick Tips:"
    echo "1. View running screen sessions: screen -ls"
    echo "2. Attach to a screen session: screen -r [session_name]"
    echo "3. Detach from a screen session: Ctrl+A, then D"
    echo "4. Stop the script: Ctrl+C (when attached to the screen)"
    echo "5. View program output: http://localhost:8000/log.txt"
    echo "6. Check Git status: git status (in the Order-Notices directory)"
    echo "7. Update repository: git pull (in the Order-Notices directory)"
    echo "8. Restart the script: ./runme.sh (after stopping it)"
    echo ""
}

# Set the directory where you want to clone the repository
REPO_DIR="/home/andy/Order-Notices"

# Set the GitHub repository URL
REPO_URL="https://github.com/mountee32/Order-Notices.git"

screen_name="order-notices"
server_name="log-server"

# Print quick tips
print_quick_tips

# Function to start the HTTP server
start_http_server() {
    if screen -list | grep -q "$server_name"; then
        echo "HTTP server screen session already exists"
    else
        echo "Starting HTTP server in a new screen session"
        screen -dmS "$server_name" bash -c "cd $REPO_DIR && python3 -m http.server 8000"
    fi
}

# Start the HTTP server once at the beginning
start_http_server

if screen -list | grep -q "$screen_name"; then
    echo "Screen session already exists, reattaching"
    screen -r "$screen_name"
else
    echo "Screen session doesn't exist, creating new"
    screen -dmS "$screen_name" bash -c "
        while true; do
            # Change to the repository directory
            cd \"$REPO_DIR\"

            # Check if the directory exists
            if [ ! -d \"$REPO_DIR\" ]; then
                # If the directory doesn't exist, clone the repository
                git clone \"$REPO_URL\" \"$REPO_DIR\"
            else
                # If the directory exists, pull the latest changes
                git pull && {
                    chmod +x runme.sh
                    # Install required Python modules (just needed the first time)
                    # pip3 install -r requirements.txt

                    # Run the Python program
                    python3 main.py
                    # python3 main.py excel
                }
            fi

            # Sleep for 2 minutes (120 seconds)
            sleep 120
        done
    "
fi
