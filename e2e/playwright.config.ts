import { defineConfig } from "@playwright/test";

/**
 * Configuración de Playwright para las pruebas E2E de la API.
 *
 * Se asume que la API YA está corriendo y sembrada en baseURL (ver README).
 * La mayoría de los tests usan el "API request context" (peticiones HTTP puras,
 * sin navegador); solo el smoke de /docs comprueba que Swagger UI carga.
 */
export default defineConfig({
  testDir: "./tests",
  // Reporter compacto en consola.
  reporter: [["list"]],
  use: {
    // Todas las peticiones (request.get, request.post...) parten de esta URL.
    baseURL: "http://127.0.0.1:8000",
  },
  // NOTA: si se quisiera que Playwright levantara la API automáticamente, se
  // podría descomentar este bloque. Lo dejamos desactivado a propósito porque el
  // enunciado pide asumir la API ya corriendo y sembrada.
  //
  // webServer: {
  //   command: "cd .. && uvicorn app.main:app --port 8000",
  //   url: "http://127.0.0.1:8000/",
  //   reuseExistingServer: true,
  // },
});
