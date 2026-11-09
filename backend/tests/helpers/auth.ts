import jwt from "jsonwebtoken";

import { Role } from "@prisma/client";

/**
 * Génère un en-tête Authorization valide pour un rôle donné.
 * La clé utilisée est "test-secret" (définie dans tests/setup.ts).
 */
export const bearer = (role: Role, id = "user-1"): string =>
  `Bearer ${jwt.sign({ id, role }, "test-secret", { expiresIn: "1h" })}`;

export const adminToken = (): string => bearer(Role.ADMIN, "admin-1");

export const recruiterToken = (): string =>
  bearer(Role.RECRUITER, "recruiter-1");
