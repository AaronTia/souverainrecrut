#!/usr/bin/env python3
"""Assemble le livrable dans l'arborescence du cahier des charges (§ 6) et produit l'archive ZIP de rendu.

    python livrable/assembler-livrable.py

Résultat (ignoré par Git) : livrable/SouverainRecrut-CICD/ et livrable/SouverainRecrut-CICD.zip
Le script refuse de produire l'archive s'il détecte un secret ou un fichier sensible.
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "livrable" / "SouverainRecrut-CICD"
ZIP = ROOT / "livrable" / "SouverainRecrut-CICD.zip"

# (source dans le dépôt, destination dans le livrable)
FICHIERS = [
    # ---- integration-continue : Jour 1
    ("Jenkinsfile", "integration-continue/Jenkinsfile"),
    ("backend/Dockerfile", "integration-continue/Dockerfile"),
    ("backend/.dockerignore", "integration-continue/.dockerignore"),
    ("backend/sonar-project.properties", "integration-continue/sonar/sonar-project.properties"),
    ("backend/jest.config.js", "integration-continue/tests/jest.config.js"),
    ("backend/tests", "integration-continue/tests/tests"),
    ("backend/scripts/export-openapi.ts", "integration-continue/tests/export-openapi.ts"),
    ("docker/docker-compose.yml", "integration-continue/stack-ci/docker-compose.yml"),
    ("docker/jenkins/Dockerfile", "integration-continue/stack-ci/jenkins/Dockerfile"),
    ("docs/devops/README-pipeline.md", "integration-continue/README.md"),
    ("docs/devops/etapes-bloquantes.md", "integration-continue/etapes-bloquantes.md"),
    ("docs/devops/reports", "integration-continue/reports"),
    ("docs/devops/captures", "integration-continue/captures"),
    # ---- deploiement : Jour 2
    ("deploiement", "deploiement"),
    # ---- documentation
    ("documentation/architecture.md", "documentation/architecture.md"),
    ("documentation/procedure-deploiement.md", "documentation/procedure-deploiement.md"),
    ("documentation/procedure-rollback.md", "documentation/procedure-rollback.md"),
    ("documentation/rapport-final.md", "documentation/rapport-final.md"),
    ("documentation/rapport/rapport-final.pdf", "documentation/rapport/rapport-final.pdf"),
    ("docs/devops/cahier-des-charges-local.md", "documentation/suivi-livrables.md"),
]

# Jamais dans le livrable : secrets, états, fichiers générés
EXCLUS_NOMS = {".env", ".previous_tag", "terraform.tfstate", "terraform.tfstate.backup", "terraform.tfvars"}
EXCLUS_DOSSIERS = {".terraform", "generated", "prisma", "node_modules", "__pycache__", "coverage"}
SECRETS = [
    (r"glpat-[0-9A-Za-z_\-]{10,}", "jeton GitLab"),
    (r"glrt-[0-9A-Za-z_\-]{10,}", "jeton de runner GitLab"),
    (r"dckr_pat_[0-9A-Za-z_\-]{10,}", "jeton Docker Hub"),
    (r"squ_[0-9a-f]{20,}", "jeton SonarQube"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "clé privée"),
    (r"45\.112\.\d+\.\d+", "adresse IP publique"),
]

MAPPING = """\
| Dans le dépôt GitHub | Dans ce livrable |
|---|---|
| `Jenkinsfile` | `integration-continue/Jenkinsfile` |
| `backend/Dockerfile`, `backend/.dockerignore` | `integration-continue/Dockerfile`, `.dockerignore` |
| `backend/sonar-project.properties` | `integration-continue/sonar/` |
| `backend/jest.config.js`, `backend/tests/` | `integration-continue/tests/` |
| `docker/` (Jenkins + SonarQube) | `integration-continue/stack-ci/` |
| `docs/devops/README-pipeline.md`, `etapes-bloquantes.md` | `integration-continue/README.md`, `etapes-bloquantes.md` |
| `docs/devops/reports/`, `docs/devops/captures/` | `integration-continue/reports/`, `integration-continue/captures/` |
| `deploiement/` | `deploiement/` |
| `documentation/` | `documentation/` |
| `docs/devops/cahier-des-charges-local.md` | `documentation/suivi-livrables.md` |
"""

README = f"""# SouverainRecrut – chaîne CI/CD du backend (rendu)

Projet fil rouge CI/CD · Mastère Expert en Développement et Déploiement de Solutions Numériques Sécurisées (RNCP 40166)
Aaron Tiavinjanahary · Formateur : Alimou Diallo · Sup de Vinci Rennes · 9 et 10 novembre 2026

**À lire en premier : [`documentation/rapport/rapport-final.pdf`](documentation/rapport/rapport-final.pdf)** (27 pages, schémas et captures).

| Dossier | Contenu |
|---|---|
| [`integration-continue/`](integration-continue/) | Jour 1 : Jenkinsfile, Dockerfile, configuration SonarQube, tests, stack Jenkins/SonarQube, rapports (JUnit, couverture, Trivy, OpenAPI) et captures |
| [`deploiement/`](deploiement/) | Jour 2 : Terraform, Ansible, Docker Compose, scripts de déploiement et de rollback, `.gitlab-ci.yml` |
| [`documentation/`](documentation/) | architecture, procédures de déploiement et de rollback, rapport final (Markdown et PDF), suivi des livrables |

Dépôts sources :
- code et intégration continue : `github.com/AaronTia/souverainrecrut` (branche `Dev`)
- déploiement : `gitlab.com/WakakiVongola/souverainrecrut-deploy`

## Correspondance des chemins

Les documents citent parfois les chemins du dépôt GitHub ; voici leur emplacement dans ce livrable.

{MAPPING}
Ce livrable ne contient aucun secret : `.env` réels, jetons, clés privées, `*.tfvars` et états Terraform sont exclus
(vérification automatique à l'assemblage).
"""


def copier(src: Path, dst: Path):
    if src.is_dir():
        for f in src.rglob("*"):
            rel = f.relative_to(src)
            if any(part in EXCLUS_DOSSIERS for part in rel.parts) or f.name in EXCLUS_NOMS:
                continue
            if f.is_file():
                (dst / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst / rel)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main():
    # On vide le dossier plutôt que de le supprimer : sous Windows, il peut être ouvert (explorateur, terminal).
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.iterdir():
        shutil.rmtree(f) if f.is_dir() else f.unlink()
    for src, dst in FICHIERS:
        s = ROOT / src
        if not s.exists():
            sys.exit(f"Fichier source manquant : {src}")
        copier(s, OUT / dst)

    runbook = OUT / "integration-continue/etapes-bloquantes.md"
    runbook.write_text(runbook.read_text(encoding="utf-8").replace("(README-pipeline.md)", "(README.md)"), encoding="utf-8")
    (OUT / "README.md").write_text(README, encoding="utf-8")

    alertes = []
    for f in OUT.rglob("*"):
        if f.is_file() and f.suffix.lower() not in {".jpg", ".png", ".pdf"}:
            texte = f.read_text(encoding="utf-8", errors="ignore")
            alertes += [f"{f.relative_to(OUT)} : {nom}" for motif, nom in SECRETS if re.search(motif, texte)]
    if alertes:
        sys.exit("ARCHIVE NON PRODUITE, secret détecté :\n  " + "\n  ".join(alertes))

    ZIP.unlink(missing_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.rglob("*")):
            if f.is_file():
                z.write(f, Path(OUT.name) / f.relative_to(OUT))
    nb = sum(1 for f in OUT.rglob("*") if f.is_file())
    print(f"{nb} fichiers · aucun secret détecté · {ZIP.relative_to(ROOT)} ({ZIP.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
