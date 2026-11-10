/**
 * Services portant une vraie logique métier : hash du mot de passe, unicité d'email,
 * authentification, readiness. Les services de pure délégation (candidats, offres,
 * candidatures, dashboard, info) sont couverts par les tests d'intégration HTTP.
 */
import bcrypt from "bcrypt";
import { Role, User } from "@prisma/client";
import jwt from "jsonwebtoken";

import { AppError } from "../../src/errors/app.error";
import { UserRepository } from "../../src/repositories/user.repository";
import { AuthService } from "../../src/services/auth.service";
import { HealthService } from "../../src/services/health.service";
import { UserService } from "../../src/services/user.service";
import { prismaMock } from "../setup/prisma-mock";

jest.mock("../../src/repositories/user.repository");
jest.mock("bcrypt");

const bcryptMock = bcrypt as jest.Mocked<typeof bcrypt>;

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

beforeEach(() => {
  jest.clearAllMocks();
});

describe("UserService", () => {
  const service = new UserService();
  const repo = UserRepository.prototype as jest.Mocked<
    InstanceType<typeof UserRepository>
  >;

  it("getAll délègue au repository avec les valeurs par défaut", async () => {
    repo.findAll.mockResolvedValue({ items: [user], total: 1 });
    await expect(service.getAll()).resolves.toEqual({
      items: [user],
      total: 1,
    });
    expect(repo.findAll).toHaveBeenCalledWith(0, 10);

    await service.getAll(20, 5);
    expect(repo.findAll).toHaveBeenCalledWith(20, 5);
  });

  it("getById retourne l'utilisateur ou lève 404", async () => {
    repo.findById.mockResolvedValue(user);
    await expect(service.getById("u1")).resolves.toEqual(user);

    repo.findById.mockResolvedValue(null);
    await expect(service.getById("inconnu")).rejects.toMatchObject({
      statusCode: 404,
      message: "Utilisateur introuvable.",
    });
  });

  it("getProfile retourne le profil ou lève 404", async () => {
    const { password: _omit, ...profile } = user;
    repo.findProfile.mockResolvedValue(profile as User);
    await expect(service.getProfile("u1")).resolves.toEqual(profile);

    repo.findProfile.mockResolvedValue(null);
    await expect(service.getProfile("inconnu")).rejects.toBeInstanceOf(AppError);
  });

  it("create rejette un email déjà utilisé (409)", async () => {
    repo.findByEmail.mockResolvedValue(user);
    await expect(
      service.create({ ...user, password: "Password123!" })
    ).rejects.toMatchObject({ statusCode: 409 });
    expect(repo.create).not.toHaveBeenCalled();
  });

  it("create hashe le mot de passe avant de créer l'utilisateur", async () => {
    repo.findByEmail.mockResolvedValue(null);
    bcryptMock.hash.mockResolvedValue("hashed-password" as never);
    repo.create.mockResolvedValue(user);

    await service.create({ ...user, password: "Password123!" });

    expect(bcryptMock.hash).toHaveBeenCalledWith("Password123!", 10);
    expect(repo.create).toHaveBeenCalledWith({
      ...user,
      password: "hashed-password",
    });
  });

  it("update et delete lèvent 404 si l'utilisateur n'existe pas", async () => {
    repo.findById.mockResolvedValue(null);
    await expect(service.update("inconnu", {})).rejects.toMatchObject({
      statusCode: 404,
    });
    await expect(service.delete("inconnu")).rejects.toMatchObject({
      statusCode: 404,
    });
    expect(repo.update).not.toHaveBeenCalled();
    expect(repo.delete).not.toHaveBeenCalled();
  });

  it("update et delete délèguent au repository si l'utilisateur existe", async () => {
    repo.findById.mockResolvedValue(user);
    repo.update.mockResolvedValue(user);
    repo.delete.mockResolvedValue(user);

    await expect(service.update("u1", { firstName: "Grace" })).resolves.toEqual(user);
    await expect(service.delete("u1")).resolves.toEqual(user);
    expect(repo.update).toHaveBeenCalledWith("u1", { firstName: "Grace" });
    expect(repo.delete).toHaveBeenCalledWith("u1");
  });
});

describe("AuthService", () => {
  const service = new AuthService();
  const repo = UserRepository.prototype as jest.Mocked<
    InstanceType<typeof UserRepository>
  >;

  it("login lève 401 si l'email est inconnu", async () => {
    repo.findByEmail.mockResolvedValue(null);
    await expect(
      service.login("inconnu@test.fr", "Password123!")
    ).rejects.toMatchObject({
      statusCode: 401,
      message: "Email ou mot de passe invalide.",
    });
  });

  it("login lève 401 si le mot de passe est faux", async () => {
    repo.findByEmail.mockResolvedValue(user);
    bcryptMock.compare.mockResolvedValue(false as never);
    await expect(
      service.login("ada@test.fr", "mauvais")
    ).rejects.toMatchObject({ statusCode: 401 });
  });

  it("login retourne un token JWT et l'utilisateur sans mot de passe", async () => {
    repo.findByEmail.mockResolvedValue(user);
    bcryptMock.compare.mockResolvedValue(true as never);

    const result = await service.login("ada@test.fr", "Password123!");

    expect(result.user).toEqual({ ...user, password: undefined });
    expect((result.user as Record<string, unknown>).password).toBeUndefined();
    const payload = jwt.verify(result.token, process.env.JWT_SECRET as string) as {
      id: string;
      role: Role;
    };
    expect(payload).toMatchObject({ id: "u1", role: Role.ADMIN });
  });
});

describe("HealthService", () => {
  const service = new HealthService();

  it("health retourne UP avec les métadonnées", async () => {
    const result = await service.health();
    expect(result.status).toBe("UP");
    expect(result.environment).toBe("test");
    expect(typeof result.uptime).toBe("number");
    expect(typeof result.timestamp).toBe("string");
  });

  it("readiness retourne READY quand la base répond", async () => {
    prismaMock.$queryRaw.mockResolvedValue([{ 1: 1 }] as never);
    const result = await service.readiness();
    expect(result).toMatchObject({ status: "READY", database: "CONNECTED" });
  });

  it("readiness retourne NOT_READY quand la base est indisponible", async () => {
    prismaMock.$queryRaw.mockRejectedValue(new Error("ECONNREFUSED") as never);
    const result = await service.readiness();
    expect(result).toMatchObject({
      status: "NOT_READY",
      database: "DISCONNECTED",
    });
  });
});
