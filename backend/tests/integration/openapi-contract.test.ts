/**
 * Contrat entre la documentation OpenAPI (src/docs, exclue de SonarQube)
 * et les routes réellement montées dans Express.
 *
 * Pour chaque opération documentée, la route doit exister : la réponse peut être
 * 401 (auth requise), 400, 200… mais jamais le 404 du notFoundMiddleware.
 */
import request from "supertest";

import app from "../../src/app";
import { swaggerSpec } from "../../src/docs/swagger";
import { prismaMock } from "../setup/prisma-mock";

type Method = "get" | "post" | "put" | "delete" | "patch";

const spec = swaggerSpec as {
  openapi: string;
  servers: { url: string }[];
  paths: Record<string, Partial<Record<Method, { security?: unknown[]; tags?: string[] }>>>;
};

const operations = Object.entries(spec.paths).flatMap(([path, methods]) =>
  (Object.keys(methods) as Method[]).map((method) => [method, path] as const)
);

describe("Contrat OpenAPI ↔ routes Express", () => {
  it("la spécification est en OpenAPI 3 et sert l'API sous /v1", () => {
    expect(spec.openapi).toMatch(/^3\./);
    expect(spec.servers[0].url).toMatch(/\/v1$/);
    expect(operations.length).toBeGreaterThanOrEqual(14);
  });

  it.each(operations)("%s %s est une route montée", async (method, path) => {
    prismaMock.$queryRaw.mockResolvedValue([{ 1: 1 }] as never);
    const url = "/v1" + path.replace(/\{[^}]+\}/g, "x");

    const res = await request(app)[method](url);

    const isRouteNotFound =
      res.status === 404 && /^Route .* introuvable\.$/.test(res.body?.error?.message ?? "");
    expect(isRouteNotFound).toBe(false);
  });

  it("toutes les opérations hors auth/info/health déclarent une sécurité bearer (héritée ou locale)", () => {
    const publicPaths = ["/auth/login", "/info", "/health", "/ready"];
    for (const [path, methods] of Object.entries(spec.paths)) {
      if (publicPaths.includes(path)) continue;
      for (const op of Object.values(methods)) {
        // security absent => héritage du `security` global (bearerAuth) ; [] => explicitement public
        expect(op?.security ?? [{ bearerAuth: [] }]).not.toEqual([]);
      }
    }
  });
});
