import { afterEach, describe, expect, it, vi } from "vitest";

import { clearAccessToken, getMe, login, setAccessToken } from "./client";

describe("workspace API client", () => {
  afterEach(() => { vi.unstubAllGlobals(); clearAccessToken(); });

  it("creates a development session without an existing bearer token", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ access_token: "signed-token" }) });
    vi.stubGlobal("fetch", fetchMock);
    await expect(login("internal")).resolves.toEqual({ access_token: "signed-token" });
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/v1/auth/dev/session", expect.objectContaining({ method: "POST" }));
  });

  it("sends the bearer token to protected workspace routes", async () => {
    setAccessToken("signed-token");
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ user_id: "dev-internal" }) });
    vi.stubGlobal("fetch", fetchMock);
    await expect(getMe()).resolves.toMatchObject({ user_id: "dev-internal" });
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/v1/me", expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer signed-token" }) }));
  });
});
