/**
 *
 * Chaque test décrit le comportement ATTENDU et est marqué `it.failing` :
 *   - aujourd'hui il échoue (le défaut est présent)  -> Jest le compte comme réussi
 *   - le jour où le défaut est corrigé, il passe     -> Jest le signale en échec,
 *     il faut alors retirer `.failing` : la dette ne peut pas être oubliée.
 *
 */
import request from "supertest";
import { Prisma, Role, User } from "@prisma/client";

import app from "../../src/app";
import { prismaMock } from "../setup/prisma-mock";
import { adminToken, recruiterToken } from "../helpers/auth";

const user: User = {
  id: "u1",
  firstName: "Ada",
  lastName: "Lovelace",
  email: "ada@test.fr",
  password: "$2b$10$hash-bcrypt-de-test",
  role: Role.ADMIN,
  createdAt: new Date("2026-01-01"),
  updatedAt: new Date("2026-01-01"),
};

describe("Défauts connus – sécurité des utilisateurs", () => {
  it.failing("PUT /v1/users/:id re-hashe le mot de passe (aujourd'hui stocké en clair)", async () => {
    prismaMock.user.findUnique.mockResolvedValue(user);
    prismaMock.user.update.mockResolvedValue(user);

    await request(app)
      .put("/v1/users/u1")
      .set("Authorization", adminToken())
      .send({ password: "NouveauMotDePasse1!" });

    const { data } = prismaMock.user.update.mock.calls[0][0] as {
      data: { password?: string };
    };
    expect(data.password).toBeDefined();
    expect(data.password).not.toBe("NouveauMotDePasse1!");
  });

  it.failing("GET /v1/users n'expose pas le hash des mots de passe", async () => {
    prismaMock.user.findMany.mockResolvedValue([user]);
    prismaMock.user.count.mockResolvedValue(1);

    const res = await request(app)
      .get("/v1/users")
      .set("Authorization", adminToken());

    expect(res.status).toBe(200);
    expect(res.body.data[0].password).toBeUndefined();
  });

  it.failing("GET /v1/users/:id n'expose pas le hash du mot de passe", async () => {
    prismaMock.user.findUnique.mockResolvedValue(user);

    const res = await request(app)
      .get("/v1/users/u1")
      .set("Authorization", adminToken());

    expect(res.status).toBe(200);
    expect(res.body.data.password).toBeUndefined();
  });
});

describe("Défauts connus – validation des entrées", () => {
  it.failing("POST /v1/auth/login sans corps répond 400 (aujourd'hui aucune validation sur la route)", async () => {
    const res = await request(app).post("/v1/auth/login").send({});

    expect(res.status).toBe(400);
    expect(res.body.error.message).toBe("Erreur de validation.");
  });

  it.failing("GET /v1/jobs?page=abc retombe sur la page 1 (aujourd'hui page/skip valent NaN)", async () => {
    prismaMock.job.findMany.mockResolvedValue([]);
    prismaMock.job.count.mockResolvedValue(0);

    const res = await request(app)
      .get("/v1/jobs?page=abc&limit=xyz")
      .set("Authorization", recruiterToken());

    expect(res.status).toBe(200);
    expect(res.body.pagination).toMatchObject({ page: 1, limit: 10 });
    expect(prismaMock.job.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ skip: 0, take: 10 })
    );
  });
});

describe("Défauts connus – erreurs base de données et droits", () => {
  it.failing("POST /v1/applications avec un candidat inexistant répond 4xx (aujourd'hui 500 : erreur P2003 non gérée)", async () => {
    const consoleError = jest.spyOn(console, "error").mockImplementation(() => undefined);
    prismaMock.application.create.mockRejectedValue(
      new Prisma.PrismaClientKnownRequestError("Foreign key constraint failed", {
        code: "P2003",
        clientVersion: "test",
      })
    );

    const res = await request(app)
      .post("/v1/applications")
      .set("Authorization", recruiterToken())
      .send({ candidateId: "inexistant", jobId: "j1" });

    consoleError.mockRestore();
    expect([400, 404, 409]).toContain(res.status);
  });

  it.failing("un RECRUITER ne peut pas créer une offre au nom d'un autre recruteur (aujourd'hui aucun contrôle de propriété)", async () => {
    prismaMock.job.create.mockResolvedValue({} as never);

    const res = await request(app)
      .post("/v1/jobs")
      .set("Authorization", recruiterToken()) // id = recruiter-1
      .send({
        title: "Développeur Fullstack",
        description: "Une description suffisamment longue.",
        location: "Paris",
        company: "SouverainRecrut",
        recruiterId: "recruiter-2",
      });

    expect(res.status).toBe(403);
    expect(prismaMock.job.create).not.toHaveBeenCalled();
  });
});
