/* Panel provisional: confirma que la sesión funciona y permite salir. */
(function () {
  'use strict';

  const saludo = document.getElementById('saludo');
  const detalle = document.getElementById('detalle');
  const botonSalir = document.getElementById('boton-salir');

  const ROLES = { admin: 'Administrador', estudiante: 'Estudiante' };

  async function cargar() {
    try {
      const datos = await Api.yo();
      saludo.textContent = 'Hola, ' + datos.usuario.nombre_mostrar;
      detalle.textContent = 'Tu sesión está activa. Rol: ' +
        (ROLES[datos.usuario.rol] || datos.usuario.rol) + '.';
    } catch (error) {
      if (error.estado === 401) {
        window.location.replace('/acceso');
        return;
      }
      saludo.textContent = 'No pudimos cargar tus datos';
      detalle.textContent = error.mensaje;
    }
  }

  botonSalir.addEventListener('click', async () => {
    botonSalir.disabled = true;
    try {
      await Api.logout();
    } catch (_) {
      /* aunque falle, volvemos al inicio; el servidor decide si la sesión sigue */
    }
    window.location.replace('/');
  });

  cargar();
})();