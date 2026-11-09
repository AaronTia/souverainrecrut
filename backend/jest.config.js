/** @type {import('jest').Config} */
const base = {
  testEnvironment: "node",

  // Compile les fichiers TypeScript avec ts-jest
  transform: {
    "^.+\\.ts$": ["ts-jest", { tsconfig: "tsconfig.test.json" }],
  },

  // Variables d'environnement de test, chargées avant chaque fichier
  setupFiles: ["<rootDir>/tests/setup/env.ts"],

  // Couverture : uniquement le code applicatif
  collectCoverageFrom: [
    "src/**/*.ts",
    "!src/server.ts", // démarre seulement le serveur
    "!src/docs/**", // contenu Swagger
    "!src/types/**", // déclarations de types
  ],
};

module.exports = {
  projects: [
    {
      ...base,
      displayName: "unit",
      testMatch: ["<rootDir>/tests/unit/**/*.test.ts"],
      // Prisma est remplacé par un faux client (aucune base de données)
      setupFilesAfterEnv: ["<rootDir>/tests/setup/prisma-mock.ts"],
    },
    {
      ...base,
      displayName: "integration",
      testMatch: ["<rootDir>/tests/integration/**/*.test.ts"],
    },
  ],

  coverageDirectory: "coverage",
  coverageReporters: ["text", "lcov"], // lcov.info est lu par SonarQube

  // Rapport JUnit pour Jenkins (reports/junit.xml)
  reporters: [
    "default",
    ["jest-junit", { outputDirectory: "reports", outputName: "junit.xml" }],
  ],
};
