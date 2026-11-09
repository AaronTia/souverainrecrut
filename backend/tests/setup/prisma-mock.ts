import { PrismaClient } from "@prisma/client";
import { mockDeep, mockReset, DeepMockProxy } from "jest-mock-extended";

import { prisma } from "../../src/config/prisma";

jest.mock("../../src/config/prisma", () => ({
  prisma: mockDeep<PrismaClient>(),
}));

export const prismaMock = prisma as unknown as DeepMockProxy<PrismaClient>;

// Remet le faux Prisma à zéro avant chaque test,
// pour qu'un test n'influence jamais le suivant.
beforeEach(() => {
  mockReset(prismaMock);
});
