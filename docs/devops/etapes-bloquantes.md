# Étapes bloquantes – mise en place de la CI (Jour 1)

> Runbook du pipeline décrit dans [README-pipeline.md](README-pipeline.md). Preuves : [captures/](captures/) et [reports/](reports/).

Journal des points qui ont bloqué la chaîne **GitHub → Jenkins → SonarQube → Trivy → Docker Hub**, avec leur cause et la solution retenue. Sert de runbook : *que faire quand une étape échoue*.

| # | Étape | Symptôme | Statut |
|---|---|---|---|
| 1 | Tests Jest | `npm test` : « No tests found » / TypeScript non compilé | ✅ Résolu |
| 2 | Prisma | Types `User`, `Role`… introuvables (`TS2305`) | ✅ Résolu |
| 3 | Jest | Seuils de couverture ignorés | ✅ Résolu |
| 4 | SonarQube | Mot de passe admin perdu après redémarrage | ✅ Résolu |
| 5 | SonarQube | Webhook vers Jenkins refusé | ✅ Résolu |
| 6 | Jenkins | Image sans `docker`, Node ni Trivy | ✅ Résolu |
| 7 | Jenkins | Credential `sonar-token` non enregistré | ✅ Résolu |
| 8 | Pipeline | `NullPointerException` au stage Checkout | ✅ Résolu |
| 9 | Pipeline | Logs illisibles (codes couleur, messages dotenv) | ✅ Résolu |
| 10 | Trivy | 2 vulnérabilités CRITICAL → push bloqué | ✅ Résolu |
| 11 | Push Docker Hub | `Could not find credentials entry with ID 'dockerhub'` | ✅ Résolu |

---

## 1. Tests Jest non exécutables

- **Symptôme** : `npm test` affichait « Jest sera configuré plus tard », puis « No tests found, exiting with code 1 ».
- **Cause** : le dépôt fourni n'avait qu'un script placeholder, ni configuration Jest, ni compilateur TypeScript pour Jest (`ts-jest`).
- **Solution** : `ts-jest`, `@types/jest`, `supertest`, `jest-mock-extended`, `jest-junit` en devDependencies ; `jest.config.js` (projets `unit` / `integration`, rapports `lcov` pour SonarQube et `junit.xml` pour Jenkins) ; `tsconfig.test.json` ; faux client Prisma dans `tests/setup/prisma-mock.ts`.

## 2. Client Prisma non généré

- **Symptôme** : `Module '"@prisma/client"' has no exported member 'User'` (tests et `tsc`).
- **Cause** : npm a bloqué le script `postinstall` de Prisma (`allowScripts`).
- **Solution** : lancer `npx prisma generate` après chaque `npm ci` (stage dédié dans le Jenkinsfile).

## 3. Seuil de couverture ignoré

- **Symptôme** : `Unknown option "coverageThresholds"` dans la sortie Jest.
- **Cause** : faute de frappe (`coverageThresholds` au lieu de `coverageThreshold`) et option placée au niveau des projets.
- **Solution** : `coverageThreshold` au niveau global uniquement → les seuils (100 % sur `middlewares/` et `validators/`, 90 % global) sont appliqués et font échouer le stage Tests s'ils ne sont pas atteints.

## 4. Mot de passe admin SonarQube

- **Symptôme** : impossible de se reconnecter après le redémarrage de SonarQube.
- **Cause** : commande de réinitialisation lancée dans PowerShell : `\$` n'échappe pas `$`, le hash a été tronqué.
- **Solution** : relancer la requête SQL depuis Bash (ou échapper avec `` `$ `` dans PowerShell). Identifiants remis à `admin` / `admin`, puis changement imposé à la connexion.

## 5. Webhook SonarQube → Jenkins refusé

- **Symptôme** : « Invalid URL: loopback, wildcard, link-local, site-local… not allowed for webhooks ».
- **Cause** : SonarQube bloque par défaut les adresses de réseau privé (`http://jenkins:8080`).
- **Solution** : `SONAR_VALIDATEWEBHOOKS=false` dans `docker/docker-compose.yml` (acceptable en local uniquement), puis webhook `Jenkins` → `http://jenkins:8080/sonarqube-webhook/`.

## 6. Jenkins sans les outils du pipeline

- **Symptôme** : l'image `jenkins/jenkins:lts-jdk17` ne contient ni `docker`, ni Node.js, ni Trivy.
- **Solution** : image personnalisée `docker/jenkins/Dockerfile` (docker CLI, Node.js 22, Trivy, plugins `sonar`, `docker-workflow`, `ansicolor`), construite par `docker compose`. Le socket Docker de l'hôte est monté dans le conteneur.

## 7. Credential `sonar-token` absent

- **Symptôme** : la liste « Server authentication token » du serveur SonarQube restait vide.
- **Cause** : le credential n'avait pas été enregistré (formulaire non validé).
- **Solution** : créer un credential **Secret text** d'ID `sonar-token` (Administrer Jenkins → Credentials → Global), puis le sélectionner dans le serveur SonarQube `sonar`.

## 8. `NullPointerException` au stage Checkout

- **Symptôme** : `Cannot invoke method take() on null object` (Jenkinsfile, ligne 27) ; tous les stages suivants sautés.
- **Cause** : avec `skipDefaultCheckout()`, Jenkins ne définit pas `env.GIT_COMMIT`.
- **Solution** : `def scmVars = checkout scm` puis `env.GIT_COMMIT = scmVars.GIT_COMMIT` ; le nettoyage final ignore un tag vide.

## 9. Logs illisibles

- **Symptôme** : codes `[0m`, `[33m` dans la console et messages `◇ injected env (0) from .env // tip…`.
- **Cause** : couleurs ANSI de morgan non interprétées par Jenkins ; messages d'information de dotenv 17.
- **Solution** : plugin AnsiColor + `ansiColor('xterm')` dans le Jenkinsfile ; `DOTENV_CONFIG_QUIET=true` (Jenkinsfile et `tests/setup/env.ts`).

## 10. Trivy : vulnérabilités CRITICAL

- **Symptôme** : stage Scan Trivy en échec (`--severity CRITICAL --ignore-unfixed --exit-code 1`), push non exécuté.
- **Causes et solutions** :
  - `proxy-addr` 2.0.7 (CVE-2026-90711), via Express → passage à `proxy-addr` 2.0.8.
  - `tar` 6.2.1 (CVE-2026-59873), dans le **npm intégré à l'image `node:20-alpine`** (pas une dépendance du projet) → `backend/Dockerfile` : passage à `node:22-alpine` et suppression de npm/npx/corepack/yarn de l'image finale ; exécution en utilisateur `node`.
- **Résultat** : 0 CRITICAL, 16 HIGH (non bloquants, rapport archivé `reports/trivy-image.txt`).

## 11. Credential Docker Hub manquant

- **Symptôme** : `ERROR: Could not find credentials entry with ID 'dockerhub'` au stage Push Docker Hub (tous les contrôles précédents passent).
- **Cause** : le credential n'existait pas encore dans Jenkins.
- **Solution** :
  1. Sur hub.docker.com : *Account settings → Personal access tokens → Generate new token* (droits **Read & Write**).
  2. Dans Jenkins : *Administrer Jenkins → Credentials → System → Identifiants globaux → Add Credentials*, type **Nom d'utilisateur et mot de passe**, ID **`dockerhub`**, nom d'utilisateur = identifiant Docker Hub (`aarontiavin`), mot de passe = Access Token.
  3. Build #9 relancé : image `aarontiavin/souverainrecrut-backend:1.0.0-12a585b` publiée (digest `sha256:5c9992b3…`). Voir `captures/07-dockerhub-tag-1.0.0-12a585b.jpg`.

---

## Choix assumés (à justifier dans le rapport)

- **`src/docs/` exclu de SonarQube** : ce dossier ne contient que la documentation Swagger/OpenAPI (~40 % des lignes de `src`, très répétitive). Les doublons y sont acceptés ; SonarQube affiche donc ~0 % de duplications sur le code applicatif.
- **Déclenchement par Poll SCM (`H/5 * * * *`)** plutôt que webhook GitHub : Jenkins tourne en local et n'est pas joignable par GitHub. Un webhook nécessiterait un relais (smee.io) ou d'exposer Jenkins sur Internet.
- **Seuil Trivy** : seules les vulnérabilités CRITICAL disposant d'un correctif bloquent la publication ; les HIGH sont reportées dans le rapport archivé.
- **Code applicatif non modifié** : `backend/src/` est identique au dépôt de référence ; seuls les fichiers de CI/CD, de tests et le Dockerfile ont été adaptés.
