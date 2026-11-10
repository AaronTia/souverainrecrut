import request from "supertest";

import app from "../../src/app";
import { prismaMock } from "../setup/prisma-mock";
import { recruiterToken } from "../helpers/auth";

describe("Routes système", () => {
  it("GET / retourne le message d'accueil", async () => {
    const res = await request(app).get("/");

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      success: true,
      version: "1.0.0",
      api: "/v1",
      documentation: "/api-docs",
    });
  });

  it("GET /api-docs/ sert la documentation Swagger", async () => {
    const res = await request(app).get("/api-docs/");

    expect(res.status).toBe(200);
    expect(res.text).toContain("swagger");
  });

  it("GET /v1/info retourne les informations de l'API", async () => {
    const res = await request(app).get("/v1/info");

    expect(res.status).toBe(200);
    expect(res.body.data).toMatchObject({
      name: "SouverainRecrut API",
      version: "1.0.0",
      environment: "test",
      apiVersion: "v1",
      documentation: "/api-docs",
      health: "/v1/health",
      readiness: "/v1/ready",
    });
  });

  it("GET /v1/health retourne UP", async () => {
    const res = await request(app).get("/v1/health");

    expect(res.status).toBe(200);
    expect(res.body.data.status).toBe("UP");
    expect(res.body.data.environment).toBe("test");
  });

  it("GET /v1/ready retourne 200 quand la base répond", async () => {
    prismaMock.$queryRaw.mockResolvedValue([{ 1: 1 }] as never);

    const res = await request(app).get("/v1/ready");

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data).toMatchObject({
      status: "READY",
      database: "CONNECTED",
    });
  });

  it("GET /v1/ready retourne 503 quand la base est indisponible", async () => {
    prismaMock.$queryRaw.mockRejectedValue(new Error("ECONNREFUSED") as never);

    const res = await request(app).get("/v1/ready");

    expect(res.status).toBe(503);
    expect(res.body.success).toBe(false);
    expect(res.body.data).toMatchObject({
      status: "NOT_READY",
      database: "DISCONNECTED",
    });
  });

  it("GET /v1/dashboard/stats retourne les statistiques", async () => {
    prismaMock.user.count.mockResolvedValue(2);
    prismaMock.candidate.count.mockResolvedValue(10);
    prismaMock.job.count.mockResolvedValue(4);
    prismaMock.application.count
      .mockResolvedValueOnce(7)
      .mockResolvedValueOnce(3);

    const res = await request(app)
      .get("/v1/dashboard/stats")
      .set("Authorization", recruiterToken());

    expect(res.status).toBe(200);
    expect(res.body.data).toEqual({
      users: 2,
      candidates: 10,
      jobs: 4,
      applications: 7,
      pendingApplications: 3,
    });
    expect(prismaMock.application.count).toHaveBeenLastCalledWith({
      where: { status: "PENDING" },
    });
  });

  it("retourne 404 pour une route inconnue", async () => {
    const res = await request(app).get("/v1/inexistante");

    expect(res.status).toBe(404);
    expect(res.body.error.message).toBe("Route /v1/inexistante introuvable.");
  });

  it("retourne 500 sans détail technique sur une erreur inattendue", async () => {
    const consoleError = jest
      .spyOn(console, "error")
      .mockImplementation(() => undefined);
    prismaMock.job.findMany.mockRejectedValue(new Error("boom"));
    prismaMock.job.count.mockResolvedValue(0);

    const res = await request(app)
      .get("/v1/jobs")
      .set("Authorization", recruiterToken());

    expect(res.status).toBe(500);
    expect(res.body.error.message).toBe("Erreur interne du serveur.");
    expect(JSON.stringify(res.body)).not.toContain("boom");

    consoleError.mockRestore();
  });
});
