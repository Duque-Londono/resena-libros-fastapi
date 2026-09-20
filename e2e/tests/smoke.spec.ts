import { test, expect } from "@playwright/test";

/**
 * Smoke tests: comprobaciones básicas de que la API está viva y la documentación
 * carga. Usan el API request context (sin navegador).
 */

test("la raíz responde 200", async ({ request }) => {
  const respuesta = await request.get("/");
  expect(respuesta.status()).toBe(200);
  const cuerpo = await respuesta.json();
  expect(cuerpo).toHaveProperty("mensaje");
});

test("la documentación Swagger (/docs) carga", async ({ request }) => {
  const respuesta = await request.get("/docs");
  expect(respuesta.status()).toBe(200);
  const html = await respuesta.text();
  // Swagger UI incluye la palabra "swagger" en su HTML; confirma que se sirve.
  expect(html.toLowerCase()).toContain("swagger");
});

test("el esquema OpenAPI (/openapi.json) está disponible", async ({ request }) => {
  const respuesta = await request.get("/openapi.json");
  expect(respuesta.status()).toBe(200);
  const esquema = await respuesta.json();
  // La clave "paths" contiene todos los endpoints declarados.
  expect(esquema).toHaveProperty("paths");
});
