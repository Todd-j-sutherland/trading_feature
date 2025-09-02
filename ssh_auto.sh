#!/bin/bash
# Auto SSH with passphrase
export SSH_ASKPASS_REQUIRE=never
echo "todd" | ssh-add ~/.ssh/id_ed25519 2>/dev/null
ssh "$@"
