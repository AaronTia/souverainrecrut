import jwt from "jsonwebtoken";

import { Role } from "@prisma/client";

/**
 * Génère un en-tête Authorization valide pour un rôle donné.
 * La clé utilisée est process.env.JWT_SECRET (définie dans tests/setup/env.ts).
 */
export const bearer = (role: Role, id: string): string =>
  `Bearer ${jwt.sign({ id, role }, process.env.JWT_SECRET as string, { expiresIn: "1h" })}`;

export const adminToken = (): string => bearer(Role.ADMIN, "admin-1");

export const recruiterToken = (): string => bearer(Role.RECRUITER, "recruiter-1");
