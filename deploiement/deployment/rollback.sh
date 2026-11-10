#!/usr/bin/env bash
# Retour à la version précédente (tag sauvegardé par deploy.sh) ou à un tag donné.
#   ./rollback.sh                 # utilise .previous_tag
#   ./rollback.sh 1.0.0-12a585b
#
# Limite : le rollback applicatif ne défait pas les migrations de schéma ;
# les migrations Prisma doivent rester compatibles avec la version N-1.
set -euo pipefail
cd "$(dirname "$0")"

tag="${1:-$(cat .previous_tag 2>/dev/null || true)}"
[ -n "$tag" ] || { echo "ERREUR : aucun tag précédent connu, passer le tag en argument"; exit 1; }

echo "==> Rollback vers $tag"
IMAGE_TAG="$tag" ./deploy.sh
