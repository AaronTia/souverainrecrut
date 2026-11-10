# README du pipeline CI – SouverainRecrut Backend

Chaîne d'intégration continue du **Jour 1** : à chaque commit sur la branche `Dev`, le backend est testé, analysé, conteneurisé, scanné puis publié sur Docker Hub.

```
GitHub (Dev) ──Poll SCM──► Jenkins ──► Tests Jest (127, couverture 100 %)
                                   ──► Docs API (OpenAPI → Redocly HTML)
                                   ──► SonarQube + Quality Gate (webhook)
                                   ──► docker build  backend/Dockerfile
                                   ──► Trivy (CRITICAL corrigeable = bloquant)
                                   ──► docker push  aarontiavin/souverainrecrut-backend:<version>-<sha>
```

Preuves d'exécution (build #9, commit `12a585b`) : [captures/](captures/) · [reports/](reports/) · runbook : [etapes-bloquantes.md](etapes-bloquantes.md).

---

## 1. Prérequis

| Poste de travail | Comptes |
|---|---|
| Docker Desktop (Compose v2) | GitHub : fork `AaronTia/souverainrecrut`, branche `Dev` |
| Git, Node.js 22+ (pour lancer les tests en local) | Docker Hub : compte `aarontiavin` + Personal Access Token **Read & Write** |
| ~6 Go de RAM libres (Jenkins + SonarQube + PostgreSQL) | — |

## 2. Démarrer la stack CI locale

```bash
cd docker
docker compose up -d --build
```

| Service | URL | Image | Rôle |
|---|---|---|---|
| `jenkins` | http://localhost:8080 | `docker/jenkins/Dockerfile` (LTS JDK 17 + docker CLI, Node 22, Trivy, plugins) | Orchestrateur |
| `sonarqube` | http://localhost:9000 | `sonarqube:community` | Analyse statique + Quality Gate |
| `sonar-db` | interne | `postgres:16-alpine` | Base de SonarQube |

Mot de passe initial Jenkins : `docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword`.
SonarQube : `admin / admin` puis changement obligatoire.

Le socket Docker de l'hôte est monté dans Jenkins (`/var/run/docker.sock`) : les images du projet sont construites par le démon de l'hôte, pas en Docker-in-Docker.

## 3. Configuration Jenkins (une seule fois)

### 3.1 Plugins
Plugins suggérés à l'installation (Git, Pipeline, Credentials Binding, JUnit, Timestamper) + ceux ajoutés par `docker/jenkins/Dockerfile` : `sonar`, `docker-workflow`, `ansicolor`.

### 3.2 Credentials (Administrer Jenkins → Credentials → System → Global)

| ID | Type | Contenu | Utilisé par |
|---|---|---|---|
| `sonar-token` | Secret text | Token d'analyse généré dans SonarQube (*My Account → Security*) | serveur SonarQube `sonar` → `withSonarQubeEnv` |
| `dockerhub` | Username / Password | identifiant Docker Hub + Access Token | stage *Push Docker Hub* (`withCredentials`) |

Aucun secret n'est présent dans le dépôt : ils sont injectés en variables d'environnement masquées dans les logs.

### 3.3 Serveur SonarQube (Administrer Jenkins → System → SonarQube servers)
- Nom : **`sonar`** (doit correspondre à `withSonarQubeEnv('sonar')`)
- URL : `http://sonarqube:9000` (nom du service sur le réseau Compose)
- Token : `sonar-token`

### 3.4 Webhook SonarQube → Jenkins (SonarQube → Administration → Webhooks)
- Nom `Jenkins`, URL `http://jenkins:8080/sonarqube-webhook/`
- `SONAR_VALIDATEWEBHOOKS=false` dans `docker-compose.yml` pour autoriser une adresse de réseau privé (local uniquement).

### 3.5 Job
- Type **Pipeline**, nom `souverainrecrut-backend`
- *Pipeline script from SCM* → Git `https://github.com/AaronTia/souverainrecrut.git`, branche `*/Dev`, script `Jenkinsfile`
- Déclencheur : **Poll SCM** `H/5 * * * *` (Jenkins est local, GitHub ne peut pas le joindre par webhook)

## 4. Variables du pipeline

| Variable | Valeur | Origine |
|---|---|---|
| `IMAGE_NAME` / `LOCAL_IMAGE` | `souverainrecrut-backend` | `environment {}` du Jenkinsfile |
| `IMAGE_TAG` | `<version package.json>-<sha court>` ex. `1.0.0-12a585b` | calculé au stage Checkout |
| `TRIVY_CACHE` | `/var/jenkins_home/.cache/trivy` | base de vulnérabilités persistée |
| `CI=true`, `DOTENV_CONFIG_QUIET=true` | — | mode CI de Jest, logs dotenv silencieux |
| `SONAR_HOST_URL`, `SONAR_AUTH_TOKEN` | injectées | `withSonarQubeEnv('sonar')` |
| `DH_USER`, `DH_TOKEN` | injectées | credential `dockerhub` |

Paramètres SonarQube : `backend/sonar-project.properties` (clé `souverainrecrut-backend`, sources `src`, tests `tests`, exclusion `src/docs/**`, couverture `coverage/lcov.info`).

## 5. Stages du Jenkinsfile

| # | Stage | Commande clé | Échec si… | Durée (#9) |
|---|---|---|---|---|
| 1 | Checkout | `checkout scm` + calcul `IMAGE_TAG` | dépôt injoignable | 2 s |
| 2 | Install | `npm ci` | lockfile incohérent | 47 s |
| 3 | Prisma generate | `npx prisma generate` | schéma invalide | 1 s |
| 4 | Tests | `npm run test:ci` (Jest, `--coverage`, JUnit) | test rouge, ou couverture < 100 % sur middlewares/validators, < 90 % ailleurs | 15 s |
| 5 | Docs API | `npm run docs:api` : export de la spec swagger-jsdoc (`scripts/export-openapi.ts`) puis `@redocly/cli build-docs` | spec invalide | ~10 s |
| 6 | SonarQube | `npx @sonar/scan` | scanner en erreur | 53 s |
| 7 | Quality Gate | `waitForQualityGate abortPipeline: true` | Quality Gate ≠ PASSED (timeout 5 min) | 10 s |
| 8 | Build image | `docker build -t souverainrecrut-backend:$IMAGE_TAG backend/` | Dockerfile en erreur | 18 s |
| 9 | Scan Trivy | rapport HIGH+CRITICAL archivé, puis `--severity CRITICAL --ignore-unfixed --exit-code 1` | ≥ 1 CRITICAL corrigeable | 9 s |
| 10 | Push Docker Hub | `docker login --password-stdin` → `tag` → `push` | credential absent / refus du registre | 1 min 6 s |
| — | Post | `docker image rm` local, `docker logout` | — | — |

Options : `timeout 30 min`, `disableConcurrentBuilds`, conservation des 10 derniers builds, `ansiColor`, `timestamps`.

## 6. Artefacts et rapports produits

| Artefact | Produit par | Archivé dans Jenkins | Copie livrable |
|---|---|---|---|
| `backend/reports/junit.xml` | jest-junit | onglet *Résultats des tests* | [reports/junit-result.xml](reports/junit-result.xml) |
| `backend/coverage/lcov.info` | Jest | oui | [reports/lcov.info](reports/lcov.info) |
| `backend/reports/openapi.json` + `api-docs.html` | swagger-jsdoc + Redocly | oui | [reports/openapi.json](reports/openapi.json), [reports/api-docs.html](reports/api-docs.html) |
| Analyse SonarQube | scanner | http://localhost:9000/dashboard?id=souverainrecrut-backend | captures 05–06 |
| `reports/trivy-image.txt` | Trivy | oui | [reports/trivy-image.txt](reports/trivy-image.txt) |
| Image Docker | docker | — | `docker pull aarontiavin/souverainrecrut-backend:1.0.0-12a585b` |
| Console du build | Jenkins | oui | [reports/jenkins-build-9-console.log](reports/jenkins-build-9-console.log) |

## 7. Résultats du build de référence (#9, 9 nov. 2026)

| Contrôle | Résultat |
|---|---|
| Tests | 16 suites, **127 / 127** passés (depuis le 10/11 : 18 suites, 151 tests dont 8 `it.failing` documentant des défauts connus – voir cahier local §8 bis) |
| Couverture | **100 %** lignes / branches / fonctions (seuil Jest 100 %) |
| SonarQube | Quality Gate **Passed** · 1,5 k lignes · 0 nouveau problème · duplication 0,0 % |
| Trivy | **0 CRITICAL**, 16 HIGH (dépendances transitives, non bloquantes, listées dans le rapport) |
| Image | `aarontiavin/souverainrecrut-backend:1.0.0-12a585b` · digest `sha256:5c9992b3…` · 160 Mo compressés · linux/amd64 |

## 8. Lancer les contrôles à la main (sans Jenkins)

```bash
cd backend
npm ci && npx prisma generate
npm run test:ci                              # tests + coverage/ + reports/junit.xml
npm run docs:api                             # reports/openapi.json + reports/api-docs.html
docker build -t souverainrecrut-backend:dev .
trivy image --severity HIGH,CRITICAL souverainrecrut-backend:dev
```

## 9. Choix techniques

- **Tag `version-sha`** : traçabilité commit → image, pas de `latest`.
- **Seuil Trivy** : bloquer uniquement les CRITICAL avec correctif disponible ; les HIGH sont reportées et revues.
- **`src/docs/` exclu de SonarQube** : documentation Swagger générée, très répétitive, hors code métier.
- **Poll SCM** plutôt que webhook GitHub : Jenkins n'est pas exposé sur Internet.
- **Image finale** `node:22-alpine`, sans npm/yarn/corepack, utilisateur `node` : surface d'attaque réduite (a aussi éliminé la CVE `tar` du npm embarqué).
- **Documentation API générée par le pipeline** : la spec OpenAPI est exportée depuis le code (`swagger-jsdoc`) à chaque build et rendue en HTML statique par Redocly, donc toujours synchrone avec l'API publiée.
- **Code applicatif inchangé** : `backend/src/` identique au dépôt de référence (le script d'export vit dans `backend/scripts/`).

## 10. En cas d'échec

Voir le runbook [etapes-bloquantes.md](etapes-bloquantes.md) : 11 incidents rencontrés, cause et correctif pour chacun.
