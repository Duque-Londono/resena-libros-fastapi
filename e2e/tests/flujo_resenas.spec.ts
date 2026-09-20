import { test, expect, APIRequestContext } from "@playwright/test";

/**
 * Flujo completo de reseñas por API request context (sin navegador).
 *
 * Cada test construye lo que necesita y usa emails con timestamp para no
 * colisionar con datos previos, de modo que no depende de un estado frágil.
 * Solo asume que la API está corriendo y sembrada (existe el admin admin@demo.com).
 */

// Credenciales del admin sembrado por db/seed.py.
const ADMIN = { username: "admin@demo.com", password: "admin12345" };

/** Registra un usuario normal nuevo y devuelve su token. */
async function registrarYObtenerToken(
  request: APIRequestContext,
  etiqueta: string,
): Promise<string> {
  const sufijo = `${Date.now()}_${etiqueta}`;
  const email = `e2e_${sufijo}@test.com`;
  const password = "clave12345";

  const registro = await request.post("/auth/register", {
    data: { email, username: `e2e_${sufijo}`, password },
  });
  expect(registro.status()).toBe(201);

  return await obtenerToken(request, email, password);
}

/** Inicia sesión (formulario OAuth2) y devuelve el access_token. */
async function obtenerToken(
  request: APIRequestContext,
  username: string,
  password: string,
): Promise<string> {
  // El login usa application/x-www-form-urlencoded (OAuth2PasswordRequestForm).
  const login = await request.post("/auth/login", {
    form: { username, password },
  });
  expect(login.status()).toBe(200);
  const cuerpo = await login.json();
  expect(cuerpo.access_token).toBeTruthy();
  return cuerpo.access_token;
}

/** Atajo para construir la cabecera Authorization. */
function auth(token: string) {
  return { Authorization: `Bearer ${token}` };
}

test("flujo completo: crear obra, reseñar, editar, propiedad, favoritos y limpieza", async ({
  request,
}) => {
  // --- Preparación de usuarios ---
  const tokenUsuario = await registrarYObtenerToken(request, "autor");
  const tokenOtro = await registrarYObtenerToken(request, "otro");
  const tokenAdmin = await obtenerToken(request, ADMIN.username, ADMIN.password);

  // --- El admin crea una obra ---
  const creacionObra = await request.post("/works", {
    headers: auth(tokenAdmin),
    data: {
      title: `Obra E2E ${Date.now()}`,
      type: "book",
      genre: "fantasy",
      release_year: 2021,
    },
  });
  expect(creacionObra.status()).toBe(201);
  const workId = (await creacionObra.json()).id;

  // --- El usuario normal crea una reseña sobre esa obra ---
  const creacionResena = await request.post(`/works/${workId}/reviews`, {
    headers: auth(tokenUsuario),
    data: { rating: 5, text: "Reseña de prueba E2E" },
  });
  expect(creacionResena.status()).toBe(201);
  const resena = await creacionResena.json();
  const reviewId = resena.id;
  expect(resena.rating).toBe(5);

  // --- GET público de la reseña ---
  const verResena = await request.get(`/reviews/${reviewId}`);
  expect(verResena.status()).toBe(200);
  const resenaVista = await verResena.json();
  expect(resenaVista.rating).toBe(5);
  expect(resenaVista.text).toBe("Reseña de prueba E2E");

  // --- El dueño edita su reseña (200) ---
  const edicionDueno = await request.put(`/reviews/${reviewId}`, {
    headers: auth(tokenUsuario),
    data: { rating: 4 },
  });
  expect(edicionDueno.status()).toBe(200);
  expect((await edicionDueno.json()).rating).toBe(4);

  // --- Un segundo usuario intenta editarla (403, regla de propiedad) ---
  const edicionAjena = await request.put(`/reviews/${reviewId}`, {
    headers: auth(tokenOtro),
    data: { rating: 1 },
  });
  expect(edicionAjena.status()).toBe(403);

  // --- El usuario añade la obra a sus favoritos (201 la primera vez) ---
  const anadir = await request.post(`/me/reading-list/${workId}`, {
    headers: auth(tokenUsuario),
  });
  expect([200, 201]).toContain(anadir.status());

  // --- La obra aparece en su lista de lectura ---
  const lista = await request.get("/me/reading-list", { headers: auth(tokenUsuario) });
  expect(lista.status()).toBe(200);
  const obras = await lista.json();
  expect(obras.some((o: { id: number }) => o.id === workId)).toBe(true);

  // --- Limpieza: el usuario borra su reseña (204) ---
  const borrado = await request.delete(`/reviews/${reviewId}`, {
    headers: auth(tokenUsuario),
  });
  expect(borrado.status()).toBe(204);
});
