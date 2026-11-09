import request from "supertest";
import { Application, ApplicationStatus } from "@prisma/client";

import app from "../../src/app";
import { prismaMock } from "../setup/prisma-mock";
import { adminToken, recruiterToken } from "../helpers/auth";

const application: Application = {
  id: "a1",
  candidateId: "c1",
  jobId: "j1",
  status: ApplicationStatus.PENDING,
  createdAt: new Date("2026-01-01"),
  updatedAt: new Date("2026-01-01"),
};

describe("Applications", () => {
  it("GET /v1/applications retourne une liste paginée", async () => {
    prismaMock.application.findMany.mockResolvedValue([application]);
    prismaMock.application.count.mockResolvedValue(8);

    const res = await request(app)
      .get("/v1/applications?page=1&limit=5")
      .set("Authorization", recruiterToken());

    expect(res.status).toBe(200);
    expect(res.body.pagination).toEqual({
      page: 1,
      limit: 5,
      total: 8,
      totalPages: 2,
    });
    expect(prismaMock.application.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ skip: 0, take: 5 })
    );
  });

  it("GET /v1/applications/:id retourne la candidature ou 404", async () => {
    prismaMock.application.findUnique.mockResolvedValue(application);
    const ok = await request(app)
      .get("/v1/applications/a1")
      .set("Authorization", recruiterToken());
    expect(ok.status).toBe(200);
    expect(ok.body.data.status).toBe(ApplicationStatus.PENDING);

    prismaMock.application.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .get("/v1/applications/inconnu")
      .set("Authorization", recruiterToken());
    expect(ko.status).toBe(404);
    expect(ko.body.error.message).toBe("Candidature introuvable.");
  });

  it("POST /v1/applications crée une candidature (201)", async () => {
    prismaMock.application.create.mockResolvedValue(application);

    const res = await request(app)
      .post("/v1/applications")
      .set("Authorization", recruiterToken())
      .send({ candidateId: "c1", jobId: "j1" });

    expect(res.status).toBe(201);
    expect(prismaMock.application.create).toHaveBeenCalledWith({
      data: { candidateId: "c1", jobId: "j1" },
      include: { candidate: true, job: true },
    });
  });

  it("POST /v1/applications refuse des données invalides (400)", async () => {
    const res = await request(app)
      .post("/v1/applications")
      .set("Authorization", recruiterToken())
      .send({ status: "BIDON" });

    expect(res.status).toBe(400);
    const fields = res.body.error.details.map(
      (d: { field: string }) => d.field
    );
    expect(fields).toEqual(
      expect.arrayContaining(["candidateId", "jobId", "status"])
    );
  });

  it("PUT /v1/applications/:id met à jour le statut (200) ou 404", async () => {
    prismaMock.application.findUnique.mockResolvedValue(application);
    prismaMock.application.update.mockResolvedValue({
      ...application,
      status: ApplicationStatus.ACCEPTED,
    });

    const ok = await request(app)
      .put("/v1/applications/a1")
      .set("Authorization", recruiterToken())
      .send({ status: "ACCEPTED" });
    expect(ok.status).toBe(200);
    expect(ok.body.data.status).toBe(ApplicationStatus.ACCEPTED);

    prismaMock.application.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .put("/v1/applications/inconnu")
      .set("Authorization", recruiterToken())
      .send({ status: "ACCEPTED" });
    expect(ko.status).toBe(404);
    expect(prismaMock.application.update).toHaveBeenCalledTimes(1);
  });

  it("PUT /v1/applications/:id refuse un statut invalide (400)", async () => {
    const res = await request(app)
      .put("/v1/applications/a1")
      .set("Authorization", recruiterToken())
      .send({ status: "BIDON" });

    expect(res.status).toBe(400);
  });

  it("DELETE /v1/applications/:id supprime la candidature (ADMIN) ou 404", async () => {
    prismaMock.application.findUnique.mockResolvedValue(application);
    prismaMock.application.delete.mockResolvedValue(application);

    const ok = await request(app)
      .del("/v1/applications/a1")
      .set("Authorization", adminToken());
    expect(ok.status).toBe(200);
    expect(prismaMock.application.delete).toHaveBeenCalledWith({
      where: { id: "a1" },
    });

    prismaMock.application.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .del("/v1/applications/inconnu")
      .set("Authorization", adminToken());
    expect(ko.status).toBe(404);
  });
});
