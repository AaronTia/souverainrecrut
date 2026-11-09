import { asyncHandler } from "../../src/utils/async-handler";
import { mockNext, mockRequest, mockResponse } from "../helpers/http";

describe("asyncHandler", () => {
  it("exécute le handler et ne touche pas à next en cas de succès", async () => {
    const req = mockRequest();
    const res = mockResponse();
    const next = mockNext();

    const handler = asyncHandler(async (req, res) => {
      res.status(200).json({ ok: true });
    });

    await handler(req, res, next);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(next).not.toHaveBeenCalled();
  });

  it("transmet l'erreur au middleware suivant en cas de rejet", async () => {
    const req = mockRequest();
    const res = mockResponse();
    const next = mockNext();
    const boom = new Error("boom");

    const handler = asyncHandler(async () => {
      throw boom;
    });

    await handler(req, res, next);

    expect(next).toHaveBeenCalledWith(boom);
    expect(res.status).not.toHaveBeenCalled();
  });
});
