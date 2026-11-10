# Terraform – vérification du serveur et inventaire Ansible

## Pourquoi pas de VM créée par Terraform ?

Le cahier des charges (§4.2) le prévoit : le provider `vsphere` exige un **ESXi/vCenter**. Avec
**VMware Workstation seul**, il n'existe pas d'API de création de VM utilisable par ce provider. La VM
Ubuntu est donc créée **à la main** (snapshot « post-install » avant configuration), et Terraform est
utilisé sur ce qui est réellement pilotable :

| Ressource | Rôle |
|---|---|
| `local_file.ansible_inventory` | génère `generated/inventory.ini` depuis `vm_ip`, `ssh_user`, `deploy_dir` : une seule source de vérité pour l'adresse du serveur |
| `null_resource.vm_ready_check` | se connecte en SSH et **échoue** si le serveur n'est pas prêt (Docker actif, Compose installé, répertoire de déploiement présent, ≥ 5 Go libres) |

Avec un ESXi/vCenter, il suffirait d'ajouter le provider `vsphere` et une ressource `vsphere_virtual_machine`
en amont ; les deux ressources ci-dessus resteraient inchangées.

## Utilisation (Terraform exécuté dans Docker, rien à installer sous Windows)

```bash
cp terraform.tfvars.example terraform.tfvars        # adapter vm_ip, ssh_user (fichier ignoré par Git)

# alias : TF = terraform dans l'image officielle, clé SSH montée en lecture seule
TF() { docker run --rm -v "$PWD:/tf" -v "$HOME/.ssh/souverainrecrut_deploy:/keys/deploy_key:ro" -w /tf hashicorp/terraform:latest "$@"; }

TF init
TF validate
TF plan
TF apply
```

## Sécurité

- `terraform.tfvars`, `*.tfstate*` et `.terraform/` sont dans `.gitignore`.
- La clé privée n'est jamais copiée : elle est montée en lecture seule et lue par `file()` au moment de l'exécution ; la variable est marquée `sensitive`.
- En équipe, le state doit être stocké dans un backend distant verrouillé (S3 + DynamoDB, GitLab Terraform state) ; ici un state local suffit car il ne contient aucun secret.
