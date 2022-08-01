import { describe, expect, test } from "vitest";

describe("import vue components", () => {
  test("normal imports as expected", async () => {
    const cmp = await import("../src/components/HelloWorld.vue");
    expect(cmp).toBeDefined();
  });
});
