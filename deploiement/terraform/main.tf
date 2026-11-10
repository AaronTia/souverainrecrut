# 1) Inventaire Ansible généré depuis les variables : une seule source de vérité pour l'IP.
resource "local_file" "ansible_inventory" {
  filename        = "${path.module}/generated/inventory.ini"
  file_permission = "0644"
  content         = <<-EOT
    # Généré par Terraform – ne pas modifier à la main
    [app]
    ${var.vm_ip} ansible_user=${var.ssh_user} ansible_ssh_private_key_file=/root/.ssh/id_ed25519

    [app:vars]
    ansible_python_interpreter=/usr/bin/python3
    deploy_dir=${var.deploy_dir}
  EOT
}

# 2) Vérification de la VM : Terraform échoue si le serveur n'est pas prêt pour le déploiement.
resource "null_resource" "vm_ready_check" {
  triggers = {
    vm_ip       = var.vm_ip
    deploy_dir  = var.deploy_dir
    min_disk_gb = var.min_disk_gb
  }

  connection {
    type        = "ssh"
    host        = var.vm_ip
    user        = var.ssh_user
    private_key = file(var.ssh_private_key_path)
    timeout     = "30s"
  }

  provisioner "remote-exec" {
    inline = [
      "set -e",
      "echo \"OS      : $(lsb_release -ds)\"",
      "echo \"CPU     : $(nproc) vCPU | RAM : $(free -m | awk '/Mem:/{print $2}') Mo\"",
      "docker --version",
      "docker compose version",
      "systemctl is-active docker",
      "test -d ${var.deploy_dir}",
      "free_gb=$(df -BG --output=avail / | tail -1 | tr -dc '0-9'); echo \"Disque libre : $${free_gb} Go\"; test \"$${free_gb}\" -ge ${var.min_disk_gb}",
    ]
  }
}
