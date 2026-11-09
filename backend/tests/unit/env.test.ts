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

  it("applique les défauts de nodeEnv, jwtSecret et apiVersion si absents", () => {
    const saved = {
      NODE_ENV: process.env.NODE_ENV,
      JWT_SECRET: process.env.JWT_SECRET,
      API_VERSION: process.env.API_VERSION,
    };
    delete process.env.NODE_ENV;
    delete process.env.JWT_SECRET;
    delete process.env.API_VERSION;
    try {
      jest.isolateModules(() => {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const { env: defaultEnv } = require("../../src/config/env");
        expect(defaultEnv.nodeEnv).toBe("development");
        expect(defaultEnv.jwtSecret).toBe("");
        expect(defaultEnv.apiVersion).toBe("v1");
      });
    } finally {
      for (const [key, value] of Object.entries(saved)) {
        if (value === undefined) delete process.env[key];
        else process.env[key] = value;
      }
    }
  });

  it("utilise les variables d'environnement quand elles sont définies", () => {
    const saved = {
      PORT: process.env.PORT,
      DATABASE_URL: process.env.DATABASE_URL,
      FRONTEND_URL: process.env.FRONTEND_URL,
    };
    process.env.PORT = "5000";
    process.env.DATABASE_URL = "postgresql://user:pass@localhost:5432/db";
    process.env.FRONTEND_URL = "http://localhost:3000";
    try {
      jest.isolateModules(() => {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const { env: customEnv } = require("../../src/config/env");
        expect(customEnv.port).toBe(5000);
        expect(customEnv.databaseUrl).toBe(
          "postgresql://user:pass@localhost:5432/db"
        );
        expect(customEnv.frontendUrl).toBe("http://localhost:3000");
      });
    } finally {
      for (const [key, value] of Object.entries(saved)) {
        if (value === undefined) delete process.env[key];
        else process.env[key] = value;
      }
    }
  });
});
