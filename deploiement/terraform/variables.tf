variable "vm_ip" {
  description = "Adresse IP de la VM Ubuntu (VMware Workstation, NAT ou Bridged)"
  type        = string

  validation {
    condition     = can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", var.vm_ip))
    error_message = "vm_ip doit être une adresse IPv4."
  }
}

variable "ssh_user" {
  description = "Utilisateur SSH de déploiement"
  type        = string
}

variable "ssh_private_key_path" {
  description = "Chemin de la clé privée SSH (hors dépôt)"
  type        = string
  sensitive   = true
}

variable "deploy_dir" {
  description = "Répertoire de déploiement sur le serveur"
  type        = string
  default     = "/opt/souverainrecrut"
}

variable "min_disk_gb" {
  description = "Espace disque libre minimal exigé sur / (Go)"
  type        = number
  default     = 5
}
