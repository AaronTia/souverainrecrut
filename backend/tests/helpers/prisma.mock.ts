import { PrismaClient } from "@prisma/client";

import { mockDeep } from "jest-mock-extended";

/**
 * Mock profond du client Prisma.
 * Toutes les méthodes (user.findUnique, $queryRaw, ...) sont des jest.fn().
 */
export const prismaMock = mockDeep<PrismaClient>();
