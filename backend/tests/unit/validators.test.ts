import { ApplicationStatus, Role } from "@prisma/client";

import {
  createApplicationSchema,
  updateApplicationSchema,
} from "../../src/validators/application.schema";
import {
  createCandidateSchema,
  updateCandidateSchema,
} from "../../src/validators/candidate.schema";
import {
  createJobSchema,
  updateJobSchema,
} from "../../src/validators/job.schema";
import {
  createUserSchema,
  updateUserSchema,
} from "../../src/validators/user.schema";

describe("user.schema", () => {
  const validUser = {
    firstName: "Ada",
    lastName: "Lovelace",
    email: "ada@test.fr",
    password: "Password123!",
  };

  it("valide une création complète (rôle optionnel)", () => {
    expect(createUserSchema.safeParse(validUser).success).toBe(true);
    expect(
      createUserSchema.safeParse({ ...validUser, role: Role.ADMIN }).success
    ).toBe(true);
  });

  it("rejette un email invalide, un mot de passe trop court ou un rôle inconnu", () => {
    const result = createUserSchema.safeParse({
      ...validUser,
      email: "invalide",
      password: "court",
      role: "SUPERADMIN",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const fields = result.error.issues.map((i) => i.path.join("."));
      expect(fields).toEqual(
        expect.arrayContaining(["email", "password", "role"])
      );
    }
  });

  it("valide une mise à jour partielle, y compris un objet vide", () => {
    expect(updateUserSchema.safeParse({}).success).toBe(true);
    expect(
      updateUserSchema.safeParse({ firstName: "Grace", role: Role.RECRUITER })
        .success
    ).toBe(true);
  });

  it("rejette une mise à jour invalide", () => {
    expect(updateUserSchema.safeParse({ firstName: "G" }).success).toBe(false);
    expect(updateUserSchema.safeParse({ password: "court" }).success).toBe(
      false
    );
  });
});

describe("candidate.schema", () => {
  it("valide un candidat et normalise l'email en minuscules", () => {
    const result = createCandidateSchema.safeParse({
      fullName: "Jean Dupont",
      email: "Jean.Dupont@Test.FR",
      phone: "0601020304",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.email).toBe("jean.dupont@test.fr");
    }
  });

  it("accepte l'absence de téléphone", () => {
    expect(
      createCandidateSchema.safeParse({
        fullName: "Jean Dupont",
        email: "jean@test.fr",
      }).success
    ).toBe(true);
  });

  it("rejette un nom trop court, un email invalide ou un téléphone invalide", () => {
    const result = createCandidateSchema.safeParse({
      fullName: "J",
      email: "invalide",
      phone: "123",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const fields = result.error.issues.map((i) => i.path.join("."));
      expect(fields).toEqual(
        expect.arrayContaining(["fullName", "email", "phone"])
      );
    }
  });

  it("valide une mise à jour partielle", () => {
    expect(updateCandidateSchema.safeParse({}).success).toBe(true);
    expect(updateCandidateSchema.safeParse({ phone: "0700000000" }).success).toBe(true);
    expect(updateCandidateSchema.safeParse({ email: "invalide" }).success).toBe(false);
  });
});

describe("job.schema", () => {
  const validJob = {
    title: "Développeur Fullstack",
    description: "Une description suffisamment longue.",
    location: "Paris",
    company: "SouverainRecrut",
    recruiterId: "recruiter-1",
  };

  it("valide une offre complète", () => {
    expect(createJobSchema.safeParse(validJob).success).toBe(true);
  });

  it("rejette une offre invalide", () => {
    const result = createJobSchema.safeParse({
      title: "D",
      description: "court",
      location: "",
      company: "",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const fields = result.error.issues.map((i) => i.path.join("."));
      expect(fields).toEqual(
        expect.arrayContaining(["title", "description", "location", "company", "recruiterId"])
      );
    }
  });

  it("valide une mise à jour partielle", () => {
    expect(updateJobSchema.safeParse({}).success).toBe(true);
    expect(updateJobSchema.safeParse({ title: "Nouveau titre" }).success).toBe(true);
    expect(updateJobSchema.safeParse({ title: "x" }).success).toBe(false);
  });
});

describe("application.schema", () => {
  it("valide une candidature (statut optionnel)", () => {
    expect(
      createApplicationSchema.safeParse({ candidateId: "c1", jobId: "j1" })
        .success
    ).toBe(true);
    expect(
      createApplicationSchema.safeParse({
        candidateId: "c1",
        jobId: "j1",
        status: ApplicationStatus.PENDING,
      }).success
    ).toBe(true);
  });

  it("rejette une candidature sans candidat/offre ou avec un statut inconnu", () => {
    expect(createApplicationSchema.safeParse({}).success).toBe(false);
    expect(
      createApplicationSchema.safeParse({
        candidateId: "c1",
        jobId: "j1",
        status: "BIDON",
      }).success
    ).toBe(false);
  });

  it("exige un statut valide pour la mise à jour", () => {
    expect(
      updateApplicationSchema.safeParse({ status: ApplicationStatus.ACCEPTED })
        .success
    ).toBe(true);
    expect(updateApplicationSchema.safeParse({}).success).toBe(false);
    expect(updateApplicationSchema.safeParse({ status: "BIDON" }).success).toBe(false);
  });
});
