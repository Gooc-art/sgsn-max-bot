#!/usr/bin/env bash
set -eu

sudo mkdir -p /opt/sud
sudo rsync -a --delete --exclude output --exclude .git ./ /opt/sud/
sudo chmod +x /opt/sud/sud_export.py
echo "Installed to /opt/sud"
