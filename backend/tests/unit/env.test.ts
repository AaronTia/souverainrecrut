import { env } from "../../src/config/env";

describe("env", () => {
  it("charge les valeurs de test définies dans tests/setup.ts", () => {
    expect(env.nodeEnv).toBe("test");
    expect(env.jwtSecret).toBe("test-secret");
    expect(env.apiVersion).toBe("v1");
  });

  it("applique les valeurs par défaut quand les variables sont absentes", () => {
    expect(env.port).toBe(4500);
    expect(env.databaseUrl).toBe("");
    expect(env.frontendUrl).toBe("http://localhost:5173");
  });
});
