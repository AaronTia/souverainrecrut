# Rapport final – projet fil rouge CI/CD SouverainRecrut

Mastère Expert en Développement et Déploiement de Solutions Numériques Sécurisées – RNCP 40166 – Sup de Vinci Rennes
Module CI/CD (14 h) – Blocs 4 et 5 – Formateur : Alimou Diallo – 9 et 10 novembre 2026

## 1. Objectif et résultat

Mettre en place une chaîne reproductible du commit au serveur pour l'API backend : tests, analyse, image
conteneur, scan, publication, puis déploiement approuvé et réversible.

| Exigence du cahier | Résultat | Preuve |
|---|---|---|
| Tests backend + couverture exploitable | ✅ 18 suites, 151 tests, couverture 99,4 % lignes | `docs/devops/reports/junit-result.xml`, `lcov.info` |
| SonarQube + Quality Gate PASSED | ✅ | capture 05, 06 |
| Jenkinsfile : checkout → tests → Sonar → image → Trivy → push | ✅ builds #9, #10, #11 verts | `Jenkinsfile`, capture 02 |
| Image taguée, scannée, publiée | ✅ `aarontiavin/souverainrecrut-backend:1.0.0-723d0f4` | capture 07, `trivy-image.txt` |
| VM Ubuntu + Docker via Ansible | ✅ `failed=0`, idempotent | `deploiement/ansible/`, `deploiement-preuves.txt` |
| Terraform | ✅ avec adaptation (voir §4) | `deploiement/terraform/`, `terraform-apply.txt` |
| Déploiement Compose + PostgreSQL, image tirée de Docker Hub | ✅ | `deploiement-preuves.txt` |
| Migrations Prisma maîtrisées | ✅ `migrate deploy` depuis les fichiers **de l'image** | `deploy.sh` |
| Persistance des données | ✅ après `down` + `up` et après rollback | `procedure-rollback.md` |
| Pipeline GitLab avec approbation manuelle | ✅ pipeline #3049879562 : `validate-tag` → `deploy-production` (approuvé) → `smoke-test`, tous verts | captures 12 à 14, `.gitlab-ci.yml` |
| Rollback documenté **et testé** | ✅ 723d0f4 → 12a585b → 723d0f4 | `procedure-rollback.md` |

## 2. Choix techniques justifiés

| Choix | Justification |
|---|---|
| Deux dépôts (GitHub code / GitLab déploiement) | séparation des responsabilités ; seul le **tag d'image** les relie (pattern multi-repo du cours) |
| Tag `version-sha` | traçabilité commit → image ; jamais `latest` en production |
| Trivy : bloquer seulement les CRITICAL corrigeables | évite de bloquer sur des CVE sans correctif ; les 16 HIGH sont listées dans le rapport archivé |
| Migrations extraites **de l'image** | la version déployée applique exactement ses propres migrations, pas celles d'un autre commit |
| GitLab Runner **sur la VM** | la VM est derrière le NAT d'un poste de travail : les runners partagés de gitlab.com ne peuvent pas l'atteindre ; le runner sort vers GitLab, aucun port entrant |
| Poll SCM (5 min) plutôt que webhook GitHub | Jenkins local, non joignable depuis Internet |
| `sudo` sans mot de passe + clé dédiée | automatisation sans mot de passe dans les scripts ni dans le dépôt |
| `src/docs` exclu de SonarQube | documentation Swagger répétitive (~40 % des lignes) ; doublons acceptés |
| Code applicatif `backend/src/` inchangé | le périmètre est la chaîne de livraison, pas le code métier |

## 3. Qualité : ce que la suite de tests prouve, et ce qu'elle ne prouve pas

La suite a été **recentrée sur les comportements** : suppression des tests qui recopiaient l'implémentation
(appels Prisma) ou ne vérifiaient qu'un `typeof`, ajout de tests CORS, de contrat OpenAPI ↔ routes et de
8 tests `it.failing` qui documentent des défauts du dépôt de référence. Seuils : 100 % sur `middlewares/` et
`validators/`, 90 % global.

### Défauts identifiés (tracés, non corrigés : périmètre « code applicatif inchangé »)

| # | Défaut | Gravité |
|---|---|---|
| D1 | `PUT /users/:id` avec un mot de passe : **stocké en clair** (pas de hash à la mise à jour) | Critique |
| D2 | `GET /users` et `/users/:id` **renvoient le hash bcrypt** (pas de `select`) | Haute |
| D3 | `POST /auth/login` sans validation d'entrée (corps vide → 401 au lieu de 400) | Moyenne |
| D4 | `?page=abc` → `skip: NaN` → erreur serveur | Moyenne |
| D5 | Violation de clé étrangère (`P2003`) non traduite → 500 | Moyenne |
| D6 | Un recruteur peut créer une offre au nom d'un autre (pas de contrôle de propriété) | Moyenne |

Les tests `it.failing` **passent aujourd'hui** (défaut présent) et feront échouer le pipeline le jour où le
défaut sera corrigé sans mise à jour du test : la dette est visible, pas masquée.

**Limite** : Prisma est mocké, donc contraintes d'unicité, cascades et clés étrangères ne sont pas exercées
contre PostgreSQL en CI. Piste : suite d'intégration sur un PostgreSQL éphémère dans le pipeline Jenkins.

## 4. Écarts assumés par rapport au cahier

| Écart | Raison | Impact |
|---|---|---|
| Ubuntu **22.04** au lieu de 24.04 | VM fournie | aucun (Docker, Compose, Ansible identiques) |
| Terraform sans `vsphere_virtual_machine` | VMware Workstation, pas d'ESXi/vCenter (prévu au §4.2 du cahier) | Terraform vérifie le serveur et génère l'inventaire ; VM créée à la main avec snapshot |
| Pas de HTTPS | environnement de laboratoire | API en HTTP sur réseau local ; reverse proxy TLS à ajouter en production |

## 5. Exécution du pipeline GitLab et incidents rencontrés

Le pipeline s'exécute sur un **GitLab Runner installé sur la VM** (executor `shell`, tag `souverainrecrut-vm`).
Pipeline de référence **#3049879562** (commit `d2b6ad47`) : `validate-tag` ✅ → `deploy-production` ✅ (approuvé
manuellement par `@WakakiVongola`, visible dans *Deploy > Environments*) → `smoke-test` ✅
(`/v1/health` UP, `/v1/ready` READY, image en production = `1.0.0-723d0f4`). Durée : ~8 min 15 s.

| # | Incident | Cause | Résolution |
|---|---|---|---|
| 1 | `.gitlab-ci.yml` refusé par GitLab | `echo "... : ..."` : le `: ` est lu comme une clé YAML | ligne entre apostrophes ; configuration validée (« Pipeline syntax is correct ») |
| 2 | `validate-tag` échoue (`curl` code 56) | coupure réseau ponctuelle de la VM vers Docker Hub | 5 tentatives avec temporisation |
| 3 | **Clé privée affichée dans le log d'un job** | `SSH_PRIVATE_KEY` créée en type *Variable* au lieu de *File* : `chmod 600 "$SSH_PRIVATE_KEY"` a reçu le contenu et l'a recopié dans son message d'erreur | variable recréée en type **File** ; logs concernés à effacer ; clé à renouveler (voir ci-dessous) |
| 4 | Rollback redéployait la version courante | `deploy.sh` rechargeait `.env` et écrasait `IMAGE_TAG` | l'`IMAGE_TAG` de l'environnement prime désormais |
| 5 | VM qui décroche par intermittence | instabilité du réseau virtuel VMware (NAT) | redémarrage du service NAT ; scripts idempotents et tentatives répétées |

**Leçon de sécurité (incident 3)** : un secret multiligne ne peut pas être masqué par GitLab ; seul le type *File* évite
qu'il apparaisse dans un log. Les deux logs concernés ont été **effacés** (*Erase job log*, 10/11/2026). La clé a été conservée (projet pédagogique,
dépôt privé à un seul membre) ; en production réelle elle devrait être renouvelée (nouvelle clé, installation sur
le serveur, retrait de l'ancienne).

**Limites restantes** : options du cours non réalisées (SBOM `syft`, signature `cosign`, tests de charge `k6`) ; snapshot
VMware « post-install » confirmé.

## 6. Métriques de la livraison

| Indicateur | Valeur |
|---|---|
| Builds Jenkins | 11 (5 en échec avant stabilisation, 3 verts de référence #9 à #11) |
| Durée d'un build complet | ~5 min |
| Durée du pipeline GitLab complet | ~8 min 15 s avant optimisation, dont 4 min 40 s pour `prisma migrate deploy` (la CLI Prisma était retéléchargée depuis npm à chaque déploiement) |
| Migration Prisma après optimisation | **13 s** en cache (53 s au premier passage) grâce à un volume `npm_cache` : environ 20 fois plus rapide ; pipeline complet estimé à ~3 min |
| Temps de restauration (rollback testé) | ~2 min |
| Incidents documentés | 11 en CI (`etapes-bloquantes.md`) + 5 en déploiement (§5) |

## 7. Argumentaire pour le jury (MSPR 4.1 / 5.1)

1. **Fiable** : image unique testée, scannée, puis déployée telle quelle ; digest identique de Jenkins à la production.
2. **Réversible** : rollback joué sur trois versions, données conservées, limites de schéma documentées.
3. **Traçable** : commit → build → tag → digest → conteneur ; approbation manuelle tracée par GitLab.
4. **Sûr** : secrets hors dépôt, image non-root sans outils de build, pare-feu, tests de sécurité des middlewares.
5. **Honnête** : défauts du code de référence et limites de la chaîne documentés plutôt que cachés.
