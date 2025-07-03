#!/bin/bash

# health_check.sh - Health monitoring that works WITH systemd
# This monitors health and reports issues, systemd handles restarts

# Configuration
SERVER_DIR="/home/velt/Code/Projects/hid_server"
HEALTH_CHECK_URL="https://localhost:8444/"
LOG_FILE="$SERVER_DIR/health_check.log"

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to perform comprehensive health check
health_check() {
    log_message "=== Starting Health Check ==="
    
    # 1. Check if systemd service is running
    if ! systemctl is-active --quiet hid-server; then
        log_message "❌ Systemd service hid-server is not active"
        return 1
    fi
    log_message "✅ Systemd service is active"
    
    # 2. Check if port is listening
    if ! lsof -i :8444 > /dev/null 2>&1; then
        log_message "❌ No process listening on port 8444"
        return 1
    fi
    log_message "✅ Port 8444 is listening"
    
    # 3. Check HTTP endpoint
    if command -v curl > /dev/null 2>&1; then
        if curl -f -s -k --connect-timeout 5 "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log_message "✅ HTTP health check passed"
            return 0
        else
            local curl_exit_code=$?
            log_message "❌ HTTP health check failed (curl exit code: $curl_exit_code)"
            return 1
        fi
    else
        log_message "⚠️  curl not available, skipping HTTP check"
        return 0  # Consider it healthy if service is running and port is open
    fi
}

# Function to check service health and restart if needed
handle_unhealthy_service() {
    log_message "🔄 Service is unhealthy, requesting systemd restart"
    
    # Get current status for logging
    local service_status=$(systemctl is-active hid-server 2>/dev/null || echo "unknown")
    log_message "Current service status: $service_status"
    
    # Request restart via systemd
    if systemctl restart hid-server; then
        log_message "✅ Restart command sent successfully"
        
        # Wait for service to come back up
        local attempt=1
        while [ $attempt -le 6 ]; do  # Wait up to 60 seconds
            log_message "🔍 Restart verification attempt $attempt/6"
            sleep 10
            
            if systemctl is-active --quiet hid-server; then
                log_message "✅ Service is active after restart"
                
                # Give it a moment to start listening
                sleep 5
                
                if health_check; then
                    log_message "✅ Service is healthy after restart"
                    return 0
                else
                    log_message "⚠️  Service restarted but health check still fails"
                fi
            fi
            ((attempt++))
        done
        
        log_message "❌ Service failed to become healthy after restart"
        return 1
    else
        log_message "❌ Failed to send restart command"
        return 1
    fi
}

# Main execution
main() {
    log_message "Starting health check (systemd integration mode)"
    
    if health_check; then
        log_message "✅ All health checks passed"
        exit 0
    else
        log_message "❌ Health check failed"
        
        if handle_unhealthy_service; then
            log_message "✅ Service successfully recovered"
            exit 0
        else
            log_message "🚨 CRITICAL: Unable to recover service"
            exit 1
        fi
    fi
}

# Execute main function
main
