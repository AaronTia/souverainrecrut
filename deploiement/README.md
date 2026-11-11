# Déploiement – SouverainRecrut Backend (Jour 2)

Provisionnement et déploiement de l'API sur un serveur Ubuntu, **sans jamais reconstruire l'image** : le serveur tire
l'image publiée sur Docker Hub par Jenkins (`aarontiavin/souverainrecrut-backend:<version>-<sha7>`).

```
Docker Hub (image publiée par Jenkins)
        │ docker pull
        ▼
GitLab CI ── validate-tag ──► deploy-production (approbation manuelle) ──► smoke-test      rollback-production (manuel)
        │ jobs exécutés par le GitLab Runner installé sur la VM
        ▼
VM Ubuntu (VMware) ── Docker Compose : backend + PostgreSQL (volume persistant)
        ▲
Terraform (contrôle + inventaire) ── Ansible (Docker, Compose, ufw, runner)
```

Dépôt GitLab dédié : `gitlab.com/WakakiVongola/souverainrecrut-deploy` (contient ce dossier à sa racine).
Procédures détaillées : [`../documentation/procedure-deploiement.md`](../documentation/procedure-deploiement.md) et
[`../documentation/procedure-rollback.md`](../documentation/procedure-rollback.md).

## Contenu

| Dossier / fichier | Rôle |
|---|---|
| [`terraform/`](terraform/) | `providers.tf`, `main.tf`, `variables.tf`, `outputs.tf` : vérifie le serveur par SSH et génère l'inventaire Ansible. Voir [`terraform/README.md`](terraform/README.md) (pourquoi pas de `vsphere`). |
| [`ansible/`](ansible/) | `inventory.ini`, `playbook.yml` (mise à jour du système, Docker Engine + Compose, ufw, répertoire de déploiement, GitLab Runner), `run-ansible.ps1` (exécution en conteneur depuis Windows). |
| [`deployment/`](deployment/) | `docker-compose.yml` (backend, PostgreSQL, migrations), `.env.example`, `deploy.sh`, `rollback.sh`. |
| [`.gitlab-ci.yml`](.gitlab-ci.yml) | Pipeline : validation du tag, déploiement SSH approuvé manuellement, smoke test, rollback. |

## Prérequis

| Élément | Détail |
|---|---|
| Serveur | Ubuntu Server 22.04/24.04, 2 vCPU, 4 Go RAM, 30 Go, SSH actif, snapshot « post-install » |
| Poste | Docker Desktop (Ansible et Terraform tournent en conteneur), clé SSH dédiée `~/.ssh/souverainrecrut_deploy` |
| Docker Hub | tag publié par Jenkins ; jeton **lecture seule** facultatif (indispensable seulement si l'image devient privée) |
| GitLab | projet de déploiement, runner enregistré avec le tag `souverainrecrut-vm`, variables ci-dessous |

## Variables CI/CD GitLab

| Variable | Type | Protection | Rôle |
|---|---|---|---|
| `DEPLOY_HOST` | Variable | Protected | adresse du serveur |
| `DEPLOY_USER` | Variable | Protected | utilisateur SSH |
| `SSH_PRIVATE_KEY` | **File** | Protected | clé privée de déploiement (jamais en type Variable : elle s'afficherait dans un log en cas d'erreur) |
| `DOCKERHUB_USER` | Variable | Protected | compte Docker Hub |
| `DOCKERHUB_TOKEN` | Variable | Protected + **Masked** | **facultative** : si elle existe, `docker login` par l'entrée standard avant le pull ; non définie ici car l'image est publique |
| `POSTGRES_PASSWORD` | Variable | Protected + **Masked** | mot de passe de la base |
| `JWT_SECRET` | Variable | Protected + **Masked** | clé de signature des jetons |
| `IMAGE_TAG` / `PREVIOUS_TAG` | dans `.gitlab-ci.yml` | — | tag à déployer / tag de retour arrière, modifiables au lancement |

## Mise en route (dans l'ordre)

```bash
# 1. Terraform : contrôle du serveur + inventaire (dans le conteneur officiel)
cd terraform && cp terraform.tfvars.example terraform.tfvars          # adapter vm_ip, ssh_user
TF() { docker run --rm -v "$PWD:/tf" -v "$HOME/.ssh/souverainrecrut_deploy:/keys/deploy_key:ro" -w /tf hashicorp/terraform:latest "$@"; }
TF init && TF validate && TF plan && TF apply

# 2. Ansible : configuration du serveur (simulation puis application)
powershell -ExecutionPolicy Bypass -File .\ansible\run-ansible.ps1 --nopass --check --diff
powershell -ExecutionPolicy Bypass -File .\ansible\run-ansible.ps1 --nopass

# 3. Enregistrer le runner sur le serveur (jeton glrt-… fourni par GitLab, jamais commité)
sudo gitlab-runner register --url https://gitlab.com --token <glrt-…> --executor shell --description souverainrecrut-vm

# 4. GitLab : Build > Pipelines > New pipeline, puis approuver deploy-production (▶)
```

## Ce que fait le déploiement

1. `validate-tag` : format `X.Y.Z-sha7` (jamais `latest`) et existence du tag sur Docker Hub.
2. `deploy-production` (manuel) : copie compose et scripts en SSH, reconstruit `.env` (mode 0600) depuis les variables,
   `docker login` si un jeton est défini, puis `deploy.sh` : mémorise le tag courant, `docker pull`, extrait `prisma/` **de l'image**,
   `prisma migrate deploy` (cache npm persistant : 13 s), démarre l'API et attend `/v1/ready` = `READY`. `docker logout` en fin de job.
3. `smoke-test` : `/v1/health`, `/v1/ready`, `docker compose ps`, image en production = tag demandé.
4. `rollback-production` (manuel) : `rollback.sh $PREVIOUS_TAG`, testé sur 723d0f4 → 12a585b → 723d0f4.

## Sécurité

- Aucun secret dans ce dossier : `.env`, `*.tfvars`, `*.tfstate`, `.terraform/` et `prisma/` extrait sont ignorés par Git.
- Pare-feu `ufw` en *deny* par défaut : seuls 22 (SSH) et 4000 (API) sont ouverts ; PostgreSQL n'est pas publié sur l'hôte.
- Clé SSH dédiée au déploiement, distincte de la clé personnelle.
