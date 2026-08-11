#!/usr/bin/env bash
set -eu

env_dir="$HOME/.config/sgsn-max-bot"
env_file="$env_dir/max-bot.env"
mkdir -p "$HOME/.config/systemd/user" "$env_dir"
if [ ! -f "$env_file" ]; then
  cat > "$env_file" <<'EOF'
MAX_TOKEN=
MAX_API_BASE=https://platform-api2.max.ru
SGSN_MAX_DAYS=45
SGSN_EXPORT_TIMEOUT_SECONDS=14400
SGSN_HTTP_TIMEOUT_SECONDS=20
EOF
  chmod 600 "$env_file"
fi

cat > "$HOME/.config/systemd/user/sgsn-max-bot.service" <<EOF
[Unit]
Description=SGSN MAX bot
After=network-online.target

[Service]
WorkingDirectory=$HOME/sgsn-max-bot
EnvironmentFile=$env_file
ExecStart=/usr/bin/python3 $HOME/sgsn-max-bot/max_bot.py --poll
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable sgsn-max-bot.service
systemctl --user status sgsn-max-bot.service --no-pager || true
