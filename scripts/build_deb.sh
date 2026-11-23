#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-0.1.0}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
PKG="$DIST/face-privacy-toolkit_${VERSION}_all"
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" "$PKG/usr/lib/face-privacy-toolkit" "$PKG/usr/bin" "$PKG/usr/share/doc/face-privacy-toolkit"
cat > "$PKG/DEBIAN/control" <<EOF
Package: face-privacy-toolkit
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Maintainer: BENDER35 <grandrodri3@gmail.com>
Depends: python3, python3-pil, python3-numpy
Recommends: python3-opencv
Description: Privacy-focused image toolkit (EXIF, redact, local hash)
 Local CLI/web tools for image privacy. No social scraping, no biometric
 identification, no online profile matching.
EOF
install -m 0755 "$ROOT/face_privacy.py" "$PKG/usr/lib/face-privacy-toolkit/face_privacy.py"
install -m 0755 "$ROOT/web_app.py" "$PKG/usr/lib/face-privacy-toolkit/web_app.py"
install -m 0644 "$ROOT/README.md" "$ROOT/GUIDE.md" "$ROOT/LICENSE" "$PKG/usr/share/doc/face-privacy-toolkit/"
cat > "$PKG/usr/bin/face-privacy" <<'EOF'
#!/usr/bin/env bash
exec python3 /usr/lib/face-privacy-toolkit/face_privacy.py "$@"
EOF
cat > "$PKG/usr/bin/face-privacy-web" <<'EOF'
#!/usr/bin/env bash
exec python3 /usr/lib/face-privacy-toolkit/web_app.py "$@"
EOF
chmod 0755 "$PKG/usr/bin/face-privacy" "$PKG/usr/bin/face-privacy-web"
mkdir -p "$DIST"
dpkg-deb --build --root-owner-group "$PKG" "$DIST/face-privacy-toolkit_${VERSION}_all.deb" >/dev/null
echo "$DIST/face-privacy-toolkit_${VERSION}_all.deb"
