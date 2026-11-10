# Cahier des charges local – SouverainRecrut CI/CD (M2, 2 jours)

Suivi des **exigences** et des **livrables** du projet fil rouge, dérivé du cahier des charges officiel
(`docs/leçon/Cahier_des_charges_SouverainRecrut_CICD_M2.pdf`) et des cours Jour 1 / Jour 2.
Ce fichier est la source de vérité locale : il est mis à jour à chaque étape franchie.

Légende : ✅ fait · ⏳ en cours · ⬜ à faire · ⚠️ partiel / à compléter

Dépôt de référence : `github.com/Santoudllo/souverainrecrut` · branche de travail : `Dev`
Formateur : Alimou Diallo · RNCP 40166 · Blocs 4 (E46) et 5 (E52)

---

## 1. Périmètre et contraintes

| Contrainte | Détail |
|---|---|
| Périmètre | **Backend uniquement** (Node.js 22+, Express, TypeScript, Prisma, PostgreSQL). Frontend React exclu. |
| Code applicatif | `backend/src/` **non modifié** : seuls CI/CD, tests, Dockerfile et docs sont adaptés. |
| Secrets | Jamais dans Git, jamais dans les logs, jamais en ARG/ENV du Dockerfile. Credentials Jenkins / variables GitLab masquées. |
| Traçabilité | Image taguée `version-sha` reliée à un commit précis. |
| Image déployée | Le Jour 2 fait **`docker pull`** de l'image publiée par Jenkins, jamais de rebuild depuis les sources. |

## 2. Architecture cible

```
JOUR 1 – Intégration & publication            JOUR 2 – Provisionnement & déploiement
GitHub (Dev) -> Jenkins -> Tests Jest          VMware / Ubuntu Server 24.04
             -> SonarQube + Quality Gate       -> Terraform (selon environnement)
             -> docker build + Trivy           -> Ansible (Docker, Compose, répertoire)
             -> Docker Hub (image versionnée)  -> GitLab CI/CD -> docker pull -> Compose + PostgreSQL
```

---

## 3. Exigences de qualité et de sécurité (§7 du cahier)

| # | Exigence | Attendu | Preuve | État |
|---|---|---|---|---|
| E1 | Reproductibilité | Build, config et déploiement décrits et rejouables | `docs/devops/README-pipeline.md` ✅ · README déploiement ⬜ | ⚠️ J1 fait, J2 à faire |
| E2 | Qualité logicielle | Tests exécutés, couverture et SonarQube consultables | `junit.xml`, `lcov`, Quality Gate PASSED | ✅ |
| E3 | Sécurité | Secrets protégés, image scannée Trivy | Credentials Jenkins, `reports/trivy-image.txt` | ✅ (0 CRITICAL) |
| E4 | Traçabilité | Tag explicite relié au code | `souverainrecrut-backend:1.0.0-<sha>` | ✅ |
| E5 | Déploiement | Le serveur récupère l'image et l'API démarre avec PostgreSQL | `docker compose ps`, endpoint `/health` | ⬜ |
| E6 | Continuité | Procédure de rollback documentée et testée | `procedure-rollback.md` + scénario joué | ⬜ |
| E7 | Documentation | Choix techniques, prérequis, procédures expliqués | README pipeline + runbook ✅ · `documentation/` J2 ⬜ | ⚠️ |

---

## 4. Livrables Jour 1 – Intégration continue (§3 du cahier, Bloc 4)

| # | Livrable | Emplacement | État | Notes |
|---|---|---|---|---|
| J1-01 | Fork + clone, branche `Dev`, `npm ci`, `npx prisma generate` | — | ✅ | |
| J1-02 | Framework de tests configuré (ts-jest, supertest, jest-mock-extended, jest-junit) | `backend/jest.config.js`, `tsconfig.test.json` | ✅ | Seuil couverture 100 % (global) |
| J1-03 | Tests auth, candidats, offres, candidatures, contrôle d'accès | `backend/tests/unit/`, `backend/tests/integration/` | ✅ | Prisma mocké (`tests/setup/prisma-mock.ts`) |
| J1-04 | Rapport de couverture exploitable (lcov + junit) | `backend/coverage/`, `junit.xml` | ✅ | Généré par le pipeline |
| J1-05 | Configuration SonarQube | `backend/sonar-project.properties` | ✅ | `src/docs/` exclu (Swagger) |
| J1-06 | Quality Gate PASSED | SonarQube `http://localhost:9000` | ✅ | Webhook → Jenkins OK |
| J1-07 | Jenkins installé avec Docker, Node 22, Trivy, plugins | `docker/jenkins/Dockerfile`, `docker/docker-compose.yml` | ✅ | |
| J1-08 | Credentials Jenkins : `sonar-token` | Jenkins → Credentials | ✅ | |
| J1-09 | Credentials Jenkins : `dockerhub` (user + PAT Read&Write) | Jenkins → Credentials | ✅ | `aarontiavin/******` – capture 09 |
| J1-10 | Jenkinsfile : checkout Dev → deps → Prisma → tests → Sonar + QG → build → Trivy → push conditionnel | `Jenkinsfile` | ✅ | Poll SCM `H/5 * * * *` |
| J1-11 | Dockerfile vérifié/adapté (multi-stage, `node:22-alpine`, user `node`, sans npm) | `backend/Dockerfile`, `backend/.dockerignore` | ✅ | |
| J1-12 | Tag explicite version + commit | `1.0.0-<sha>` | ✅ | |
| J1-13 | Scan Trivy avec seuils définis | Stage `Scan Trivy` | ✅ | CRITICAL+fix bloquant, HIGH reportés |
| J1-14 | Image publiée sur Docker Hub | `hub.docker.com/r/aarontiavin/souverainrecrut-backend` | ✅ | Build #9 → tag `1.0.0-12a585b`, digest `sha256:5c9992b3…` – capture 07 |
| J1-15 | README du pipeline (prérequis, variables, déclencheurs, schéma) | `docs/devops/README-pipeline.md` | ✅ | Schéma, prérequis, credentials, variables, stages, seuils, choix |
| J1-16 | Runbook « quoi faire quand une étape échoue » | `docs/devops/etapes-bloquantes.md` | ✅ | 11 incidents documentés |
| J1-17 | Rapports archivés (tests, couverture, Sonar, Trivy) | `docs/devops/reports/` | ✅ | junit-result.xml, lcov.info, trivy-image.txt, console build #9 (+ README) |
| J1-18 | Captures : build vert, Quality Gate, Trivy, image Docker Hub | `docs/devops/captures/` | ✅ | 11 captures (Jenkins ×5, SonarQube ×3, Docker Hub, webhook, Redocly) |
| J1-19 | Documentation API générée par le pipeline (cours J1 slide 18) | `backend/scripts/export-openapi.ts`, stage *Docs API*, `reports/openapi.json` + `api-docs.html` | ✅ | Équivalent Node du `redocly build-docs` ; à confirmer sur le prochain build Jenkins |

**Résultat attendu J1** : Jenkinsfile opérationnel, tests exécutables, couverture, résultats Sonar et Trivy, image versionnée publiée sur Docker Hub.

**État au 10/11/2026 : J1 complet (19/19)** – build de référence Jenkins #9 sur `12a585b`. Reste pour le livrable final : recopier `Jenkinsfile`, `backend/Dockerfile`, `sonar-project.properties`, `docs/devops/reports/` et `README-pipeline.md` dans `integration-continue/`.

---

## 5. Livrables Jour 2 – Provisionnement et déploiement (§4–5 du cahier, Bloc 5)

### 5.1 Infrastructure

| # | Livrable | Emplacement | État | Notes |
|---|---|---|---|---|
| J2-01 | VM Ubuntu Server 24.04 (2 vCPU, 4 Go, 30 Go, NAT/Bridged, SSH) | VMware | ⬜ | |
| J2-02 | IP, accès Internet et SSH vérifiés | — | ⬜ | |
| J2-03 | Snapshot avant configuration | VMware | ⬜ | |
| J2-04 | Terraform : `main.tf`, `variables.tf`, `outputs.tf`, `providers.tf` | `deploiement/terraform/` | ⬜ | Sans ESXi/vCenter : VM manuelle, Terraform sur ressources disponibles – **justifier** |
| J2-05 | `terraform init / validate / plan / apply` joués | — | ⬜ | `terraform.tfvars` et `*.tfstate` hors Git |

### 5.2 Configuration serveur

| # | Livrable | Emplacement | État | Notes |
|---|---|---|---|---|
| J2-06 | Inventaire SSH | `deploiement/ansible/inventory.ini` | ⬜ | |
| J2-07 | Playbook : update système, Docker Engine + Compose plugin, service activé, répertoire de déploiement, vérification | `deploiement/ansible/playbook.yml` | ⬜ | Idempotent ; `--check --diff` avant apply |
| J2-08 | Secrets Ansible protégés (Vault ou variables CI) | — | ⬜ | |

### 5.3 Déploiement applicatif

| # | Livrable | Emplacement | État | Notes |
|---|---|---|---|---|
| J2-09 | `docker-compose.yml` : backend (image Docker Hub taguée) + PostgreSQL, volume persistant, réseau, `restart`, healthchecks | `deploiement/deployment/docker-compose.yml` | ⬜ | Pas de `latest` |
| J2-10 | `.env.example` (variables API + Prisma) | `deploiement/deployment/.env.example` | ⬜ | Le `.env` réel reste hors Git |
| J2-11 | Stratégie de migrations Prisma maîtrisée | compose / script | ⬜ | Penser à la réversibilité du schéma |
| J2-12 | Projet GitLab dédié au déploiement | GitLab | ⬜ | |
| J2-13 | Variables CI/CD GitLab masquées : Docker Hub user/token, hôte, user SSH, clé privée, `IMAGE_TAG` | GitLab → Settings → CI/CD | ⬜ | |
| J2-14 | `.gitlab-ci.yml` : valider le tag → SSH → transférer fichiers → `docker compose pull` → `up -d` → vérifier `ps` + API | `deploiement/.gitlab-ci.yml` | ⬜ | |
| J2-15 | Approbation manuelle avant production (`when: manual`, environnement protégé) | `.gitlab-ci.yml` | ⬜ | Trace : qui, quand, quelle version |

### 5.4 Validation et rollback

| # | Livrable | Emplacement | État | Notes |
|---|---|---|---|---|
| J2-16 | Vérification API (health + endpoints principaux) | script smoke-test | ⬜ | |
| J2-17 | Vérification backend ↔ PostgreSQL et persistance | — | ⬜ | Redémarrer et vérifier les données |
| J2-18 | Version précédente identifiée + retour documenté | `procedure-rollback.md` | ⬜ | Conserver `PREVIOUS_TAG` |
| J2-19 | Rollback testé sur un scénario maîtrisé | captures / logs | ⬜ | |

### 5.5 Options vues en cours (bonus, non exigées par le cahier)

| # | Livrable | État | Notes |
|---|---|---|---|
| J2-20 | SBOM (`syft`) archivé par le pipeline | ⬜ | Critère go/no-go du cours J2 |
| J2-21 | Signature d'image (`cosign`) | ⬜ | |
| J2-22 | Métriques DORA dans le rapport final | ⬜ | Fréquence, délai, taux d'échec, temps de restauration |

**Résultat attendu J2** : API accessible sur le serveur, déployée depuis une image Docker Hub identifiée, avec procédure de vérification et de retour arrière documentée.

---

## 6. Documentation à remettre (§6 du cahier)

| Fichier | Contenu | État |
|---|---|---|
| `integration-continue/README.md` | Prérequis, variables, déclencheurs, schéma du pipeline Jenkins | ✅ (`docs/devops/README-pipeline.md`, à copier dans l'arborescence finale) |
| `deploiement/README.md` | Prérequis VM, Terraform, Ansible, GitLab, variables | ⬜ |
| `documentation/architecture.md` | Schéma complet, rôle de chaque outil, flux commit → prod | ⬜ |
| `documentation/procedure-deploiement.md` | Étapes reproductibles par un tiers | ⬜ |
| `documentation/procedure-rollback.md` | Retour arrière + limites (migrations) | ⬜ |
| `documentation/rapport-final.md` | Choix justifiés, preuves, argumentaire MSPR 4.1 / 5.1, métriques | ⬜ |
| Runbook | `docs/devops/etapes-bloquantes.md` | ✅ |

## 7. Arborescence cible du livrable

```
SouverainRecrut-CICD/
├── integration-continue/
│   ├── Jenkinsfile
│   ├── Dockerfile
│   ├── sonar/
│   ├── reports/
│   └── README.md
├── deploiement/
│   ├── terraform/
│   ├── ansible/
│   ├── deployment/
│   │   ├── docker-compose.yml
│   │   └── .env.example
│   ├── .gitlab-ci.yml
│   └── README.md
└── documentation/
    ├── architecture.md
    ├── procedure-deploiement.md
    ├── procedure-rollback.md
    └── rapport-final.md
```

Remise : archive ZIP ou lien du dépôt GitHub/GitLab, **sans aucun secret** (`.env` réels, tokens, clés privées, `tfstate`).

---

## 8. Choix techniques assumés (à justifier dans le rapport)

- `src/docs/` (Swagger) exclu de SonarQube : doublons acceptés, duplication ~0 % sur le code métier.
- Déclenchement Jenkins par Poll SCM plutôt que webhook GitHub : Jenkins local non joignable depuis Internet.
- Seuil Trivy : seules les CRITICAL corrigeables bloquent ; les HIGH sont reportées.
- `SONAR_VALIDATEWEBHOOKS=false` : acceptable en local uniquement.
- Image `node:22-alpine` sans npm, utilisateur `node` : réduction de la surface d'attaque.
- Terraform : *(à compléter le Jour 2 selon l'environnement VMware disponible)*.

## 9. Critères go / no-go pour le jury

- [x] Quality Gate au vert
- [ ] Image taguée publiée et déployée telle quelle (même artefact partout)
- [ ] Tests de validation réussis après déploiement
- [ ] Procédure de rollback testée
- [ ] Approbation manuelle tracée
- [ ] Runbook et documentation à jour
- [x] Aucun secret dans le dépôt
- [ ] Démo du chemin complet : modification du code → image → API déployée
