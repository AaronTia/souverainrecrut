import request from "supertest";

import app from "../../src/app";

const allowedOrigin = "http://localhost:5173"; // FRONTEND_URL par défaut (src/config/env.ts)

describe("CORS", () => {
  it("autorise l'origine du frontend configuré avec les credentials", async () => {
    const res = await request(app).get("/v1/health").set("Origin", allowedOrigin);

    expect(res.status).toBe(200);
    expect(res.headers["access-control-allow-origin"]).toBe(allowedOrigin);
    expect(res.headers["access-control-allow-credentials"]).toBe("true");
  });

  it("ne reflète jamais une origine étrangère (le navigateur bloquera la réponse)", async () => {
    const evil = "https://site-malveillant.example";
    const res = await request(app).get("/v1/health").set("Origin", evil);

    expect(res.status).toBe(200);
    expect(res.headers["access-control-allow-origin"]).not.toBe(evil);
    expect(res.headers["access-control-allow-origin"]).toBe(allowedOrigin);
  });

  it("répond au preflight OPTIONS pour l'origine autorisée", async () => {
    const res = await request(app)
      .options("/v1/candidates")
      .set("Origin", allowedOrigin)
      .set("Access-Control-Request-Method", "POST")
      .set("Access-Control-Request-Headers", "Authorization, Content-Type");

    expect(res.status).toBe(204);
    expect(res.headers["access-control-allow-origin"]).toBe(allowedOrigin);
    expect(res.headers["access-control-allow-methods"]).toContain("POST");
  });
});
