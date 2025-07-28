#!/bin/bash
# Fix remote metadata issue for morning routine

echo "🔧 Fixing Remote ML Model Metadata"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}This script will:${NC}"
echo "1. Copy the fixed pipeline.py to remote"
echo "2. Create/fix metadata files on remote"
echo "3. Test the morning routine remotely"
echo ""

read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPO_REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

REMOTE_HOST="root@170.64.199.151"
REMOTE_PATH="/root/test"

echo -e "${YELLOW}Step 1: Copying fixed pipeline.py to remote...${NC}"
scp app/core/ml/training/pipeline.py $REMOTE_HOST:$REMOTE_PATH/app/core/ml/training/pipeline.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Pipeline.py copied successfully${NC}"
else
    echo -e "${RED}❌ Failed to copy pipeline.py${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 2: Ensuring metadata directories exist on remote...${NC}"
ssh $REMOTE_HOST "mkdir -p $REMOTE_PATH/data/ml_models/models"

echo -e "${YELLOW}Step 3: Copying metadata files to remote...${NC}"
scp data/ml_models/current_metadata.json $REMOTE_HOST:$REMOTE_PATH/data/ml_models/current_metadata.json
scp data/ml_models/models/current_metadata.json $REMOTE_HOST:$REMOTE_PATH/data/ml_models/models/current_metadata.json

echo -e "${YELLOW}Step 4: Testing morning routine on remote...${NC}"
ssh $REMOTE_HOST "cd $REMOTE_PATH && source ../trading_venv/bin/activate && python -m app.main morning"

echo ""
echo -e "${GREEN}🎉 Remote fix complete!${NC}"
echo ""
echo "If you still see the version error, run this command on the remote:"
echo "ssh root@170.64.199.151"
echo "cd /root/test"
echo "find . -name 'current_metadata.json' -exec grep -l 'version' {} \;"
echo ""
echo "All metadata files should contain a 'version' key."
