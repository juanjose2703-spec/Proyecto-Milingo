/* Lógica de la pantalla de inicio de sesión. */
(function () {
  'use strict';

  const formulario = document.getElementById('formulario-acceso');
  const tarjeta = document.getElementById('tarjeta-acceso');
  const campoUsuario = document.getElementById('usuario');
  const campoClave = document.getElementById('contrasena');
  const errorUsuario = document.getElementById('error-usuario');
  const errorClave = document.getElementById('error-contrasena');
  const aviso = document.getElementById('aviso');
  const avisoTexto = document.getElementById('aviso-texto');
  const botonVer = document.getElementById('ver-clave');
  const boton = document.getElementById('boton-acceso');
  const botonTexto = document.getElementById('boton-acceso-texto');

  function marcarError(campo, contenedor, mensaje) {
    campo.setAttribute('aria-invalid', 'true');
    contenedor.textContent = mensaje;
  }

  function limpiarCampo(campo, contenedor) {
    campo.removeAttribute('aria-invalid');
    contenedor.textContent = '';
  }

  function limpiarTodo() {
    limpiarCampo(campoUsuario, errorUsuario);
    limpiarCampo(campoClave, errorClave);
    aviso.hidden = true;
    avisoTexto.textContent = '';
  }

  function mostrarAviso(mensaje) {
    avisoTexto.textContent = mensaje; // textContent: nunca interpreta HTML
    aviso.hidden = false;
  }

  function sacudirTarjeta() {
    tarjeta.classList.remove('sacudir');
    void tarjeta.offsetWidth; // reinicia la animación
    tarjeta.classList.add('sacudir');
  }

  function cargando(si) {
    boton.disabled = si;
    boton.setAttribute('aria-busy', String(si));
    botonTexto.textContent = si ? 'Entrando…' : 'Entrar';
  }

  // Mostrar u ocultar contraseña
  botonVer.addEventListener('click', () => {
    const mostrar = campoClave.type === 'password';
    campoClave.type = mostrar ? 'text' : 'password';
    botonVer.setAttribute('aria-pressed', String(mostrar));
    botonVer.setAttribute('aria-label', mostrar ? 'Ocultar contraseña' : 'Mostrar contraseña');
  });

  campoUsuario.addEventListener('input', () => limpiarCampo(campoUsuario, errorUsuario));
  campoClave.addEventListener('input', () => limpiarCampo(campoClave, errorClave));

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarTodo();

    const usuario = campoUsuario.value.trim();
    const contrasena = campoClave.value;

    // Validación en el navegador (el servidor valida de nuevo).
    let primerInvalido = null;
    if (!usuario) {
      marcarError(campoUsuario, errorUsuario, 'Escribe tu usuario o correo.');
      primerInvalido = campoUsuario;
    }
    if (!contrasena) {
      marcarError(campoClave, errorClave, 'Escribe tu contraseña.');
      primerInvalido = primerInvalido || campoClave;
    }
    if (primerInvalido) {
      primerInvalido.focus();
      return;
    }

    cargando(true);
    try {
      const datos = await Api.login(usuario, contrasena);
      // Se deja el botón en "Entrando…" hasta que cargue la página siguiente.
      window.location.assign(Api.rutaInicio(datos.usuario.rol));
    } catch (error) {
      mostrarAviso(error.mensaje || 'No pudimos iniciar sesión. Inténtalo de nuevo.');
      sacudirTarjeta();
      cargando(false);
      campoClave.focus();
      campoClave.select();
    }
  });

  // Si ya hay una sesión activa, se salta el formulario.
  // (En la consola puede verse un 401 de /auth/me: es lo esperado sin sesión.)
  Api.yo()
    .then((datos) => window.location.replace(Api.rutaInicio(datos.usuario.rol)))
    .catch(() => { /* sin sesión: se queda en el formulario */ });
})();