#!/usr/bin/env bash
# Déploie (ou met à jour) SouverainRecrut sur ce serveur à partir de l'image Docker Hub.
#
#   ./deploy.sh                 # tag défini dans .env
#   IMAGE_TAG=1.0.0-abc1234 ./deploy.sh
#
# Étapes : pull de l'image -> extraction des migrations Prisma de cette image
# -> migrate deploy -> up -d -> vérification /v1/ready. Le tag précédent est
# conservé dans .previous_tag pour rollback.sh.
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] || { echo "ERREUR : .env absent (copier .env.example)"; exit 1; }
# Un IMAGE_TAG passé dans l'environnement (rollback.sh, GitLab CI) prime sur celui du .env
REQUESTED_TAG="${IMAGE_TAG:-}"
set -a; . ./.env; set +a
IMAGE_TAG="${REQUESTED_TAG:-${IMAGE_TAG:?IMAGE_TAG manquant}}"
IMAGE="${DOCKERHUB_USER}/souverainrecrut-backend:${IMAGE_TAG}"

current="$(docker inspect --format '{{ index .Config.Image }}' souverainrecrut-backend 2>/dev/null || true)"
if [ -n "$current" ] && [ "$current" != "$IMAGE" ]; then
  echo "${current##*:}" > .previous_tag
  echo "Tag précédent sauvegardé : $(cat .previous_tag)"
fi

echo "==> Pull $IMAGE"
docker pull "$IMAGE"

echo "==> Extraction des migrations Prisma de l'image"
rm -rf prisma && tmp="$(docker create "$IMAGE")" && docker cp "$tmp:/app/prisma" ./prisma && docker rm "$tmp" >/dev/null
ls prisma/migrations

echo "==> Base de données"
IMAGE_TAG="$IMAGE_TAG" docker compose up -d db
IMAGE_TAG="$IMAGE_TAG" docker compose --profile migrate run --rm migrate

echo "==> Backend"
IMAGE_TAG="$IMAGE_TAG" docker compose up -d --remove-orphans backend
sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${IMAGE_TAG}/" .env

echo "==> Vérification"
for i in $(seq 1 20); do
  if wget -qO- "http://127.0.0.1:${BACKEND_PORT:-4000}/v1/ready" 2>/dev/null | grep -q '"READY"'; then
    docker compose ps
    echo "OK : $IMAGE déployée et prête."
    exit 0
  fi
  sleep 3
done
echo "ERREUR : l'API ne répond pas READY après 60 s"
docker compose logs --tail 50 backend
exit 1
