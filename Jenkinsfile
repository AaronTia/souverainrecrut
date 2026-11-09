pipeline {
  agent any

  options {
    skipDefaultCheckout()
    timestamps()
    timeout(time: 30, unit: 'MINUTES')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '10'))
  }

  environment {
    CI          = 'true'
    LOCAL_IMAGE = 'souverainrecrut-backend'
    IMAGE_NAME  = 'souverainrecrut-backend'   // nom du dépôt sur Docker Hub
    TRIVY_CACHE = '/var/jenkins_home/.cache/trivy'
  }

  stages {
    stage('Checkout') {
      steps {
        script {
          // Avec skipDefaultCheckout(), env.GIT_COMMIT n'est pas défini :
          // on récupère le commit dans le résultat de checkout scm.
          def scmVars = checkout scm
          env.GIT_COMMIT = scmVars.GIT_COMMIT

          // Tag traçable : version applicative + identifiant court du commit
          def version = sh(returnStdout: true,
            script: "node -p \"require('./backend/package.json').version\"").trim()
          env.IMAGE_TAG = "${version}-${env.GIT_COMMIT.take(7)}"
        }
        echo "Image à produire : ${env.IMAGE_NAME}:${env.IMAGE_TAG}"
      }
    }

    stage('Install') {
      steps {
        dir('backend') {
          sh 'node --version && npm --version'
          sh 'npm ci'
        }
      }
    }

    stage('Prisma generate') {
      steps {
        dir('backend') {
          sh 'npx prisma generate'
        }
      }
    }

    stage('Tests') {
      steps {
        dir('backend') {
          // Tests Jest + couverture (coverage/lcov.info) + rapport JUnit (reports/junit.xml)
          sh 'npm run test:ci'
        }
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'backend/reports/junit.xml'
          archiveArtifacts artifacts: 'backend/coverage/lcov.info', allowEmptyArchive: true
        }
      }
    }

    stage('SonarQube') {
      steps {
        dir('backend') {
          // withSonarQubeEnv injecte SONAR_HOST_URL et SONAR_AUTH_TOKEN (serveur "sonar")
          withSonarQubeEnv('sonar') {
            sh 'npx --yes @sonar/scan -Dsonar.host.url="$SONAR_HOST_URL" -Dsonar.token="$SONAR_AUTH_TOKEN"'
          }
        }
      }
    }

    stage('Quality Gate') {
      steps {
        // Attend le webhook SonarQube -> Jenkins ; échec du Quality Gate = build rouge
        timeout(time: 5, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }

    stage('Build image') {
      steps {
        dir('backend') {
          sh 'docker build -t "$LOCAL_IMAGE:$IMAGE_TAG" .'
        }
      }
    }

    stage('Scan Trivy') {
      steps {
        sh 'mkdir -p reports'
        // Rapport complet (HIGH + CRITICAL) archivé pour le livrable
        sh '''
          trivy image --cache-dir "$TRIVY_CACHE" --no-progress \
            --severity HIGH,CRITICAL --format table \
            --output reports/trivy-image.txt \
            "$LOCAL_IMAGE:$IMAGE_TAG"
        '''
        // Seuil bloquant : aucune vulnérabilité CRITICAL corrigeable
        sh '''
          trivy image --cache-dir "$TRIVY_CACHE" --no-progress \
            --severity CRITICAL --ignore-unfixed --exit-code 1 \
            "$LOCAL_IMAGE:$IMAGE_TAG"
        '''
      }
      post {
        always {
          archiveArtifacts artifacts: 'reports/trivy-image.txt', allowEmptyArchive: true
        }
      }
    }

    stage('Push Docker Hub') {
      steps {
        // Atteint seulement si tous les contrôles précédents sont passés
        withCredentials([usernamePassword(credentialsId: 'dockerhub',
                                          usernameVariable: 'DH_USER',
                                          passwordVariable: 'DH_TOKEN')]) {
          sh '''
            echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
            docker tag "$LOCAL_IMAGE:$IMAGE_TAG" "$DH_USER/$IMAGE_NAME:$IMAGE_TAG"
            docker push "$DH_USER/$IMAGE_NAME:$IMAGE_TAG"
          '''
        }
      }
      post {
        always {
          sh 'docker logout || true'
        }
      }
    }
  }

  post {
    success {
      echo "Image publiée : <compte>/${env.IMAGE_NAME}:${env.IMAGE_TAG}"
    }
    failure {
      echo 'Pipeline en échec : voir le stage en rouge (tests, Quality Gate, Trivy...).'
    }
    always {
      // Libère l'espace disque de l'hôte (images locales du build)
      // (ignoré si le build a échoué avant le calcul du tag)
      sh '[ -z "$IMAGE_TAG" ] || docker image rm "$LOCAL_IMAGE:$IMAGE_TAG" || true'
    }
  }
}
