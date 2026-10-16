/* Cliente de la API de Milingo.
 * - Envía siempre la cookie de sesión.
 * - Añade el token CSRF a las peticiones que modifican datos.
 * - Convierte los errores del servidor en ErrorApi con un mensaje legible.
 * No guarda nada sensible en localStorage: el token vive solo en memoria. */
const Api = (() => {
  const BASE = '/api/v1';
  let tokenCsrf = null;

  class ErrorApi extends Error {
    constructor(estado, codigo, mensaje) {
      super(mensaje);
      this.name = 'ErrorApi';
      this.estado = estado;
      this.codigo = codigo;
      this.mensaje = mensaje;
    }
  }

  async function obtenerToken() {
    await enviar('GET', '/auth/csrf'); // enviar() guarda el token recibido
  }

  async function enviar(metodo, ruta, cuerpo, reintento = true) {
    const cabeceras = { Accept: 'application/json' };
    const opciones = { method: metodo, headers: cabeceras, credentials: 'same-origin' };

    if (metodo !== 'GET') {
      if (!tokenCsrf) await obtenerToken();
      cabeceras['X-CSRF-Token'] = tokenCsrf;
    }
    if (cuerpo !== undefined) {
      cabeceras['Content-Type'] = 'application/json';
      opciones.body = JSON.stringify(cuerpo);
    }

    let respuesta;
    try {
      respuesta = await fetch(BASE + ruta, opciones);
    } catch (_) {
      throw new ErrorApi(
        0, 'sin_conexion',
        'No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.'
      );
    }

    let json = null;
    try { json = await respuesta.json(); } catch (_) { /* respuesta sin JSON */ }

    if (!respuesta.ok || !json || json.ok === false) {
      // Token vencido: se pide uno nuevo y se reintenta una sola vez.
      if (respuesta.status === 403 && json && json.error
          && json.error.codigo === 'csrf_invalido' && reintento) {
        tokenCsrf = null;
        return enviar(metodo, ruta, cuerpo, false);
      }
      const e = (json && json.error) || {};
      throw new ErrorApi(
        respuesta.status,
        e.codigo || 'error',
        e.mensaje || 'Algo salió mal. Inténtalo de nuevo.'
      );
    }

    const datos = json.datos || {};
    if (datos.csrf_token) tokenCsrf = datos.csrf_token;
    return datos;
  }

  const RUTA_POR_ROL = { admin: '/admin', estudiante: '/panel' };

  return {
    ErrorApi,
    get: (ruta) => enviar('GET', ruta),
    post: (ruta, cuerpo) => enviar('POST', ruta, cuerpo === undefined ? {} : cuerpo),
    login: (usuario, contrasena) => enviar('POST', '/auth/login', { usuario, contrasena }),
    logout: async () => {
      await enviar('POST', '/auth/logout', {});
      tokenCsrf = null;
    },
    yo: () => enviar('GET', '/auth/me'),
    rutaInicio: (rol) => RUTA_POR_ROL[rol] || '/panel',
  };
})();