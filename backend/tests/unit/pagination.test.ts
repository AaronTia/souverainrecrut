import {
  buildPaginationMeta,
  getPagination,
} from "../../src/utils/pagination";

describe("getPagination", () => {
  it("applique les valeurs par défaut", () => {
    expect(getPagination()).toEqual({ page: 1, limit: 10, skip: 0 });
  });

  it("calcule le décalage à partir de la page et de la limite", () => {
    expect(getPagination("3", "20")).toEqual({ page: 3, limit: 20, skip: 40 });
  });

  it("borne la page à 1 et la limite entre 1 et 100", () => {
    expect(getPagination("-5", "500")).toEqual({
      page: 1,
      limit: 100,
      skip: 0,
    });
    expect(getPagination("1", "0").limit).toBe(1);
  });

  it("gère des valeurs non numériques", () => {
    const result = getPagination("abc", "xyz");
    expect(Number.isNaN(result.page)).toBe(true);
    expect(Number.isNaN(result.limit)).toBe(true);
  });
});

describe("buildPaginationMeta", () => {
  it("arrondit le nombre de pages au supérieur", () => {
    expect(buildPaginationMeta(1, 10, 21).totalPages).toBe(3);
  });

  it("retourne 0 page pour un total nul", () => {
    expect(buildPaginationMeta(1, 10, 0)).toEqual({
      page: 1,
      limit: 10,
      total: 0,
      totalPages: 0,
    });
  });
});
