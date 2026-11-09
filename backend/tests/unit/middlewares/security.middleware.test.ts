/**
 * Tests unitaires de sécurité des middlewares.
 *
 *   1. Injection de champs non prévus dans le corps (mass assignment)
 *   2. Token JWT non signé (algorithme "none") pour se faire passer pour ADMIN
 */
import { NextFunction, Request, Response } from "express";
import { Role } from "@prisma/client";

import { validate } from "../../../src/middlewares/validate.middleware";
import { authMiddleware } from "../../../src/middlewares/auth.middleware";
import { createCandidateSchema } from "../../../src/validators/candidate.schema";
import { AppError } from "../../../src/errors/app.error";

// ------------------------------------------------------------
// Fabriques de faux objets Express
// ------------------------------------------------------------
const mockRequest = (overrides: Partial<Request> = {}): Request =>
  ({ headers: {}, body: {}, ...overrides }) as Request;

const mockResponse = (): Response => {
  const res = {} as Response;
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  return res;
};

/** Construit un token JWT "alg: none" : en-tête + payload, sans signature. */
const unsignedToken = (payload: object): string => {
  const encode = (obj: object) =>
    Buffer.from(JSON.stringify(obj)).toString("base64url");

  return `${encode({ alg: "none", typ: "JWT" })}.${encode(payload)}.`;
};

describe("Sécurité des middlewares", () => {
  // ----------------------------------------------------------
  // CAS 1 : mass assignment
  // ----------------------------------------------------------
  it("validate() retire les champs non prévus par le schéma (id, createdAt, role) avant le contrôleur", () => {
    // Arrange : un attaquant ajoute des champs gérés par le serveur
    const req = mockRequest({
      body: {
        fullName: "Awa Diallo",
        email: "Awa@Example.com",
        id: "id-choisi-par-l-attaquant",
        createdAt: "2000-01-01T00:00:00.000Z",
        role: "ADMIN",
      },
    });
    const res = mockResponse();
    const next: NextFunction = jest.fn();

    // Act
    validate(createCandidateSchema)(req, res, next);

    // Assert : la requête passe, mais seuls les champs autorisés restent
    expect(next).toHaveBeenCalledWith();
    expect(req.body).toEqual({
      fullName: "Awa Diallo",
      email: "awa@example.com",
    });
    expect(req.body).not.toHaveProperty("id");
    expect(req.body).not.toHaveProperty("createdAt");
    expect(req.body).not.toHaveProperty("role");
  });

  // ----------------------------------------------------------
  // CAS 2 : token non signé (attaque "alg: none")
  // ----------------------------------------------------------
  it("authMiddleware refuse un token non signé (alg: none) qui se prétend ADMIN", () => {
    // Arrange : token forgé sans connaître le secret
    const forged = unsignedToken({ id: "attaquant", role: Role.ADMIN });
    const req = mockRequest({
      headers: { authorization: `Bearer ${forged}` },
    });
    const next = jest.fn();

    // Act
    authMiddleware(req, mockResponse(), next);

    // Assert : 401, et aucun utilisateur n'est attaché à la requête
    expect(next).toHaveBeenCalledWith(expect.any(AppError));
    expect(next.mock.calls[0][0]).toMatchObject({ statusCode: 401 });
    expect(req.user).toBeUndefined();
  });
});
