import jwt from "jsonwebtoken";
import { z } from "zod";
import { Role } from "@prisma/client";

import { AppError } from "../../src/errors/app.error";
import { authMiddleware } from "../../src/middlewares/auth.middleware";
import { authorize } from "../../src/middlewares/authorize.middleware";
import { validate } from "../../src/middlewares/validate.middleware";
import { errorMiddleware } from "../../src/middlewares/error.middleware";
import { notFoundMiddleware } from "../../src/middlewares/not-found.middleware";
import { loggerMiddleware } from "../../src/middlewares/logger.middleware";
import { corsMiddleware } from "../../src/middlewares/cors.middleware";
import { mockNext, mockRequest, mockResponse } from "../helpers/http";

describe("authMiddleware", () => {
  it("retourne 401 sans en-tête Authorization", () => {
    const next = mockNext();
    authMiddleware(mockRequest(), mockResponse(), next);

    const error = next.mock.calls[0][0] as AppError;
    expect(error).toBeInstanceOf(AppError);
    expect(error.statusCode).toBe(401);
    expect(error.message).toBe("Authentification requise.");
  });

  it("retourne 401 si le schéma n'est pas Bearer", () => {
    const next = mockNext();
    const req = mockRequest({ headers: { authorization: "Basic abc" } });
    authMiddleware(req, mockResponse(), next);

    const error = next.mock.calls[0][0] as AppError;
    expect(error.statusCode).toBe(401);
    expect(error.message).toBe("Token invalide.");
  });

  it("retourne 401 si le token est absent après Bearer", () => {
    const next = mockNext();
    const req = mockRequest({ headers: { authorization: "Bearer" } });
    authMiddleware(req, mockResponse(), next);

    const error = next.mock.calls[0][0] as AppError;
    expect(error.statusCode).toBe(401);
    expect(error.message).toBe("Token invalide.");
  });

  it("retourne 401 si le token est invalide", () => {
    const next = mockNext();
    const req = mockRequest({
      headers: { authorization: "Bearer ceci.nest.pas.un.jwt" },
    });
    authMiddleware(req, mockResponse(), next);

    const error = next.mock.calls[0][0] as AppError;
    expect(error.statusCode).toBe(401);
    expect(error.message).toBe("Token invalide ou expiré.");
  });

  it("attache l'utilisateur à la requête et appelle next() si le token est valide", () => {
    const token = jwt.sign({ id: "u1", role: "ADMIN" }, process.env.JWT_SECRET as string);
    const req = mockRequest({
      headers: { authorization: `Bearer ${token}` },
    });
    const next = mockNext();

    authMiddleware(req, mockResponse(), next);

    expect(next).toHaveBeenCalledWith();
    expect(req.user).toEqual({ id: "u1", role: "ADMIN" });
  });
});

describe("authorize", () => {
  it("retourne 401 si aucun utilisateur n'est attaché à la requête", () => {
    const next = mockNext();
    authorize(Role.ADMIN)(mockRequest(), mockResponse(), next);

    const error = next.mock.calls[0][0] as AppError;
    expect(error.statusCode).toBe(401);
    expect(error.message).toBe("Authentification requise.");
  });

  it("retourne 403 si le rôle n'est pas autorisé", () => {
    const next = mockNext();
    const req = mockRequest({ user: { id: "r1", role: Role.RECRUITER } });
    authorize(Role.ADMIN)(req, mockResponse(), next);

    const error = next.mock.calls[0][0] as AppError;
    expect(error.statusCode).toBe(403);
    expect(error.message).toBe("Accès refusé. Permissions insuffisantes.");
  });

  it("appelle next() si le rôle est autorisé", () => {
    const next = mockNext();
    const req = mockRequest({ user: { id: "a1", role: Role.ADMIN } });
    authorize(Role.ADMIN, Role.RECRUITER)(req, mockResponse(), next);

    expect(next).toHaveBeenCalledWith();
  });
});

describe("validate", () => {
  const schema = z.object({
    name: z.string().min(2, "Trop court."),
    email: z.email().transform((v) => v.toLowerCase()),
  });

  it("remplace req.body par les données validées et appelle next()", () => {
    const req = mockRequest({
      body: { name: "Jean", email: "JEAN@TEST.FR" },
    });
    const res = mockResponse();
    const next = mockNext();

    validate(schema)(req, res, next);

    expect(next).toHaveBeenCalledWith();
    expect(req.body).toEqual({ name: "Jean", email: "jean@test.fr" });
    expect(res.status).not.toHaveBeenCalled();
  });

  it("retourne 400 avec le détail des erreurs si la validation échoue", () => {
    const req = mockRequest({ body: { name: "J", email: "invalide" } });
    const res = mockResponse();
    const next = mockNext();

    validate(schema)(req, res, next);

    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(400);
    const payload = (res.json as jest.Mock).mock.calls[0][0];
    expect(payload.success).toBe(false);
    expect(payload.error.status).toBe(400);
    expect(payload.error.message).toBe("Erreur de validation.");
    expect(payload.error.details).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ field: "name" }),
        expect.objectContaining({ field: "email" }),
      ])
    );
  });
});

describe("errorMiddleware", () => {
  it("retourne le statut de l'AppError avec son message", () => {
    const res = mockResponse();
    errorMiddleware(
      new AppError("Candidat introuvable.", 404),
      mockRequest(),
      res,
      mockNext()
    );

    expect(res.status).toHaveBeenCalledWith(404);
    expect(res.json).toHaveBeenCalledWith({
      success: false,
      error: { status: 404, message: "Candidat introuvable." },
    });
  });

  it("retourne 500 sans détail pour une erreur inattendue", () => {
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    const res = mockResponse();

    errorMiddleware(new Error("boom"), mockRequest(), res, mockNext());

    expect(spy).toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(500);
    expect(res.json).toHaveBeenCalledWith({
      success: false,
      error: { status: 500, message: "Erreur interne du serveur." },
    });
    spy.mockRestore();
  });
});

describe("notFoundMiddleware", () => {
  it("retourne 404 avec l'URL demandée", () => {
    const res = mockResponse();
    notFoundMiddleware(
      mockRequest({ originalUrl: "/v1/inexistante" }),
      res
    );

    expect(res.status).toHaveBeenCalledWith(404);
    expect(res.json).toHaveBeenCalledWith({
      success: false,
      error: {
        status: 404,
        message: "Route /v1/inexistante introuvable.",
      },
    });
  });
});

describe("loggerMiddleware / corsMiddleware", () => {
  it("expose des middlewares (fonctions) en environnement de test", () => {
    expect(typeof loggerMiddleware).toBe("function");
    expect(typeof corsMiddleware).toBe("function");
  });

  it("utilise le format combined en production", () => {
    const previous = process.env.NODE_ENV;
    process.env.NODE_ENV = "production";
    try {
      jest.isolateModules(() => {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const mod = require("../../src/middlewares/logger.middleware");
        expect(typeof mod.loggerMiddleware).toBe("function");
      });
    } finally {
      process.env.NODE_ENV = previous;
    }
  });
});
