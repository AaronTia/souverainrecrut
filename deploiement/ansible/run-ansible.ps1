# Lance ansible-playbook depuis un conteneur Docker (Ansible ne tourne pas nativement sous Windows).
# Usage (depuis la racine du dépôt) :
#   powershell -ExecutionPolicy Bypass -File .\deploiement\ansible\run-ansible.ps1                 # playbook complet (demande le mot de passe sudo)
#   powershell -ExecutionPolicy Bypass -File .\deploiement\ansible\run-ansible.ps1 --check --diff  # simulation
#   powershell -ExecutionPolicy Bypass -File .\deploiement\ansible\run-ansible.ps1 --tags runner
#   powershell -ExecutionPolicy Bypass -File .\deploiement\ansible\run-ansible.ps1 -e system_upgrade=false
#   powershell -ExecutionPolicy Bypass -File .\deploiement\ansible\run-ansible.ps1 -m ping         # test de connectivité
#
# Pas de bloc param() : les options Ansible (-e, -m, --tags...) sont transmises telles quelles via $args.
# La clé privée est copiée dans le conteneur puis passée en 0600 : un montage direct
# depuis Windows donne des droits 0777 et OpenSSH refuse la clé.

$here = $PSScriptRoot
$key  = Join-Path $env:USERPROFILE ".ssh\souverainrecrut_deploy"
if (-not (Test-Path $key)) { Write-Error "Clé introuvable : $key"; exit 1 }

# --nopass : le sudo de la VM est configuré sans mot de passe (NOPASSWD), donc pas de -K
$nopass = $args -contains "--nopass"
$extra  = ($args | Where-Object { $_ -ne "--nopass" } | ForEach-Object { "$_" }) -join " "
$ask    = if ($nopass) { "" } else { "-K" }
if ($args -contains "-m") {
  $cmd = "ansible app -i inventory.ini $extra"
} else {
  $cmd = "ansible-playbook -i inventory.ini playbook.yml $ask $extra"
}

# ANSIBLE_CONFIG explicite : un dossier monté depuis Windows est "world writable"
# et Ansible refuse d'y lire ansible.cfg automatiquement.
docker run --rm -it `
  -v "${here}:/ansible" `
  -v "${key}:/tmp/deploy_key:ro" `
  -w /ansible `
  -e ANSIBLE_CONFIG=/ansible/ansible.cfg `
  alpine/ansible:latest `
  sh -c "mkdir -p /root/.ssh && cp /tmp/deploy_key /root/.ssh/id_ed25519 && chmod 600 /root/.ssh/id_ed25519 && ansible-galaxy collection install community.general >/dev/null && $cmd"
