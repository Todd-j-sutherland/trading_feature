#!/bin/bash

# SSH connection script with automatic passphrase handling
# Usage: ./ssh_connect.sh [command]

HOST="root@170.64.199.151"
PASSPHRASE="todd"
TIMEOUT=30

# Function to handle SSH with passphrase
ssh_with_passphrase() {
    local cmd="$1"
    
    # Use expect if available, otherwise try direct piping
    if command -v expect >/dev/null 2>&1; then
        expect -c "
            set timeout $TIMEOUT
            spawn ssh $HOST \"$cmd\"
            expect \"Enter passphrase\"
            send \"$PASSPHRASE\r\"
            expect eof
        "
    else
        # Fallback method using echo and timeout
        timeout $TIMEOUT bash -c "echo '$PASSPHRASE' | ssh -o ConnectTimeout=10 -o BatchMode=no $HOST \"$cmd\""
    fi
}

# Main execution
if [ $# -eq 0 ]; then
    # Interactive session
    ssh_with_passphrase ""
else
    # Execute command
    ssh_with_passphrase "$*"
fi
