FROM jenkins/jenkins:lts-jdk17

USER root

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
 && install -m 0755 -d /etc/apt/keyrings \
 # Dépôt Docker (CLI uniquement, le démon est celui de l'hôte)
 && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
 && echo "deb [signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
      > /etc/apt/sources.list.d/docker.list \
 # Dépôt Trivy
 && curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor -o /etc/apt/keyrings/trivy.gpg \
 && echo "deb [signed-by=/etc/apt/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" \
      > /etc/apt/sources.list.d/trivy.list \
 # Dépôt Node.js 22
 && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
 && apt-get update \
 && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin trivy nodejs \
 && rm -rf /var/lib/apt/lists/*

# Plugins nécessaires au Jenkinsfile, en plus des plugins suggérés :
#   - sonar           : withSonarQubeEnv / waitForQualityGate
#   - docker-workflow : syntaxe docker.build / docker.withRegistry
# Installés dans /usr/share/jenkins/ref, copiés dans jenkins_home au démarrage.
RUN jenkins-plugin-cli --plugins sonar docker-workflow

# Le conteneur tourne en root (voir docker-compose.yml) pour accéder au socket Docker.
