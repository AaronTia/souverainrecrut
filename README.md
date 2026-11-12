# SouverainRecrut

Plateforme web de gestion des recrutements : candidats, offres d'emploi, suivi des candidatures.

Ce dépôt est le projet fil rouge du module **CI/CD** (Mastère RNCP 40166, Sup de Vinci Rennes). Le périmètre industrialisé est l'**API backend** : de chaque commit à la mise en production, avec approbation humaine et retour arrière testé.

| Qualité | Sécurité | Livraison |
|---|---|---|
| 151 tests, 99,4 % de couverture | 0 vulnérabilité critique corrigeable dans l'image | Image identique (même digest) de Jenkins à la production |
| Quality Gate SonarQube validée | Secrets hors dépôt, déploiement soumis à approbation | Rollback testé, données conservées |

## Architecture applicative

```
Frontend (React) ──► API REST (Express, Prisma) ──► PostgreSQL
```

Stack : React, TypeScript, Vite, Material UI · Node.js 22, Express, Prisma, PostgreSQL · Jest · Docker, Jenkins, SonarQube, Trivy, GitLab CI, Terraform, Ansible.

## Chaîne CI/CD

```
GitHub (Dev) ─► Jenkins ─► Tests ─► SonarQube ─► Trivy ─► Docker Hub
                                                             │ même image
GitLab CI (approbation manuelle) ─► VM Ubuntu : Docker Compose (API + PostgreSQL)
                                    provisionnée par Terraform + Ansible
```

- **Jour 1, intégration continue** : tests, analyse qualité, scan de sécurité, publication de l'image.
- **Jour 2, déploiement** : provisionnement, déploiement approuvé, smoke test, rollback.

## Structure du dépôt

| Dossier | Contenu |
|---|---|
| `backend/` | API Express/TypeScript, schéma Prisma, tests Jest, `Dockerfile` |
| `frontend/` | Application React |
| `Jenkinsfile`, `docker/` | Pipeline d'intégration continue et stack locale (Jenkins, SonarQube) |
| `deploiement/` | Terraform, Ansible, Docker Compose et pipeline GitLab de déploiement |
| `documentation/` | Rapport final, architecture, procédures de déploiement et de rollback |
| `docs/` | Documentation du pipeline CI, preuves d'exécution (captures, rapports), supports de cours |
| `livrable/` | Script d'assemblage de l'archive de rendu |

## Documentation

**Vue d'ensemble**
- [Rapport final (PDF illustré, 27 pages)](documentation/rapport/rapport-final.pdf), version texte : [rapport-final.md](documentation/rapport-final.md)
- [Architecture de la chaîne CI/CD](documentation/architecture.md)

**Intégration continue**
- [Pipeline Jenkins : mise en place et fonctionnement](docs/devops/README-pipeline.md)
- [Étapes bloquantes et runbook](docs/devops/etapes-bloquantes.md)
- Preuves d'exécution : [captures](docs/devops/captures/) et [rapports](docs/devops/reports/)

**Déploiement et exploitation**
- [Provisionnement et déploiement](deploiement/README.md)
- [Procédure de déploiement](documentation/procedure-deploiement.md)
- [Procédure de rollback](documentation/procedure-rollback.md)

**Cadrage**
- [Cahier des charges](docs/devops/cahier-des-charges-local.md)

## Démarrage

```bash
# API en développement
cd backend && npm install && npm run dev

# Tests et couverture
cd backend && npm test

# Stack d'intégration continue locale (Jenkins, SonarQube)
cd docker && docker compose up -d --build
```

Archive de rendu, avec contrôle automatique d'absence de secrets :

```bash
python livrable/assembler-livrable.py   # produit livrable/SouverainRecrut-CICD.zip
```

## Auteurs

Joan Carpentier · Aaron Tiavinjanahary. Formateur : Alimou Diallo.
