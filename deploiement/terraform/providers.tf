terraform {
  required_version = ">= 1.5"

  required_providers {
    # Le provider vSphere exige ESXi/vCenter. Avec VMware Workstation seul, la VM est
    # créée à la main (snapshot "post-install") ; Terraform pilote ce qui est
    # réellement disponible : vérification du serveur et génération de l'inventaire.
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
