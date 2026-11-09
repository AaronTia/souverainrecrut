import bcrypt from "bcrypt";
import request from "supertest";
import { Role, User } from "@prisma/client";

import app from "../../src/app";
import { prismaMock } from "../helpers/prisma.mock";
import { adminToken } from "../helpers/auth";

const user: User = {
  id: "u1",
  firstName: "Ada",
  lastName: "Lovelace",
  email: "ada@test.fr",
  password: "hashed",
  role: Role.ADMIN,
  createdAt: new Date("2026-01-01"),
  updatedAt: new Date("2026-01-01"),
};

const validPayload = {
  firstName: "Grace",
  lastName: "Hopper",
  email: "grace@test.fr",
  password: "Password123!",
  role: Role.RECRUITER,
};

describe("Users (ADMIN uniquement)", () => {
  it("GET /v1/users retourne une liste paginée", async () => {
    prismaMock.user.findMany.mockResolvedValue([user]);
    prismaMock.user.count.mockResolvedValue(12);

    const res = await request(app)
      .get("/v1/users?page=2&limit=5")
      .set("Authorization", adminToken());

    expect(res.status).toBe(200);
    expect(res.body.data).toHaveLength(1);
    expect(res.body.pagination).toEqual({
      page: 2,
      limit: 5,
      total: 12,
      totalPages: 3,
    });
    expect(prismaMock.user.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ skip: 5, take: 5 })
    );
  });

  it("GET /v1/users/:id retourne l'utilisateur ou 404", async () => {
    prismaMock.user.findUnique.mockResolvedValue(user);
    const ok = await request(app)
      .get("/v1/users/u1")
      .set("Authorization", adminToken());
    expect(ok.status).toBe(200);
    expect(ok.body.data.email).toBe(user.email);

    prismaMock.user.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .get("/v1/users/inconnu")
      .set("Authorization", adminToken());
    expect(ko.status).toBe(404);
    expect(ko.body.error.message).toBe("Utilisateur introuvable.");
  });

  it("POST /v1/users crée un utilisateur avec un mot de passe hashé (201)", async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);
    prismaMock.user.create.mockResolvedValue(user);

    const res = await request(app)
      .post("/v1/users")
      .set("Authorization", adminToken())
      .send(validPayload);

    expect(res.status).toBe(201);
    const createCall = prismaMock.user.create.mock.calls[0][0] as {
      data: { password: string };
    };
    expect(createCall.data.password).not.toBe(validPayload.password);
    expect(
      await bcrypt.compare(validPayload.password, createCall.data.password)
    ).toBe(true);
  });

  it("POST /v1/users refuse un email déjà utilisé (409)", async () => {
    prismaMock.user.findUnique.mockResolvedValue(user);

    const res = await request(app)
      .post("/v1/users")
      .set("Authorization", adminToken())
      .send(validPayload);

    expect(res.status).toBe(409);
    expect(res.body.error.message).toBe("Cet email est déjà utilisé.");
    expect(prismaMock.user.create).not.toHaveBeenCalled();
  });

  it("POST /v1/users refuse des données invalides (400)", async () => {
    const res = await request(app)
      .post("/v1/users")
      .set("Authorization", adminToken())
      .send({ firstName: "G", email: "invalide", password: "court" });

    expect(res.status).toBe(400);
    expect(res.body.error.message).toBe("Erreur de validation.");
    const fields = res.body.error.details.map(
      (d: { field: string }) => d.field
    );
    expect(fields).toEqual(
      expect.arrayContaining(["firstName", "email", "password"])
    );
  });

  it("PUT /v1/users/:id met à jour l'utilisateur (200) ou 404", async () => {
    prismaMock.user.findUnique.mockResolvedValue(user);
    prismaMock.user.update.mockResolvedValue({
      ...user,
      firstName: "Grace",
    });

    const ok = await request(app)
      .put("/v1/users/u1")
      .set("Authorization", adminToken())
      .send({ firstName: "Grace" });
    expect(ok.status).toBe(200);
    expect(ok.body.data.firstName).toBe("Grace");

    prismaMock.user.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .put("/v1/users/inconnu")
      .set("Authorization", adminToken())
      .send({ firstName: "Grace" });
    expect(ko.status).toBe(404);
    expect(prismaMock.user.update).toHaveBeenCalledTimes(1);
  });

  it("PUT /v1/users/:id refuse une donnée invalide (400)", async () => {
    const res = await request(app)
      .put("/v1/users/u1")
      .set("Authorization", adminToken())
      .send({ email: "invalide" });

    expect(res.status).toBe(400);
  });

  it("DELETE /v1/users/:id supprime l'utilisateur (200) ou 404", async () => {
    prismaMock.user.findUnique.mockResolvedValue(user);
    prismaMock.user.delete.mockResolvedValue(user);

    const ok = await request(app)
      .del("/v1/users/u1")
      .set("Authorization", adminToken());
    expect(ok.status).toBe(200);
    expect(prismaMock.user.delete).toHaveBeenCalledWith({
      where: { id: "u1" },
    });

    prismaMock.user.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .del("/v1/users/inconnu")
      .set("Authorization", adminToken());
    expect(ko.status).toBe(404);
  });
});
