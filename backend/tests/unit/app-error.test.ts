import { AppError } from "../../src/errors/app.error";

describe("AppError", () => {
  it("utilise 500 par défaut et marque l'erreur comme opérationnelle", () => {
    const error = new AppError("erreur");

    expect(error.message).toBe("erreur");
    expect(error.statusCode).toBe(500);
    expect(error.isOperational).toBe(true);
    expect(error).toBeInstanceOf(Error);
    expect(error.stack).toBeDefined();
  });

  it("accepte un code de statut personnalisé", () => {
    const error = new AppError("introuvable", 404);

    expect(error.statusCode).toBe(404);
    expect(error.isOperational).toBe(true);
  });
});
