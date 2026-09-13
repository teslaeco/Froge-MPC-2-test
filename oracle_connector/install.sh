#!/usr/bin/env bash
set -Eeuo pipefail
trap 'echo "FROGE_SETUP_ERROR: instalator zatrzymal sie w linii $LINENO. Pokaz koncowke komunikatu."' ERR
if [ "$(id -un)" != opc ] || [ "$(uname -m)" != aarch64 ]; then
  echo "Uruchom ten instalator na swoim serwerze Oracle ARM, jako opc."
  exit 1
fi
base="$HOME/froge-connector"
if [ "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" != "$base" ]; then
  echo "Rozpakuj instalator do $base i uruchom go stamtad."
  exit 1
fi
sudo -n dnf install -y podman python3 curl zstd
if ! podman image exists localhost/froge-blender:local; then
  echo "Brak zainstalowanego obrazu Blendera. Najpierw zakoncz instalacje Blendera."
  exit 1
fi
python3 "$base/runtime_check.py"
mkdir -p "$base/state" "$base/ollama" "$base/bin" "$HOME/.config/systemd/user"
chmod 700 "$base/state"
python3 "$base/install_codex.py"
python3 "$base/codex_smoke.py" --build
if [ ! -x "$base/ollama/bin/ollama" ]; then
  echo "Pobieranie Ollama dla ARM64…"
  curl -fL --retry 2 --connect-timeout 20 -o "$base/ollama.tar.zst" https://ollama.com/download/ollama-linux-arm64.tar.zst
  tar --zstd -xf "$base/ollama.tar.zst" -C "$base/ollama"
  rm -- "$base/ollama.tar.zst"
fi
if [ ! -x "$base/bin/cloudflared" ]; then
  echo "Pobieranie tunelu HTTPS Cloudflare…"
  curl -fL --retry 2 --connect-timeout 20 -o "$base/bin/cloudflared" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
  chmod 755 "$base/bin/cloudflared"
fi
cat > "$HOME/.config/systemd/user/froge-ollama.service" <<'UNIT'
[Unit]
Description=Froge local AI
After=network-online.target
[Service]
ExecStart=%h/froge-connector/ollama/bin/ollama serve
Environment=OLLAMA_HOST=127.0.0.1:11434
Environment=OLLAMA_MODELS=%h/froge-connector/state/ollama-models
Environment=OLLAMA_NUM_PARALLEL=1
Environment=OLLAMA_MAX_LOADED_MODELS=1
Environment=OLLAMA_NO_CLOUD=1
MemoryMax=8G
Restart=on-failure
RestartSec=5
[Install]
WantedBy=default.target
UNIT
cat > "$HOME/.config/systemd/user/froge-worker.service" <<'UNIT'
[Unit]
Description=Froge Blender model worker
After=network-online.target froge-ollama.service
Wants=froge-ollama.service
[Service]
ExecStart=/usr/bin/python3 %h/froge-connector/server.py
WorkingDirectory=%h/froge-connector
Environment=PYTHONUNBUFFERED=1
Restart=on-failure
RestartSec=5
[Install]
WantedBy=default.target
UNIT
cat > "$HOME/.config/systemd/user/froge-tunnel.service" <<'UNIT'
[Unit]
Description=Froge development HTTPS tunnel
After=network-online.target froge-worker.service
[Service]
ExecStart=%h/froge-connector/bin/cloudflared tunnel --no-autoupdate --protocol http2 --url http://127.0.0.1:8765 --logfile %h/froge-connector/state/tunnel.log
Restart=on-failure
RestartSec=10
[Install]
WantedBy=default.target
UNIT
cat > "$HOME/.config/systemd/user/froge-model-pull.service" <<'UNIT'
[Unit]
Description=Download Froge local AI model
After=froge-ollama.service
Wants=froge-ollama.service
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 %h/froge-connector/pull_model.py
WorkingDirectory=%h/froge-connector
Restart=on-failure
RestartSec=60
TimeoutStartSec=infinity
[Install]
WantedBy=default.target
UNIT
sudo -n loginctl enable-linger opc
systemctl --user daemon-reload
systemctl --user enable --now froge-ollama.service froge-worker.service froge-tunnel.service
systemctl --user enable froge-model-pull.service
systemctl --user start --no-block froge-model-pull.service
echo "Programy dzialaja w tle. Przygotowanie modelu AI widac pozniej w ustawieniach strony."
for attempt in {1..30}; do
  if [ -f "$base/state/tunnel.log" ] && python3 -c 'import pathlib,re,sys; sys.exit(not bool(re.search(r"https://[a-z0-9-]+\.trycloudflare\.com",pathlib.Path(sys.argv[1]).read_text(errors="replace"))))' "$base/state/tunnel.log"; then
    break
  fi
  sleep 2
done
python3 "$base/server.py" --pair-info
echo "FROGE_CONNECTOR_INSTALLED"
echo "Adres tunelu testowego moze zmienic sie po jego restarcie."
