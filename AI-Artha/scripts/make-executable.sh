#!/bin/bash

# Make all shell scripts executable
echo "Making scripts executable..."

chmod +x scripts/run-all-tests.sh
chmod +x scripts/quick-test.sh
chmod +x scripts/deploy.sh
chmod +x scripts/deploy-prod.sh
chmod +x scripts/backup.sh
chmod +x scripts/backup-prod.sh
chmod +x scripts/restore.sh
chmod +x scripts/docker-setup.sh

echo "✅ All scripts are now executable"
echo ""
echo "You can now run:"
echo "  ./scripts/run-all-tests.sh    - Run all tests"
echo "  ./scripts/quick-test.sh       - Run quick tests"
echo "  ./scripts/deploy.sh           - Deploy development"
echo "  ./scripts/deploy-prod.sh      - Deploy production"
