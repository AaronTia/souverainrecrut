import request from "supertest";
import { Job } from "@prisma/client";

import app from "../../src/app";
import { prismaMock } from "../setup/prisma-mock";
import { adminToken, recruiterToken } from "../helpers/auth";

const job: Job = {
  id: "j1",
  title: "Développeur Fullstack",
  description: "Une description suffisamment longue.",
  location: "Paris",
  company: "SouverainRecrut",
  recruiterId: "recruiter-1",
  createdAt: new Date("2026-01-01"),
  updatedAt: new Date("2026-01-01"),
};

const validPayload = {
  title: "Développeur Fullstack",
  description: "Une description suffisamment longue.",
  location: "Paris",
  company: "SouverainRecrut",
  recruiterId: "recruiter-1",
};

describe("Jobs", () => {
  it("GET /v1/jobs retourne une liste paginée", async () => {
    prismaMock.job.findMany.mockResolvedValue([job]);
    prismaMock.job.count.mockResolvedValue(21);

    const res = await request(app)
      .get("/v1/jobs?page=3&limit=10")
      .set("Authorization", recruiterToken());

    expect(res.status).toBe(200);
    expect(res.body.pagination).toEqual({
      page: 3,
      limit: 10,
      total: 21,
      totalPages: 3,
    });
    expect(prismaMock.job.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ skip: 20, take: 10 })
    );
  });

  it("GET /v1/jobs/:id retourne l'offre ou 404", async () => {
    prismaMock.job.findUnique.mockResolvedValue(job);
    const ok = await request(app)
      .get("/v1/jobs/j1")
      .set("Authorization", recruiterToken());
    expect(ok.status).toBe(200);
    expect(ok.body.data.title).toBe(job.title);

    prismaMock.job.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .get("/v1/jobs/inconnu")
      .set("Authorization", recruiterToken());
    expect(ko.status).toBe(404);
    expect(ko.body.error.message).toBe("Offre introuvable.");
  });

  it("POST /v1/jobs crée une offre (201)", async () => {
    prismaMock.job.create.mockResolvedValue(job);

    const res = await request(app)
      .post("/v1/jobs")
      .set("Authorization", recruiterToken())
      .send(validPayload);

    expect(res.status).toBe(201);
    expect(prismaMock.job.create).toHaveBeenCalledWith({
      data: validPayload,
    });
  });

  it("POST /v1/jobs refuse des données invalides (400)", async () => {
    const res = await request(app)
      .post("/v1/jobs")
      .set("Authorization", recruiterToken())
      .send({ title: "D", description: "court" });

    expect(res.status).toBe(400);
    const fields = res.body.error.details.map(
      (d: { field: string }) => d.field
    );
    expect(fields).toEqual(
      expect.arrayContaining([
        "title",
        "description",
        "location",
        "company",
        "recruiterId",
      ])
    );
  });

  it("PUT /v1/jobs/:id met à jour l'offre (200) ou 404", async () => {
    prismaMock.job.findUnique.mockResolvedValue(job);
    prismaMock.job.update.mockResolvedValue({ ...job, location: "Lyon" });

    const ok = await request(app)
      .put("/v1/jobs/j1")
      .set("Authorization", recruiterToken())
      .send({ location: "Lyon" });
    expect(ok.status).toBe(200);
    expect(ok.body.data.location).toBe("Lyon");

    prismaMock.job.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .put("/v1/jobs/inconnu")
      .set("Authorization", recruiterToken())
      .send({ location: "Lyon" });
    expect(ko.status).toBe(404);
    expect(prismaMock.job.update).toHaveBeenCalledTimes(1);
  });

  it("PUT /v1/jobs/:id refuse une donnée invalide (400)", async () => {
    const res = await request(app)
      .put("/v1/jobs/j1")
      .set("Authorization", recruiterToken())
      .send({ title: "x" });

    expect(res.status).toBe(400);
  });

  it("DELETE /v1/jobs/:id supprime l'offre (ADMIN) ou 404", async () => {
    prismaMock.job.findUnique.mockResolvedValue(job);
    prismaMock.job.delete.mockResolvedValue(job);

    const ok = await request(app)
      .del("/v1/jobs/j1")
      .set("Authorization", adminToken());
    expect(ok.status).toBe(200);
    expect(prismaMock.job.delete).toHaveBeenCalledWith({
      where: { id: "j1" },
    });

    prismaMock.job.findUnique.mockResolvedValue(null);
    const ko = await request(app)
      .del("/v1/jobs/inconnu")
      .set("Authorization", adminToken());
    expect(ko.status).toBe(404);
  });
});
