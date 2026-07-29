#!/usr/bin/env bash
set -eu

if [ -z "${MAX_TOKEN:-}" ]; then
  echo "Set MAX_TOKEN first"
  exit 1
fi

mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/sud-max-bot.service" <<EOF
[Unit]
Description=SUD MAX bot
After=network-online.target

[Service]
WorkingDirectory=$HOME/sud-app
Environment=MAX_TOKEN=$MAX_TOKEN
ExecStart=/usr/bin/python3 $HOME/sud-app/max_bot.py --poll
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now sud-max-bot.service
systemctl --user status sud-max-bot.service
