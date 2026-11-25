import { afterEach, expect, it, vi } from "vitest";
import { getJson } from "./client";

afterEach(() => vi.unstubAllGlobals());

it("obtiene el estado de la API a través de la URL relativa", async () => {
  const fetch = vi.fn().mockResolvedValue(Response.json({ status: "ok" }));
  vi.stubGlobal("fetch", fetch);

  await expect(getJson("/health/ready")).resolves.toEqual({ status: "ok" });
  expect(fetch).toHaveBeenCalledWith(
    "/api/v1/health/ready",
    expect.any(Object),
  );
});

it("trata una respuesta HTTP 503 como un fallo", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(null, { status: 503 })),
  );

  await expect(getJson("/health/ready")).rejects.toThrow("HTTP 503");
});
