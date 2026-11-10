# Procédure de rollback

## Principe

Chaque déploiement conserve le tag précédent dans `/opt/souverainrecrut/.previous_tag`. Revenir en arrière,
c'est redéployer une image **déjà publiée et déjà validée** (Quality Gate, Trivy) : aucun build, donc rapide et sûr.

Tags disponibles sur Docker Hub (`aarontiavin/souverainrecrut-backend`) : `1.0.0-12a585b`, `1.0.0-07d2fe8`, `1.0.0-723d0f4`.

## Déclencher un rollback

**GitLab (nominal)** : pipeline → job `rollback-production` (manuel) ; variable `PREVIOUS_TAG` = tag cible.

**Sur le serveur** :
```bash
cd /opt/souverainrecrut
./rollback.sh                  # retourne au tag de .previous_tag
./rollback.sh 1.0.0-12a585b    # ou à un tag précis
```

## Vérifier

```bash
grep ^IMAGE_TAG .env                                          # tag attendu
docker compose ps                                              # backend healthy
curl -s http://127.0.0.1:4000/v1/ready                         # READY + CONNECTED
docker exec souverainrecrut-db psql -U souverainrecrut -d souverainrecrut -tc "select count(*) from candidates"   # données intactes
```

## Scénario testé le 10/11/2026

| Étape | Image en production | `/v1/ready` | Candidats en base |
|---|---|---|---|
| 1. Déploiement initial | `1.0.0-723d0f4` | READY | 1 (créé via l'API) |
| 2. `./rollback.sh 1.0.0-12a585b` | `1.0.0-12a585b` | READY | 1 |
| 3. `./rollback.sh 1.0.0-723d0f4` | `1.0.0-723d0f4` | READY | 1 |

Les données PostgreSQL (volume `souverainrecrut_postgres_data`) survivent aux changements d'image et à un
`docker compose down` / `up`.

**Incident découvert par ce test** : le premier essai redéployait la version courante au lieu de la version
demandée, car `deploy.sh` rechargeait `.env` et écrasait la variable `IMAGE_TAG` passée par `rollback.sh`. Corrigé :
un `IMAGE_TAG` fourni dans l'environnement prime désormais sur celui du `.env` (commit « fix deploy.sh »).
Sans ce test, le rollback documenté n'aurait pas fonctionné en situation réelle.

## Limite : le schéma de base de données

**Le rollback applicatif ne défait pas les migrations Prisma.** `prisma migrate deploy` n'applique que des
migrations « en avant ». Règles pour qu'un retour arrière reste possible :

1. migrations **additives** (nouvelle colonne nullable, nouvelle table) : la version N-1 les ignore ;
2. éviter en une seule release : renommer/supprimer une colonne, ajouter `NOT NULL` sans défaut ;
3. pour un changement destructif : procéder en deux releases (*expand* puis *contract*) ;
4. avant toute migration risquée : sauvegarde `docker exec souverainrecrut-db pg_dump -U souverainrecrut souverainrecrut > backup.sql`.

État actuel : une seule migration (`20260630124434_init`), commune à toutes les versions publiées, donc rollback sans risque de schéma.

## Après un rollback

1. notifier l'équipe (qui, pourquoi, quel tag) ;
2. ouvrir un ticket sur la version défectueuse ;
3. ne pas redéployer le tag fautif tant qu'un correctif n'est pas publié par Jenkins.
