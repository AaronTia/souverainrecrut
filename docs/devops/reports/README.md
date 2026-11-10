# Rapports du build de référence – Jenkins #9 (9 nov. 2026, commit `12a585b`)

| Fichier | Contenu | Chiffres clés |
|---|---|---|
| `junit-result.xml` | Résultats JUnit agrégés par Jenkins (jest-junit) | 16 suites, 127 tests, 0 échec |
| `lcov.info` | Couverture Jest (format LCOV, lue par SonarQube) | 100 % lignes / branches / fonctions |
| `trivy-image.txt` | Scan de l'image `souverainrecrut-backend:1.0.0-12a585b` (HIGH + CRITICAL) | 0 CRITICAL, 16 HIGH (OS alpine 3.24.4 : 0) |
| `jenkins-build-9-console.log` | Console complète du build (ANSI retiré) | `Finished: SUCCESS`, digest `sha256:5c9992b3b245…` |

SonarQube n'exporte pas de rapport fichier en édition Community : résultats visibles dans `../captures/05-*` et `06-*` et sur http://localhost:9000/dashboard?id=souverainrecrut-backend (Quality Gate Passed, 1,5 k lignes, duplication 0,0 %).

## Captures (`../captures/`)

| # | Fichier | Montre |
|---|---|---|
| 01 | `01-jenkins-build-9-status.jpg` | Build #9 Succès, révision Git, artefacts |
| 02 | `02-jenkins-pipeline-overview.jpg` | Les 10 stages verts, durées, « Image publiée » |
| 03 | `03-jenkins-tests-127-passed.jpg` | 127 tests passés |
| 04 | `04-jenkins-job-quality-gate-badge.jpg` | Page du job : badge Quality Gate *Passed*, historique #5→#9 |
| 05 | `05-sonarqube-quality-gate-passed.jpg` | SonarQube – New Code : QG Passed, 0 nouveau problème |
| 06 | `06-sonarqube-overall-coverage-100.jpg` | SonarQube – Overall : couverture 100 %, duplication 0 % |
| 07 | `07-dockerhub-tag-1.0.0-12a585b.jpg` | Docker Hub : tag `1.0.0-12a585b`, digest, 160 Mo |
| 08 | `08-jenkins-stage-scan-trivy.jpg` | Stage Trivy : les deux commandes (rapport + seuil bloquant) |
| 09 | `09-jenkins-credentials-masques.jpg` | Credentials `sonar-token` et `dockerhub` (secrets masqués) |
| 10 | `10-sonarqube-webhook-jenkins.jpg` | Webhook SonarQube → `http://jenkins:8080/sonarqube-webhook/`, dernière livraison OK |
