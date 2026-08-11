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
SGSN_WEEKLY_CHAT_ID=
EOF
  chmod 600 "$env_file"
elif ! grep -q '^SGSN_WEEKLY_CHAT_ID=' "$env_file"; then
  printf '\nSGSN_WEEKLY_CHAT_ID=\n' >> "$env_file"
fi

cat > "$HOME/.config/systemd/user/sgsn-weekly-sgsn.service" <<EOF
[Unit]
Description=SGSN weekly notification
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$HOME/sgsn-max-bot
EnvironmentFile=$env_file
ExecStart=/usr/bin/python3 $HOME/sgsn-max-bot/weekly_sgsn_notify.py --timeout 8
EOF

cat > "$HOME/.config/systemd/user/sgsn-weekly-sgsn.timer" <<'EOF'
[Unit]
Description=Run SGSN weekly notification every Sunday night

[Timer]
OnCalendar=Sun 03:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now sgsn-weekly-sgsn.timer
systemctl --user status sgsn-weekly-sgsn.timer --no-pager || true
