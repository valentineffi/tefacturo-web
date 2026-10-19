#!/usr/bin/env bash
# Publica docs/ en el VPS de producción de TeFacturo: nginx sirve tefacturo.ar desde /var/www/landing.
# Uso: tools/publish.sh [host-ssh]   (default: $TF_PUBLISH_HOST o tefacturo-prod, el alias de ~/.ssh/config)
# Antes: python3 tools/build_site.py. El host tiene que entrar como el usuario dueño de /var/www/landing.
set -euo pipefail
HOST="${1:-${TF_PUBLISH_HOST:-tefacturo-prod}}"
cd "$(dirname "$0")/.."
test -f docs/index.html || { echo "Falta docs/index.html: correr python3 tools/build_site.py" >&2; exit 1; }
rsync -az --delete --exclude .nojekyll docs/ "$HOST":/var/www/landing/
for url in https://tefacturo.ar/ https://tefacturo.ar/empezar/; do
  curl -sS -o /dev/null -w "$url -> %{http_code}\n" "$url" || true
done
