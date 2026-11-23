#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-0.1.0}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
NAME="face-privacy-toolkit-${VERSION}"
STAGE="$DIST/$NAME"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp "$ROOT/face_privacy.py" "$ROOT/web_app.py" "$ROOT/README.md" "$ROOT/GUIDE.md" "$ROOT/LICENSE" "$ROOT/requirements.txt" "$ROOT/.gitignore" "$STAGE/"
mkdir -p "$STAGE/scripts"
cp "$ROOT/scripts/build_deb.sh" "$ROOT/scripts/build_zip.sh" "$STAGE/scripts/"
mkdir -p "$DIST"
(cd "$DIST" && zip -qr "${NAME}.zip" "$NAME")
echo "$DIST/${NAME}.zip"
