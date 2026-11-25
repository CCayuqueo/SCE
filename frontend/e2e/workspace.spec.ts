import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import { expect, test, type Browser, type Page } from "@playwright/test";

const password = "contraseña temporal para SRC";

async function createAccount(browser: Browser, baseURL: string, name: string) {
  const context = await browser.newContext({
    baseURL,
    ignoreHTTPSErrors: process.env.SRC_E2E_LOCAL_TLS === "1",
  });
  const page = await context.newPage();
  await page.goto("/register");
  await page.getByLabel("Nombre").fill(name);
  await page
    .getByLabel("Correo electrónico")
    .fill(`${randomUUID()}@example.com`);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Crear cuenta" }).click();
  await expect(page).toHaveURL(/\/app\/inicio$/);
  return context;
}

async function join(page: Page, code: string, room: string) {
  await page.getByRole("link", { name: "Unirse a sala" }).click();
  const dialog = page.getByRole("dialog", { name: "Unirse a sala" });
  await dialog.getByLabel("Código de sala").fill(code);
  await dialog.getByRole("button", { name: "Unirse", exact: true }).click();
  await expect(page.getByRole("heading", { name: room })).toBeVisible();
}

async function confirmCapture(page: Page, time: string, edit = false) {
  await page.getByRole("link", { name: "Mi horario" }).click();
  const image = fileURLToPath(
    new URL(
      `../../images/Captura de pantalla_2026-11-25_${time}.png`,
      import.meta.url,
    ),
  );
  await page.getByLabel("Captura del horario").setInputFiles(image);
  await page.getByRole("button", { name: "Cargar captura" }).click();
  await expect(page.getByRole("heading", { name: "Borrador" })).toBeVisible();
  if (edit)
    await page.getByRole("button", { name: "Lunes 1-2", exact: true }).click();
  await page.getByRole("button", { name: "Guardar y confirmar" }).click();
  await expect(page.getByRole("heading", { name: "Confirmado" })).toBeVisible();
  await page.getByRole("link", { name: "Volver a la sala" }).click();
}

async function expectWeight(page: Page, weight: number) {
  const cell = page.getByRole("button", { name: /^Lunes 1-2:/ });
  await expect(cell).toHaveText(String(weight));
}

async function deleteAccount(page: Page, successor?: string) {
  await page.getByRole("link", { name: "Ajustes", exact: true }).click();
  await page.getByRole("button", { name: "Revisar eliminación" }).click();
  const dialog = page.getByRole("dialog", {
    name: "Eliminar cuenta permanentemente",
  });
  if (successor) {
    const option = await dialog
      .getByRole("option", { name: new RegExp(`Transferir a ${successor}`) })
      .getAttribute("value");
    await dialog.getByRole("combobox").selectOption(option!);
  }
  await dialog.getByLabel("Contraseña actual").fill(password);
  await dialog.getByLabel("Escribe ELIMINAR para confirmar").fill("ELIMINAR");
  await dialog
    .getByRole("button", { name: "Eliminar permanentemente" })
    .click();
  await expect(page).toHaveURL(/\/login$/);
}

test("flujo de las tres cuentas, horarios, permisos y eliminación", async ({
  browser,
  baseURL,
}) => {
  const contexts = [];
  const roomName = "Horario compartido";
  try {
    const owner = await createAccount(browser, baseURL!, "Alicia");
    contexts.push(owner);
    const admin = await createAccount(browser, baseURL!, "Bernardo");
    contexts.push(admin);
    const member = await createAccount(browser, baseURL!, "Camila");
    contexts.push(member);
    const [a, b, c] = contexts.map((context) => context.pages()[0]);

    await a.getByRole("link", { name: "Crear sala", exact: true }).click();
    const form = a.getByRole("dialog", { name: "Crear sala" });
    await form.getByLabel("Nombre de la sala").fill(roomName);
    await form.getByRole("button", { name: "Crear sala" }).click();
    await expect(a.getByRole("heading", { name: roomName })).toBeVisible();
    const roomURL = a.url();
    const code = (await a.locator("code").textContent())!;
    await join(b, code, roomName);
    await join(c, code, roomName);

    await confirmCapture(a, "15-04-01");
    await confirmCapture(b, "15-04-23", true);
    await confirmCapture(c, "15-04-40");

    await a.getByRole("link", { name: "Superposición" }).click();
    await expect(
      a
        .getByRole("table", { name: "Mapa de ocupación semanal" })
        .getByRole("button"),
    ).toHaveCount(70);
    await expectWeight(a, 2);
    await a.getByRole("button", { name: /^Lunes 1-2:/ }).click();
    const cell = a.getByRole("region", { name: "Detalle del bloque" });
    await expect(cell.getByText("Alicia", { exact: true })).toBeVisible();
    await expect(cell.getByText("Bernardo", { exact: true })).toBeVisible();
    await expect(cell.getByText("Camila", { exact: true })).toBeVisible();

    await a.getByRole("link", { name: "Volver a la sala" }).click();
    const bernardo = a.getByRole("row", { name: /Bernardo/ });
    await bernardo.getByRole("button", { name: "Promover" }).click();
    await expect(
      bernardo.getByText("Administrador", { exact: true }),
    ).toBeVisible();
    await b.goto(roomURL + "/superposicion");
    await expectWeight(b, 2);
    await c.goto(roomURL + "/superposicion");
    await expect(c.getByRole("alert")).toContainText(
      "requiere permisos de administración",
    );

    await c.goto(roomURL + "/mi-horario");
    await c.getByRole("button", { name: "Lunes 1-2", exact: true }).click();
    await c.getByRole("button", { name: "Guardar y confirmar" }).click();
    await expect(c.getByText("Cambios sin guardar.")).toHaveCount(0);
    await b.getByRole("button", { name: "Actualizar" }).click();
    await expectWeight(b, 3);

    await deleteAccount(c);
    await b.getByRole("button", { name: "Actualizar" }).click();
    await expectWeight(b, 2);
    await deleteAccount(a, "Bernardo");
    await b.goto(roomURL);
    await expect(
      b.getByText(/Propietario · 1 integrantes · Confirmado/),
    ).toBeVisible();
    await b.getByRole("link", { name: "Superposición" }).click();
    await expectWeight(b, 1);
  } finally {
    await Promise.all(contexts.map((context) => context.close()));
  }
});

test("navegación móvil por teclado y guía con captura", async ({
  browser,
  baseURL,
}) => {
  const context = await createAccount(browser, baseURL!, "Navegación");
  try {
    const page = context.pages()[0];
    await page.setViewportSize({ width: 390, height: 844 });
    const toggle = page.getByRole("button", { name: "Abrir menú" });
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await toggle.focus();
    await toggle.press("Enter");
    const nav = page.getByRole("navigation", { name: "Navegación principal" });
    await expect(nav.getByRole("link")).toHaveText([
      "Inicio",
      "Salas",
      "Ajustes",
      "Guía / Cómo usar",
    ]);
    for (const label of ["Inicio", "Salas", "Ajustes", "Guía / Cómo usar"]) {
      await page.keyboard.press("Tab");
      await expect(
        nav.getByRole("link", { name: label, exact: true }),
      ).toBeFocused();
    }
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("heading", { name: "Guía / Cómo usar" }),
    ).toBeVisible();
    await expect(
      page.getByRole("img", { name: /captura compatible/i }),
    ).toBeVisible();
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth),
    ).toBeLessThanOrEqual(390);
  } finally {
    await context.close();
  }
});
