#!/bin/bash

# network_recovery.sh - Ensure HID server is running when network comes back
# Called by NetworkManager when network state changes

SERVER_DIR="/home/velt/Code/Projects/hid_server"
LOG_FILE="$SERVER_DIR/network_recovery.log"

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to check network connectivity
check_network() {
    # Try multiple reliable hosts
    for host in 8.8.8.8 1.1.1.1 8.8.4.4; do
        if ping -c 1 -W 5 "$host" > /dev/null 2>&1; then
            return 0  # Network is up
        fi
    done
    return 1  # Network is down
}

# Main logic
main() {
    log_message "=== Network Recovery Check ==="
    
    if check_network; then
        log_message "✅ Network connectivity confirmed"
        
        # Check if HID server service is running
        if systemctl is-active --quiet hid-server; then
            log_message "✅ HID server service is running"
            
            # Run full health check
            if "$SERVER_DIR/health_check.sh" > /dev/null 2>&1; then
                log_message "✅ HID server health check passed"
            else
                log_message "⚠️  HID server health check failed - restart already handled"
            fi
        else
            log_message "🔄 HID server service not running - starting"
            
            if systemctl start hid-server; then
                log_message "✅ HID server service started successfully"
            else
                log_message "❌ Failed to start HID server service"
            fi
        fi
    else
        log_message "❌ Network connectivity not available"
    fi
    
    log_message "Network recovery check completed"
}

# Run main function
main
