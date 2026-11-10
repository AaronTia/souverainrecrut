output "vm_ip" {
  description = "Adresse IP du serveur de déploiement"
  value       = var.vm_ip
}

output "api_url" {
  description = "URL de l'API une fois déployée"
  value       = "http://${var.vm_ip}:4000/v1"
}

output "ssh_command" {
  description = "Commande de connexion (clé de déploiement)"
  value       = "ssh -i <clé_privée> ${var.ssh_user}@${var.vm_ip}"
}

output "inventory_file" {
  description = "Inventaire Ansible généré"
  value       = local_file.ansible_inventory.filename
}
