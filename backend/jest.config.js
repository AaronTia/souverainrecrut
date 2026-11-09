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
    "!src/config/prisma.ts", // remplacé par un mock dans les tests
    "!src/**/*.d.ts", // déclarations de types
    "!tests/**", // helpers de test
  ],

  // Objectif : 100% de couverture sur le code applicatif
  coverageThresholds: {
    global: {
      branches: 100,
      functions: 100,
      lines: 100,
      statements: 100,
    },
  },
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
      // Les tests d'intégration ont aussi besoin du faux client Prisma
      setupFilesAfterEnv: ["<rootDir>/tests/setup/prisma-mock.ts"],
    },
  ],

  coverageDirectory: "coverage",
  coverageReporters: ["text", "lcov", "html"], // lcov.info est lu par SonarQube

  // Objectif : 100% de couverture sur le code applicatif
  coverageThresholds: {
    global: {
      branches: 100,
      functions: 100,
      lines: 100,
      statements: 100,
    },
  },

  // Rapport JUnit pour Jenkins (reports/junit.xml)
  reporters: [
    "default",
    ["jest-junit", { outputDirectory: "reports", outputName: "junit.xml" }],
  ],
};
