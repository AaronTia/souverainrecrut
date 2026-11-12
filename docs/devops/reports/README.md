# Rapports du build de référence – Jenkins #9 (9 nov. 2026, commit `12a585b`)

> Ces fichiers sont figés au build #9. La suite compte depuis 18 suites et 151 tests, pour 99,4 % de couverture des lignes (captures 03, 06 et 08 : build #14).

| Fichier | Contenu | Chiffres clés (build #9) |
|---|---|---|
| `junit-result.xml` | Résultats JUnit agrégés par Jenkins (jest-junit) | 16 suites, 127 tests, 0 échec |
| `lcov.info` | Couverture Jest (format LCOV, lue par SonarQube) | 100 % lignes / branches / fonctions |
| `trivy-image.txt` | Scan de l'image `souverainrecrut-backend:1.0.0-12a585b` (HIGH + CRITICAL) | 0 CRITICAL, 16 HIGH (OS alpine 3.24.4 : 0) |
| `openapi.json` | Spécification OpenAPI 3.0.3 exportée depuis `src/docs/swagger.ts` (stage Docs API) | 14 routes, 8 tags |
| `api-docs.html` | Documentation API statique générée par Redocly à partir de `openapi.json` | 279 Ko, autonome |
| `jenkins-build-9-console.log` | Console complète du build (ANSI retiré) | `Finished: SUCCESS`, digest `sha256:5c9992b3b245…` |

SonarQube n'exporte pas de rapport fichier en édition Community : résultats visibles dans `../captures/05-*` et `06-*` et sur http://localhost:9000/dashboard?id=souverainrecrut-backend (Quality Gate Passed, 1,5 k lignes, duplication 0,0 %).

## Captures (`../captures/`)

| # | Fichier | Montre |
|---|---|---|
| 01 | `01-jenkins-build-9-status.jpg` | Build #9 Succès, révision Git, artefacts |
| 02 | `02-jenkins-pipeline-overview.jpg` | Les 10 stages verts, durées, « Image publiée » |
| 03 | `03-jenkins-tests-151-passed.jpg` | Build #14 : 151 tests passés |
| 04 | `04-jenkins-job-quality-gate-badge.jpg` | Page du job : badge Quality Gate *Passed*, historique #5→#9 |
| 05 | `05-sonarqube-quality-gate-passed.jpg` | SonarQube – New Code : Quality Gate Passed, 0 nouveau problème |
| 06 | `06-sonarqube-overall-code.jpg` | SonarQube – Overall : couverture 95,8 % (lignes + branches), 3 problèmes ouverts du code de référence |
| 07 | `07-dockerhub-tag-1.0.0-12a585b.jpg` | Docker Hub : tag `1.0.0-12a585b`, digest, 160 Mo |
| 08 | `08-jenkins-trivy-bloquant-0-critical.jpg` | Build #14 : commande Trivy bloquante, 0 vulnérabilité critique |
| 09 | `09-jenkins-credentials-masques.jpg` | Credentials `sonar-token` et `dockerhub` (secrets masqués) |
| 10 | `10-sonarqube-webhook-jenkins.jpg` | Webhook SonarQube → `http://jenkins:8080/sonarqube-webhook/`, dernière livraison OK |
| 11 | `11-redocly-api-docs.jpg` | Documentation API générée (Redocly) à partir de la spec exportée |
| 12 | `12-gitlab-pipeline-vert.jpg` | Pipeline GitLab #3049879562 : validate-tag, deploy-production, smoke-test verts ; rollback disponible |
| 13 | `13-gitlab-environnement-production.jpg` | GitLab Environments : déploiement `production` réussi, déclenché par @WakakiVongola ; « Waiting » = pipeline non approuvé |
| 14 | `14-gitlab-smoke-test-log.jpg` | Log du smoke-test : health UP, ready READY, image en production = tag demandé |
| 15 | `15-dockerhub-tag-723d0f4-digest.jpg` | Docker Hub : tag 1.0.0-723d0f4, index digest identique à Jenkins et à la VM |
| 16 | `16-gitlab-depot-deploiement.jpg` | Dépôt GitLab de déploiement (ansible, deployment, terraform, .gitlab-ci.yml) |
| 17 | `17-gitlab-runner-en-ligne.jpg` | Runner `souverainrecrut-vm` en ligne (adresse IP masquée) |
| 18 | `18-gitlab-variables-masquees.jpg` | Variables CI/CD : valeurs masquées, secrets « Masked », clé SSH « File », toutes « Protected » |
| 19 | `19-jenkins-historique-builds.jpg` | Job Jenkins : builds #12 à #14 verts, tests 127 → 150, artefacts dont la doc d'API |
