#!/usr/bin/env bash
set -euo pipefail

# Safe starter for Cloud SQL Auth proxy
# - Downloads linux binary if none available
# - Verifies existing PID/socket and avoids removing sockets in use
# - Starts proxy with unix socket dir (/tmp) by default

BASE_DIR=$(cd "$(dirname "$0")" && pwd)
PIDFILE="$BASE_DIR/cloud-sql-proxy.pid"
LOGFILE="$BASE_DIR/cloud-sql-proxy.log"
LOCAL_BIN="$BASE_DIR/cloud_sql_proxy"
SYSTEM_BIN="/usr/local/bin/cloud_sql_proxy"

# Default instance (override by passing instance as first arg)
DEFAULT_INSTANCES="asieselfutbol:us-east4:newsai"
INSTANCES="${1:-$DEFAULT_INSTANCES}"

echo "Using instances: $INSTANCES"

find_bin() {
  if [ -x "$SYSTEM_BIN" ]; then
    echo "$SYSTEM_BIN"
    return
  fi
  if [ -x "$LOCAL_BIN" ]; then
    echo "$LOCAL_BIN"
    return
  fi
  # check PATH
  if command -v cloud_sql_proxy >/dev/null 2>&1; then
    command -v cloud_sql_proxy
    return
  fi
  return 1
}

BIN=$(find_bin || true)
if [ -z "$BIN" ]; then
  echo "cloud_sql_proxy not found locally — attempting to download linux binary to $LOCAL_BIN"
  # Try several possible official filenames (fallbacks)
  urls=(
    "https://dl.google.com/cloudsql/cloud_sql_proxy.linux.x86_64"
    "https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64"
    "https://dl.google.com/cloudsql/cloud_sql_proxy.linux.x86-64"
    "https://dl.google.com/cloudsql/cloud_sql_proxy.linux.arm64"
    "https://dl.google.com/cloudsql/cloud_sql_proxy.linux"
  )
  downloaded=0
  for u in "${urls[@]}"; do
    echo "Trying: $u"
    if curl -fsSL -o "$LOCAL_BIN" "$u"; then
      downloaded=1
      break
    fi
  done

  if [ "$downloaded" -ne 1 ]; then
    echo "Failed to download cloud_sql_proxy from known URLs."
    echo "Please download the Linux binary manually from:" 
    echo "  https://cloud.google.com/sql/docs/mysql/connect-admin-proxy#install"
    echo "Then place it at: $LOCAL_BIN and make it executable: chmod +x $LOCAL_BIN"
    exit 22
  fi

  chmod +x "$LOCAL_BIN"
  BIN="$LOCAL_BIN"
fi

echo "Using cloud_sql_proxy binary: $BIN"

# Socket path used by this invocation
SOCKET_PATH="/tmp/${INSTANCES}"

if [ -f "$PIDFILE" ]; then
  pid=$(cat "$PIDFILE" 2>/dev/null || true)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "cloud_sql_proxy already running (pid $pid). Exiting."
    exit 0
  fi
  echo "Found stale pidfile (pid $pid) but no process. Removing pidfile."
  rm -f "$PIDFILE"
fi

# If socket exists but no process is running, remove stale socket
if [ -e "$SOCKET_PATH" ]; then
  echo "Socket $SOCKET_PATH exists. Checking for owner process..."
  # try to find process using the unix socket (ss may exist)
  if command -v ss >/dev/null 2>&1; then
    if ss -anx | grep -F -- "$SOCKET_PATH" >/dev/null 2>&1; then
      echo "Socket appears in ss output; assume proxy is running. Exiting."
      exit 0
    fi
  fi
  # As fallback, try lsof
  if command -v lsof >/dev/null 2>&1; then
    if lsof -U | grep -F -- "$SOCKET_PATH" >/dev/null 2>&1; then
      echo "Socket in use according to lsof. Exiting."
      exit 0
    fi
  fi
  echo "Socket present but not in use — removing stale socket."
  rm -f "$SOCKET_PATH"
fi

echo "Starting cloud_sql_proxy (logging to $LOGFILE)"
nohup "$BIN" -dir=/tmp -instances="$INSTANCES" >> "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
sleep 0.5
echo "Started cloud_sql_proxy pid $(cat "$PIDFILE")"
echo "Socket (should exist): $SOCKET_PATH"
ls -l "$SOCKET_PATH" 2>/dev/null || true

echo "Done. Use 'tail -f $LOGFILE' to follow logs, and 'cat $PIDFILE' to see pid."
