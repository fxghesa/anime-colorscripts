#!/bin/sh

# Install script for anime-colorscripts

if [ "$1" = "--user" ] || [ "$(id -u)" -ne 0 ]; then
    INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/anime-colorscripts"
    BIN_DIR="${HOME}/.local/bin"
else
    INSTALL_DIR='/usr/local/opt/anime-colorscripts'
    BIN_DIR='/usr/local/bin'
fi

echo "Installing to $INSTALL_DIR and $BIN_DIR..."

rm -rf "$INSTALL_DIR" || exit 1
mkdir -p "$INSTALL_DIR" || exit 1
mkdir -p "$BIN_DIR" || exit 1

cp -rf colorscripts "$INSTALL_DIR/"
cp -rf src "$INSTALL_DIR/"
cp anime-colorscripts.sh "$INSTALL_DIR/"
cp charalist.txt "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/anime-colorscripts.sh"

rm -f "$BIN_DIR/anime-colorscripts" || exit 1
ln -s "$INSTALL_DIR/anime-colorscripts.sh" "$BIN_DIR/anime-colorscripts"

echo "Installation complete! Run 'anime-colorscripts' to use."
