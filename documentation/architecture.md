# Architecture – chaîne CI/CD SouverainRecrut (backend)

Périmètre : API Backend (Node.js 22, Express, TypeScript, Prisma) et sa base PostgreSQL. Le frontend est exclu.

## Vue d'ensemble

```
                    JOUR 1 – Intégration et publication (poste de développement, Docker Desktop)
┌────────┐ commit  ┌─────────┐   ┌───────────┐   ┌──────────┐   ┌───────┐   ┌────────────┐
│ GitHub │ ──────► │ Jenkins │──►│ Tests Jest│──►│ SonarQube│──►│ Trivy │──►│ Docker Hub │
│ (Dev)  │ Poll SCM│         │   │ 151 tests │   │ Q. Gate  │   │ image │   │ image :    │
└────────┘  5 min  └─────────┘   │ couverture│   └──────────┘   └───────┘   │ 1.0.0-<sha>│
                                 └───────────┘                              └─────┬──────┘
                                                                                  │ docker pull
                    JOUR 2 – Provisionnement et déploiement                        ▼
┌─────────────┐ pipeline ┌────────────────┐  SSH   ┌──────────────────────────────────────┐
│  GitLab     │ ───────► │ GitLab Runner  │ ─────► │ VM Ubuntu (VMware Workstation)       │
│ projet      │ approbation│ (sur la VM)  │        │  Docker Compose                      │
│ deploy      │ manuelle └────────────────┘        │  ├─ backend  (image Docker Hub)      │
└─────────────┘                                    │  └─ postgres (volume persistant)     │
      ▲                                            └──────────────────────────────────────┘
      │ configure                                   ▲                    ▲
 ┌────┴──────┐ génère l'inventaire / vérifie        │ installe Docker    │ API :4000
 │ Terraform │ ─────────────────────────────────────┘ ┌──────────┐       │
 └───────────┘                                        │ Ansible  │───────┘
                                                      └──────────┘
```

## Rôle de chaque outil

| Outil | Rôle | Pourquoi ce choix |
|---|---|---|
| **GitHub** | Dépôt du code (fork, branche `Dev`) | imposé par le cahier ; Jenkins le scrute (Poll SCM) |
| **Jenkins** | Orchestre build, tests, qualité, image, scan, publication | *pipeline as code* (`Jenkinsfile`), plugins SonarQube/Docker |
| **SonarQube** | Analyse statique + **Quality Gate** bloquant | barrière automatique avant tout artefact |
| **Trivy** | Scan de l'image (CRITICAL corrigeables bloquants) | sécurité de la chaîne d'approvisionnement |
| **Docker Hub** | Registre : image versionnée `X.Y.Z-<sha7>` | l'artefact testé est celui déployé |
| **Terraform** | Vérifie le serveur et génère l'inventaire Ansible | VM créée à la main (Workstation sans ESXi) ; voir limite ci-dessous |
| **Ansible** | Configure le serveur : Docker, Compose, pare-feu, runner | idempotent, sans agent |
| **GitLab CI/CD** | Déploie sur le serveur, approbation manuelle, rollback | imposé par le cahier ; projet séparé du code (multi-dépôt) |
| **Docker Compose** | Orchestre backend + PostgreSQL | volume, healthchecks, redémarrage automatique |

## Séparation des dépôts (multi-repo)

- **GitHub `AaronTia/souverainrecrut`** : code, tests, `Jenkinsfile`, `Dockerfile`. Produit **l'image**.
- **GitLab `WakakiVongola/souverainrecrut-deploy`** : `deploiement/` uniquement (Ansible, Compose, Terraform, `.gitlab-ci.yml`). **Consomme** l'image sans jamais la reconstruire.

Le seul lien entre les deux est le **tag de l'image**, validé par le job `validate-tag` (format `X.Y.Z-sha7` + existence sur Docker Hub).

## Traçabilité commit → production

| Maillon | Valeur du déploiement de référence |
|---|---|
| Commit GitHub | `723d0f4` |
| Build Jenkins | #11, Quality Gate *Passed*, 151 tests, Trivy 0 CRITICAL |
| Tag Docker Hub | `aarontiavin/souverainrecrut-backend:1.0.0-723d0f4` |
| Digest publié par Jenkins | `sha256:0b9848d00e9d21685eb0419dc9ccfe2a29a06fa18a26f0b86f7f034ed4e7773a` |
| Digest en production sur la VM | `sha256:0b9848d00e9d21685eb0419dc9ccfe2a29a06fa18a26f0b86f7f034ed4e7773a` ✅ identique |

## Sécurité

- **Secrets** : credentials Jenkins ; variables GitLab masquées ; `.env` du serveur en `0600`, reconstruit par le pipeline, jamais commité. Gitignore sur `.env`, `*.tfvars`, `*.tfstate`, clés.
- **Image** : multi-stage, `node:22-alpine`, utilisateur non-root, sans npm/yarn dans l'image finale.
- **Réseau serveur** : pare-feu `ufw` en *deny* par défaut, seuls 22 et 4000 ouverts ; PostgreSQL n'est **pas** publié sur l'hôte (réseau Docker interne).
- **Accès** : clé SSH dédiée (ed25519) distincte de la clé personnelle ; `sudo` sans mot de passe limité à l'utilisateur de déploiement.
- **Production** : déploiement et rollback en `when: manual` (approbation tracée par GitLab : qui, quand, quelle version).

## Limites assumées

- **Terraform** : pas d'ESXi/vCenter, donc pas de ressource `vsphere_virtual_machine`. Terraform génère l'inventaire et contrôle l'état du serveur.
- **Ubuntu 22.04** au lieu de 24.04 (VM mise à disposition) : sans impact sur Docker, Compose ou Ansible.
- **Prisma mocké** dans les tests : contraintes SQL non exercées en CI ; voir `documentation/rapport-final.md` (défauts connus).
- **Pas de HTTPS** : l'API est exposée en HTTP sur le réseau local ; en production réelle, ajouter un reverse proxy TLS (Nginx/Traefik).
