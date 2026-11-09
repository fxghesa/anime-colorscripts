#!/bin/sh

# Uninstall script for anime-colorscripts

removed=0

# User installation paths
USER_INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/anime-colorscripts"
USER_BIN_FILE="$HOME/.local/bin/anime-colorscripts"

# System installation paths
SYS_INSTALL_DIR="/usr/local/opt/anime-colorscripts"
SYS_BIN_FILE="/usr/local/bin/anime-colorscripts"

# Remove user installation if present
if [ -d "$USER_INSTALL_DIR" ] || [ -e "$USER_BIN_FILE" ]; then
    echo "Removing user installation from $USER_INSTALL_DIR and $USER_BIN_FILE..."
    rm -rf "$USER_INSTALL_DIR"
    rm -f "$USER_BIN_FILE"
    removed=1
fi

# Remove system installation if present
if [ -d "$SYS_INSTALL_DIR" ] || [ -e "$SYS_BIN_FILE" ]; then
    if [ "$(id -u)" -eq 0 ] || [ -w "/usr/local/opt" ] 2>/dev/null; then
        echo "Removing system installation from $SYS_INSTALL_DIR and $SYS_BIN_FILE..."
        rm -rf "$SYS_INSTALL_DIR"
        rm -f "$SYS_BIN_FILE"
        removed=1
    else
        echo "System installation detected at $SYS_INSTALL_DIR."
        echo "Run 'sudo ./uninstall.sh' to remove system-wide installation."
    fi
fi

if [ "$removed" -eq 1 ]; then
    echo "anime-colorscripts has been successfully uninstalled."
else
    echo "No installation of anime-colorscripts was found."
fi
