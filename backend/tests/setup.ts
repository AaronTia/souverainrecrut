import { mockReset } from "jest-mock-extended";

/**
 * Variables d'environnement de test.
 * Elles doivent être définies avant le chargement de src/config/env.ts.
 */
process.env.NODE_ENV = "test";
process.env.JWT_SECRET = "test-secret";
process.env.API_VERSION = "v1";

/**
 * Prisma est remplacé par un mock :
 * aucune base PostgreSQL n'est nécessaire pour exécuter les tests.
 */
jest.mock("../src/config/prisma", () => ({
  prisma: require("./helpers/prisma.mock").prismaMock,
}));

beforeEach(() => {
  const { prismaMock } = require("./helpers/prisma.mock");
  mockReset(prismaMock);
});
