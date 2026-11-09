import { NextFunction, Request, Response } from "express";

/**
 * Fabrique une requête Express factice pour tester les middlewares.
 */
export const mockRequest = (
  overrides: Record<string, unknown> = {}
): Request =>
  ({
    headers: {},
    query: {},
    params: {},
    body: {},
    originalUrl: "/v1/test",
    ...overrides,
  } as unknown as Request);

/**
 * Fabrique une réponse Express factice (status/json chaînables).
 */
export const mockResponse = (): Response => {
  const res = {} as Response;
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  return res;
};

export const mockNext = (): jest.Mock & NextFunction => jest.fn();
