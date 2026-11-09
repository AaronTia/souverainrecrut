import request from "supertest";
import { Candidate } from "@prisma/client";

import app from "../../src/app";
import { prismaMock } from "../helpers/prisma.mock";
import { adminToken, recruiterToken } from "../helpers/auth";

const candidate: Candidate = {
  id: "c1",
  fullName: "Jean Dupont",
  email: "jean.dupont@test.fr",
  phone: "0601020304",
  createdAt: new Date("2026-01-01"),
  updatedAt: new Date("2026-01-01"),
};

describe("Candidats", () => {
  it("GET /v1/candidates retourne une liste paginée", async () => {
    prismaMock.candidate.findMany.mockResolvedValue([candidate]);
    prismaMock.candidate.count.mockResolvedValue(25);

    const res = await request(app)
      .get("/v1/candidates?page=2&limit=10")
      .set("Authorization", recruiterToken());

    expect(res.status).toBe(200);
    expect(res.body.data).toHaveLength(1);
    expect(res.body.pagination).toEqual({
      page: 2,
      limit: 10,
      total: 25,
      totalPages: 3,
    });
    expect(prismaMock.candidate.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ skip: 10, take: 10 })
    );
  });

  it("GET /v1/candidates/:id retourne le candidat ou 404", async () => {
    prismaMock.candidate.findUnique.mockResolvedValue(candidate);
    const ok = await request(app)
      .get("/v1/candidates/c1")
      .set("Authorization", recruiterToken());
    expect(ok.status).toBe(200);
    expect(ok.body.data.email).toBe(candidate.email);

    prismaMock.candidate.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .get("/v1/candidates/inconnu")
      .set("Authorization", recruiterToken());
    expect(ko.status).toBe(404);
    expect(ko.body.error.message).toBe("Candidat introuvable.");
  });

  it("POST /v1/candidates crée un candidat (email normalisé)", async () => {
    prismaMock.candidate.findUnique.mockResolvedValue(null);
    prismaMock.candidate.create.mockResolvedValue(candidate);

    const res = await request(app)
      .post("/v1/candidates")
      .set("Authorization", recruiterToken())
      .send({ fullName: "Jean Dupont", email: "Jean.Dupont@Test.fr" });

    expect(res.status).toBe(201);
    expect(prismaMock.candidate.create).toHaveBeenCalledWith({
      data: { fullName: "Jean Dupont", email: "jean.dupont@test.fr" },
    });
  });

  it("POST /v1/candidates refuse un email déjà utilisé (409)", async () => {
    prismaMock.candidate.findUnique.mockResolvedValue(candidate);

    const res = await request(app)
      .post("/v1/candidates")
      .set("Authorization", recruiterToken())
      .send({ fullName: "Jean Dupont", email: candidate.email });

    expect(res.status).toBe(409);
    expect(res.body.error.message).toBe(
      "Un candidat avec cet email existe déjà."
    );
    expect(prismaMock.candidate.create).not.toHaveBeenCalled();
  });

  it("POST /v1/candidates refuse des données invalides (400)", async () => {
    const res = await request(app)
      .post("/v1/candidates")
      .set("Authorization", recruiterToken())
      .send({ fullName: "J", email: "pas-un-email" });

    expect(res.status).toBe(400);
    const fields = res.body.error.details.map(
      (d: { field: string }) => d.field
    );
    expect(fields).toEqual(
      expect.arrayContaining(["fullName", "email"])
    );
  });

  it("PUT /v1/candidates/:id met à jour le candidat (200) ou 404", async () => {
    prismaMock.candidate.findUnique.mockResolvedValue(candidate);
    prismaMock.candidate.update.mockResolvedValue({
      ...candidate,
      phone: "0700000000",
    });

    const ok = await request(app)
      .put("/v1/candidates/c1")
      .set("Authorization", recruiterToken())
      .send({ phone: "0700000000" });
    expect(ok.status).toBe(200);
    expect(ok.body.data.phone).toBe("0700000000");

    prismaMock.candidate.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .put("/v1/candidates/inconnu")
      .set("Authorization", recruiterToken())
      .send({ phone: "0700000000" });
    expect(ko.status).toBe(404);
    expect(prismaMock.candidate.update).toHaveBeenCalledTimes(1);
  });

  it("DELETE /v1/candidates/:id supprime le candidat (ADMIN) ou 404", async () => {
    prismaMock.candidate.findUnique.mockResolvedValue(candidate);
    prismaMock.candidate.delete.mockResolvedValue(candidate);

    const ok = await request(app)
      .del("/v1/candidates/c1")
      .set("Authorization", adminToken());
    expect(ok.status).toBe(200);
    expect(prismaMock.candidate.delete).toHaveBeenCalledWith({
      where: { id: "c1" },
    });

    prismaMock.candidate.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .del("/v1/candidates/inconnu")
      .set("Authorization", adminToken());
    expect(ko.status).toBe(404);
  });
});
