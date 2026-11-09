import bcrypt from "bcrypt";
import jwt from "jsonwebtoken";
import { ApplicationStatus, Role, User } from "@prisma/client";

import { AppError } from "../../src/errors/app.error";
import { ApplicationRepository } from "../../src/repositories/application.repository";
import { CandidateRepository } from "../../src/repositories/candidate.repository";
import { DashboardRepository } from "../../src/repositories/dashboard.repository";
import { JobRepository } from "../../src/repositories/job.repository";
import { UserRepository } from "../../src/repositories/user.repository";
import { ApplicationService } from "../../src/services/application.service";
import { AuthService } from "../../src/services/auth.service";
import { CandidateService } from "../../src/services/candidate.service";
import { DashboardService } from "../../src/services/dashboard.service";
import { HealthService } from "../../src/services/health.service";
import { InfoService } from "../../src/services/info.service";
import { JobService } from "../../src/services/job.service";
import { UserService } from "../../src/services/user.service";
import { prismaMock } from "../helpers/prisma.mock";

jest.mock("../../src/repositories/user.repository");
jest.mock("../../src/repositories/candidate.repository");
jest.mock("../../src/repositories/job.repository");
jest.mock("../../src/repositories/application.repository");
jest.mock("../../src/repositories/dashboard.repository");
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
    const payload = jwt.verify(result.token, "test-secret") as {
      id: string;
      role: Role;
    };
    expect(payload).toMatchObject({ id: "u1", role: Role.ADMIN });
  });
});

describe("CandidateService", () => {
  const service = new CandidateService();
  const repo = CandidateRepository.prototype as jest.Mocked<
    InstanceType<typeof CandidateRepository>
  >;
  const candidate = {
    id: "c1",
    fullName: "Jean Dupont",
    email: "jean@test.fr",
    phone: "0601020304",
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  it("getAll / getById / update / delete couvrent les cas nominaux et 404", async () => {
    repo.findAll.mockResolvedValue({ items: [candidate], total: 1 });
    await expect(service.getAll()).resolves.toEqual({
      items: [candidate],
      total: 1,
    });

    repo.findById.mockResolvedValue(candidate);
    await expect(service.getById("c1")).resolves.toEqual(candidate);
    repo.findById.mockResolvedValue(null);
    await expect(service.getById("inconnu")).rejects.toMatchObject({
      statusCode: 404,
      message: "Candidat introuvable.",
    });

    repo.findById.mockResolvedValue(candidate);
    repo.update.mockResolvedValue(candidate);
    repo.delete.mockResolvedValue(candidate);
    await expect(service.update("c1", { phone: "0700" })).resolves.toEqual(candidate);
    await expect(service.delete("c1")).resolves.toEqual(candidate);

    repo.findById.mockResolvedValue(null);
    await expect(service.update("inconnu", {})).rejects.toMatchObject({ statusCode: 404 });
    await expect(service.delete("inconnu")).rejects.toMatchObject({ statusCode: 404 });
  });

  it("create rejette un email déjà utilisé (409) puis crée le candidat", async () => {
    repo.findByEmail.mockResolvedValue(candidate);
    await expect(
      service.create({ fullName: "Jean Dupont", email: "jean@test.fr" })
    ).rejects.toMatchObject({ statusCode: 409 });

    repo.findByEmail.mockResolvedValue(null);
    repo.create.mockResolvedValue(candidate);
    await expect(
      service.create({ fullName: "Jean Dupont", email: "jean@test.fr" })
    ).resolves.toEqual(candidate);
  });
});

describe("JobService", () => {
  const service = new JobService();
  const repo = JobRepository.prototype as jest.Mocked<
    InstanceType<typeof JobRepository>
  >;
  const job = {
    id: "j1",
    title: "Dev Fullstack",
    description: "Description longue.",
    location: "Paris",
    company: "SouverainRecrut",
    recruiterId: "u1",
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  it("couvre getAll, getById (200/404), create, update et delete", async () => {
    repo.findAll.mockResolvedValue({ items: [job], total: 1 });
    await expect(service.getAll()).resolves.toEqual({
      items: [job],
      total: 1,
    });
    expect(repo.findAll).toHaveBeenCalledWith(0, 10);

    repo.findById.mockResolvedValue(job);
    await expect(service.getById("j1")).resolves.toEqual(job);
    repo.findById.mockResolvedValue(null);
    await expect(service.getById("inconnu")).rejects.toMatchObject({
      statusCode: 404,
      message: "Offre introuvable.",
    });

    repo.create.mockResolvedValue(job);
    await expect(service.create({ title: "Dev Fullstack" } as never)).resolves.toEqual(job);

    repo.findById.mockResolvedValue(job);
    repo.update.mockResolvedValue(job);
    repo.delete.mockResolvedValue(job);
    await expect(service.update("j1", { title: "x" })).resolves.toEqual(job);
    await expect(service.delete("j1")).resolves.toEqual(job);

    repo.findById.mockResolvedValue(null);
    await expect(service.update("inconnu", {})).rejects.toMatchObject({ statusCode: 404 });
    await expect(service.delete("inconnu")).rejects.toMatchObject({ statusCode: 404 });
  });
});

describe("ApplicationService", () => {
  const service = new ApplicationService();
  const repo = ApplicationRepository.prototype as jest.Mocked<
    InstanceType<typeof ApplicationRepository>
  >;
  const application = {
    id: "a1",
    candidateId: "c1",
    jobId: "j1",
    status: ApplicationStatus.PENDING,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  it("couvre getAll, getById (200/404), create, update, updateStatus et delete", async () => {
    repo.findAll.mockResolvedValue({ items: [application], total: 1 });
    await expect(service.getAll()).resolves.toEqual({
      items: [application],
      total: 1,
    });

    repo.findById.mockResolvedValue(application);
    await expect(service.getById("a1")).resolves.toEqual(application);
    repo.findById.mockResolvedValue(null);
    await expect(service.getById("inconnu")).rejects.toMatchObject({
      statusCode: 404,
      message: "Candidature introuvable.",
    });

    repo.create.mockResolvedValue(application);
    await expect(
      service.create({ candidateId: "c1", jobId: "j1" } as never)
    ).resolves.toEqual(application);

    repo.findById.mockResolvedValue(application);
    repo.update.mockResolvedValue(application);
    repo.updateStatus.mockResolvedValue({
      ...application,
      status: ApplicationStatus.ACCEPTED,
    });
    repo.delete.mockResolvedValue(application);

    await expect(
      service.update("a1", { status: ApplicationStatus.REVIEWED } as never)
    ).resolves.toEqual(application);
    expect(repo.update).toHaveBeenCalledWith("a1", {
      status: ApplicationStatus.REVIEWED,
    });

    await expect(
      service.updateStatus("a1", ApplicationStatus.ACCEPTED)
    ).resolves.toMatchObject({ status: ApplicationStatus.ACCEPTED });
    expect(repo.updateStatus).toHaveBeenCalledWith(
      "a1",
      ApplicationStatus.ACCEPTED
    );

    await expect(service.delete("a1")).resolves.toEqual(application);
    expect(repo.delete).toHaveBeenCalledWith("a1");

    repo.findById.mockResolvedValue(null);
    await expect(service.update("inconnu", {})).rejects.toMatchObject({ statusCode: 404 });
    await expect(service.updateStatus("inconnu", ApplicationStatus.PENDING)).rejects.toMatchObject({ statusCode: 404 });
    await expect(service.delete("inconnu")).rejects.toMatchObject({ statusCode: 404 });
  });
});

describe("DashboardService", () => {
  it("retourne les statistiques du repository", async () => {
    const stats = {
      users: 2,
      candidates: 10,
      jobs: 4,
      applications: 7,
      pendingApplications: 3,
    };
    const repo = DashboardRepository.prototype as jest.Mocked<
      InstanceType<typeof DashboardRepository>
    >;
    repo.getStatistics.mockResolvedValue(stats);

    await expect(new DashboardService().getStatistics()).resolves.toEqual(stats);
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

describe("InfoService", () => {
  it("retourne les informations de l'API", () => {
    expect(new InfoService().getInfo()).toMatchObject({
      name: "SouverainRecrut API",
      version: "1.0.0",
      environment: "test",
      apiVersion: "v1",
      documentation: "/api-docs",
      health: "/v1/health",
      readiness: "/v1/ready",
      node: process.version,
    });
  });
});
