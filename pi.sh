#!/bin/bash

sleep 5

# Allow VLC to run under root
sed -i 's/geteuid/getppid/' /usr/bin/vlc

# Remove the X server lock file so ours starts cleanly
rm /tmp/.X0-lock &>/dev/null || true

# Set the display to use
# ALB - Not Used
export DISPLAY=:0

# Set the DBUS address for sending around system messages
export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket

# Set XDG_RUNTIME_DIR
mkdir -pv ~/.cache/xdgr
export XDG_RUNTIME_DIR=$PATH:~/.cache/xdgr

# Create Xauthority
touch /root/.Xauthority

# Start desktop manager
echo "STARTING X"
startx -- -nocursor &

# TODO: work out how to detect X has started
sleep 5

# Print all of the current displays used by running processes
echo "Displays in use after starting X"
DISPLAYS=`ps -u $(id -u) -o pid= | \
  while read pid; do
    cat /proc/$pid/environ 2>/dev/null | tr '\0' '\n' | grep '^DISPLAY=:'
  done | sort -u`
echo $DISPLAYS

# Always set display to last display
LAST_DISPLAY=`ps -u $(id -u) -o pid= | \
  while read pid; do
    cat /proc/$pid/environ 2>/dev/null | tr '\0' '\n' | grep '^DISPLAY=:'
  done | sort -u | tail -n1`
echo "Setting display to: ${LAST_DISPLAY}"
export $LAST_DISPLAY

# Prevent blanking and screensaver
# ALB bash: xset: command not found
xset s off -dpms

# Hide the cursor
#unclutter: could not open display
unclutter -idle 0.1 &

#sleep infinity
python3 vcr.py
