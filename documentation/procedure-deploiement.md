# Procédure de déploiement

Reproductible par un tiers. Durée : ~30 min la première fois, ~3 min pour une mise à jour.

## 0. Prérequis

| Élément | Détail |
|---|---|
| Image publiée | une image `aarontiavin/souverainrecrut-backend:X.Y.Z-sha7` produite par Jenkins (voir `integration-continue/README.md`) |
| VM | Ubuntu Server 22.04/24.04, 2 vCPU, 4 Go RAM, 30 Go, réseau joignable, SSH activé, snapshot « post-install » |
| Poste | Docker Desktop (pour exécuter Ansible et Terraform en conteneur), clé SSH dédiée |
| GitLab | projet privé `souverainrecrut-deploy`, runner enregistré (tag `souverainrecrut-vm`) |

## 1. Clé SSH de déploiement

```bash
ssh-keygen -t ed25519 -N "" -C souverainrecrut-deploy -f ~/.ssh/souverainrecrut_deploy
# installer la clé publique sur la VM (mot de passe demandé une seule fois)
cat ~/.ssh/souverainrecrut_deploy.pub | ssh <user>@<ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
# sudo sans mot de passe pour l'automatisation
ssh -t <user>@<ip> "echo '<user> ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/90-deploy && sudo chmod 440 /etc/sudoers.d/90-deploy"
```

## 2. Terraform – contrôle du serveur et inventaire

```bash
cd deploiement/terraform
cp terraform.tfvars.example terraform.tfvars      # adapter vm_ip et ssh_user
TF() { docker run --rm -v "$PWD:/tf" -v "$HOME/.ssh/souverainrecrut_deploy:/keys/deploy_key:ro" -w /tf hashicorp/terraform:latest "$@"; }
TF init && TF validate && TF plan && TF apply
```
Attendu : `Apply complete! Resources: 2 added` et la sortie du contrôle (Docker actif, ≥ 5 Go libres).

## 3. Ansible – préparation du serveur

```powershell
powershell -ExecutionPolicy Bypass -File .\deploiement\ansible\run-ansible.ps1 --nopass --check --diff   # simulation
powershell -ExecutionPolicy Bypass -File .\deploiement\ansible\run-ansible.ps1 --nopass                  # application
```
Attendu : `failed=0`. Le serveur a Docker Engine, Compose, `ufw` (22 et 4000), `/opt/souverainrecrut` et GitLab Runner.
Le playbook est **idempotent** : un second passage ne modifie rien.

## 4. Enregistrer le runner GitLab (une fois)

GitLab → projet → *Settings → CI/CD → Runners → New project runner*, tag `souverainrecrut-vm`, executor `shell`.
Sur la VM : `sudo gitlab-runner register --url https://gitlab.com --token <glrt-…> --executor shell --description souverainrecrut-vm`.

## 5. Variables CI/CD (GitLab → Settings → CI/CD → Variables)

| Variable | Type / options |
|---|---|
| `DEPLOY_HOST`, `DEPLOY_USER`, `DOCKERHUB_USER` | variable simple |
| `SSH_PRIVATE_KEY` | type **File**, *Protect* |
| `POSTGRES_PASSWORD`, `JWT_SECRET` | **Masked** (≥ 8 car., JWT ≥ 32) |

## 6. Déployer

**Via GitLab (nominal)** : *Build → Pipelines → Run pipeline*, renseigner `IMAGE_TAG` (ex. `1.0.0-723d0f4`).
1. `validate-tag` (automatique) : format du tag + existence sur Docker Hub.
2. `deploy-production` : **cliquer sur ▶ pour approuver** (trace : qui, quand, quelle version).
3. `smoke-test` (automatique) : `/v1/health`, `/v1/ready`, `docker compose ps`, image en production = tag demandé.

**À la main (dépannage)** :
```bash
scp deploiement/deployment/{docker-compose.yml,deploy.sh,rollback.sh} <user>@<ip>:/opt/souverainrecrut/
ssh <user>@<ip> "cd /opt/souverainrecrut && cp .env.example .env && nano .env && ./deploy.sh"
```

## 7. Ce que fait `deploy.sh`

1. mémorise le tag en cours dans `.previous_tag` (pour le rollback) ;
2. `docker pull` de l'image du tag demandé — **jamais de build** ;
3. extrait `/app/prisma` **de l'image** (les migrations correspondent à la version déployée) ;
4. démarre PostgreSQL puis exécute `prisma migrate deploy` dans un conteneur éphémère (la CLI Prisma n'est pas embarquée dans l'image de production) ;
5. démarre le backend et attend `/v1/ready` = `READY` (60 s max, sinon logs + échec).

## 8. Vérifications après déploiement

```bash
curl -s http://<ip>:4000/v1/health         # {"status":"UP"}
curl -s http://<ip>:4000/v1/ready          # {"status":"READY","database":"CONNECTED"}
curl -s -o /dev/null -w "%{http_code}\n" http://<ip>:4000/v1/candidates   # 401 sans token
ssh <user>@<ip> "cd /opt/souverainrecrut && docker compose ps && docker inspect --format '{{.Image}}' souverainrecrut-backend"
```
Comparer le digest affiché au digest du build Jenkins (`Console Output`, ligne `digest: sha256:…`).
