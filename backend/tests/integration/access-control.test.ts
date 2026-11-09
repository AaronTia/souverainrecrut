import jwt from "jsonwebtoken";
import request from "supertest";

import app from "../../src/app";
import { prismaMock } from "../helpers/prisma.mock";
import { adminToken, recruiterToken } from "../helpers/auth";

describe("Authentification (authMiddleware)", () => {
  it("refuse une requête sans en-tête Authorization (401)", async () => {
    const res = await request(app).get("/v1/candidates");

    expect(res.status).toBe(401);
    expect(res.body.error.message).toBe("Authentification requise.");
  });

  it("refuse un schéma autre que Bearer (401)", async () => {
    const res = await request(app)
      .get("/v1/candidates")
      .set("Authorization", "Basic abc");

    expect(res.status).toBe(401);
    expect(res.body.error.message).toBe("Token invalide.");
  });

  it("refuse un token signé avec une autre clé (401)", async () => {
    const forged = jwt.sign({ id: "x", role: "ADMIN" }, "autre-secret");

    const res = await request(app)
      .get("/v1/candidates")
      .set("Authorization", `Bearer ${forged}`);

    expect(res.status).toBe(401);
    expect(res.body.error.message).toBe("Token invalide ou expiré.");
  });

  it("refuse un token expiré (401)", async () => {
    const expired = jwt.sign({ id: "x", role: "ADMIN" }, "test-secret", {
      expiresIn: -10,
    });

    const res = await request(app)
      .get("/v1/candidates")
      .set("Authorization", `Bearer ${expired}`);

    expect(res.status).toBe(401);
    expect(res.body.error.message).toBe("Token invalide ou expiré.");
  });
});

describe("Autorisation par rôle (authorize)", () => {
  it.each([
    ["del", "/v1/candidates/c1"],
    ["del", "/v1/jobs/j1"],
    ["del", "/v1/applications/a1"],
    ["get", "/v1/users"],
    ["post", "/v1/users"],
    ["put", "/v1/users/u1"],
  ] as const)(
    "un RECRUITER ne peut pas faire %s %s (403)",
    async (method, url) => {
      const http = request(app) as unknown as Record<
        string,
        (u: string) => request.Test
      >;
      const res = await http[method](url).set(
        "Authorization",
        recruiterToken()
      );

      expect(res.status).toBe(403);
      expect(res.body.error.message).toBe(
        "Accès refusé. Permissions insuffisantes."
      );
    }
  );

  it("un RECRUITER peut consulter les candidats", async () => {
    prismaMock.candidate.findMany.mockResolvedValue([]);
    prismaMock.candidate.count.mockResolvedValue(0);

    const res = await request(app)
      .get("/v1/candidates")
      .set("Authorization", recruiterToken());

    expect(res.status).toBe(200);
  });

  it("un ADMIN peut consulter les utilisateurs", async () => {
    prismaMock.user.findMany.mockResolvedValue([]);
    prismaMock.user.count.mockResolvedValue(0);

    const res = await request(app)
      .get("/v1/users")
      .set("Authorization", adminToken());

    expect(res.status).toBe(200);
  });
});
