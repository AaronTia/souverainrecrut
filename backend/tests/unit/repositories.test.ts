import { ApplicationStatus } from "@prisma/client";

import { ApplicationRepository } from "../../src/repositories/application.repository";
import { BaseRepository } from "../../src/repositories/base.repository";
import { CandidateRepository } from "../../src/repositories/candidate.repository";
import { DashboardRepository } from "../../src/repositories/dashboard.repository";
import { JobRepository } from "../../src/repositories/job.repository";
import { UserRepository } from "../../src/repositories/user.repository";
import { prismaMock } from "../setup/prisma-mock";

describe("BaseRepository", () => {
  it("expose le client Prisma partagé", () => {
    class TestRepository extends BaseRepository {
      get client() {
        return this.prisma;
      }
    }
    expect(new TestRepository().client).toBe(prismaMock);
  });
});

describe("UserRepository", () => {
  const repo = new UserRepository();

  it("findAll pagine avec findMany + count", async () => {
    prismaMock.user.findMany.mockResolvedValue([]);
    prismaMock.user.count.mockResolvedValue(0);

    const result = await repo.findAll(10, 5);

    expect(result).toEqual({ items: [], total: 0 });
    expect(prismaMock.user.findMany).toHaveBeenCalledWith({
      skip: 10,
      take: 5,
      orderBy: { createdAt: "desc" },
    });
    expect(prismaMock.user.count).toHaveBeenCalledWith();

    await repo.findAll();
    expect(prismaMock.user.findMany).toHaveBeenLastCalledWith({
      skip: 0,
      take: 10,
      orderBy: { createdAt: "desc" },
    });
  });

  it("findById / findByEmail / findProfile interrogent findUnique", async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);

    await repo.findById("u1");
    expect(prismaMock.user.findUnique).toHaveBeenCalledWith({
      where: { id: "u1" },
    });

    await repo.findByEmail("a@b.fr");
    expect(prismaMock.user.findUnique).toHaveBeenCalledWith({
      where: { email: "a@b.fr" },
    });

    await repo.findProfile("u1");
    expect(prismaMock.user.findUnique).toHaveBeenCalledWith({
      where: { id: "u1" },
      select: {
        id: true,
        firstName: true,
        lastName: true,
        email: true,
        role: true,
        createdAt: true,
        updatedAt: true,
      },
    });
  });

  it("create / update / delete appellent le client Prisma", async () => {
    prismaMock.user.create.mockResolvedValue({} as never);
    prismaMock.user.update.mockResolvedValue({} as never);
    prismaMock.user.delete.mockResolvedValue({} as never);

    const data = { email: "a@b.fr" } as never;
    await repo.create(data);
    expect(prismaMock.user.create).toHaveBeenCalledWith({ data });

    await repo.update("u1", { firstName: "Grace" } as never);
    expect(prismaMock.user.update).toHaveBeenCalledWith({
      where: { id: "u1" },
      data: { firstName: "Grace" },
    });

    await repo.delete("u1");
    expect(prismaMock.user.delete).toHaveBeenCalledWith({
      where: { id: "u1" },
    });
  });
});

describe("CandidateRepository", () => {
  const repo = new CandidateRepository();

  it("couvre findAll, findById, findByEmail, create, update et delete", async () => {
    prismaMock.candidate.findMany.mockResolvedValue([]);
    prismaMock.candidate.count.mockResolvedValue(0);
    prismaMock.candidate.findUnique.mockResolvedValue(null);
    prismaMock.candidate.create.mockResolvedValue({} as never);
    prismaMock.candidate.update.mockResolvedValue({} as never);
    prismaMock.candidate.delete.mockResolvedValue({} as never);

    await repo.findAll(0, 10);
    expect(prismaMock.candidate.findMany).toHaveBeenCalledWith({
      skip: 0,
      take: 10,
      orderBy: { createdAt: "desc" },
    });

    await repo.findAll();
    expect(prismaMock.candidate.findMany).toHaveBeenLastCalledWith({
      skip: 0,
      take: 10,
      orderBy: { createdAt: "desc" },
    });

    await repo.findById("c1");
    expect(prismaMock.candidate.findUnique).toHaveBeenCalledWith({
      where: { id: "c1" },
    });

    await repo.findByEmail("jean@test.fr");
    expect(prismaMock.candidate.findUnique).toHaveBeenCalledWith({
      where: { email: "jean@test.fr" },
    });

    await repo.create({ email: "jean@test.fr" } as never);
    expect(prismaMock.candidate.create).toHaveBeenCalled();

    await repo.update("c1", { phone: "0700" } as never);
    expect(prismaMock.candidate.update).toHaveBeenCalledWith({
      where: { id: "c1" },
      data: { phone: "0700" },
    });

    await repo.delete("c1");
    expect(prismaMock.candidate.delete).toHaveBeenCalledWith({
      where: { id: "c1" },
    });
  });
});

describe("JobRepository", () => {
  const repo = new JobRepository();

  it("couvre findAll, findById, create, update et delete", async () => {
    prismaMock.job.findMany.mockResolvedValue([]);
    prismaMock.job.count.mockResolvedValue(0);
    prismaMock.job.findUnique.mockResolvedValue(null);
    prismaMock.job.create.mockResolvedValue({} as never);
    prismaMock.job.update.mockResolvedValue({} as never);
    prismaMock.job.delete.mockResolvedValue({} as never);

    await repo.findAll(0, 10);
    expect(prismaMock.job.findMany).toHaveBeenCalledWith({
      skip: 0,
      take: 10,
      orderBy: { createdAt: "desc" },
    });

    await repo.findAll();
    expect(prismaMock.job.findMany).toHaveBeenLastCalledWith({
      skip: 0,
      take: 10,
      orderBy: { createdAt: "desc" },
    });

    await repo.findById("j1");
    expect(prismaMock.job.findUnique).toHaveBeenCalledWith({
      where: { id: "j1" },
    });

    await repo.create({ title: "Dev" } as never);
    expect(prismaMock.job.create).toHaveBeenCalled();

    await repo.update("j1", { title: "DevOps" } as never);
    expect(prismaMock.job.update).toHaveBeenCalledWith({
      where: { id: "j1" },
      data: { title: "DevOps" },
    });

    await repo.delete("j1");
    expect(prismaMock.job.delete).toHaveBeenCalledWith({ where: { id: "j1" } });
  });
});

describe("ApplicationRepository", () => {
  const repo = new ApplicationRepository();

  it("couvre findAll, findById, create, update, updateStatus et delete", async () => {
    prismaMock.application.findMany.mockResolvedValue([]);
    prismaMock.application.count.mockResolvedValue(0);
    prismaMock.application.findUnique.mockResolvedValue(null);
    prismaMock.application.create.mockResolvedValue({} as never);
    prismaMock.application.update.mockResolvedValue({} as never);
    prismaMock.application.delete.mockResolvedValue({} as never);

    await repo.findAll(0, 10);
    expect(prismaMock.application.findMany).toHaveBeenCalledWith({
      skip: 0,
      take: 10,
      orderBy: { createdAt: "desc" },
      include: { candidate: true, job: true },
    });

    await repo.findAll();
    expect(prismaMock.application.findMany).toHaveBeenLastCalledWith({
      skip: 0,
      take: 10,
      orderBy: { createdAt: "desc" },
      include: { candidate: true, job: true },
    });

    await repo.findById("a1");
    expect(prismaMock.application.findUnique).toHaveBeenCalledWith({
      where: { id: "a1" },
      include: { candidate: true, job: true },
    });

    await repo.create({ candidateId: "c1", jobId: "j1" } as never);
    expect(prismaMock.application.create).toHaveBeenCalledWith({
      data: { candidateId: "c1", jobId: "j1" },
      include: { candidate: true, job: true },
    });

    await repo.update("a1", { status: ApplicationStatus.REVIEWED } as never);
    expect(prismaMock.application.update).toHaveBeenCalledWith({
      where: { id: "a1" },
      data: { status: ApplicationStatus.REVIEWED },
      include: { candidate: true, job: true },
    });

    await repo.updateStatus("a1", ApplicationStatus.ACCEPTED);
    expect(prismaMock.application.update).toHaveBeenCalledWith({
      where: { id: "a1" },
      data: { status: ApplicationStatus.ACCEPTED },
      include: { candidate: true, job: true },
    });

    await repo.delete("a1");
    expect(prismaMock.application.delete).toHaveBeenCalledWith({
      where: { id: "a1" },
    });
  });
});

describe("DashboardRepository", () => {
  it("agrège les compteurs de toutes les tables", async () => {
    prismaMock.user.count.mockResolvedValue(2);
    prismaMock.candidate.count.mockResolvedValue(10);
    prismaMock.job.count.mockResolvedValue(4);
    prismaMock.application.count
      .mockResolvedValueOnce(7)
      .mockResolvedValueOnce(3);

    const stats = await new DashboardRepository().getStatistics();

    expect(stats).toEqual({
      users: 2,
      candidates: 10,
      jobs: 4,
      applications: 7,
      pendingApplications: 3,
    });
    expect(prismaMock.application.count).toHaveBeenLastCalledWith({
      where: { status: ApplicationStatus.PENDING },
    });
  });
});
