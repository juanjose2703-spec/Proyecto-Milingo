/* Pantalla de logros. Los datos vienen de la API; aquí solo se pintan. */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const ICONOS = ['estrella', 'camino', 'llama', 'rayo', 'diana'];

  function crear(etiqueta, clase, texto) {
    const e = document.createElement(etiqueta);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  function pintar(logros) {
    const ganados = logros.filter((l) => l.desbloqueado).length;
    $('logros-resumen').textContent = logros.length === 0
      ? 'Aún no hay logros disponibles.'
      : ganados + ' de ' + logros.length + ' logros desbloqueados.';

    const lista = $('insignias');
    lista.replaceChildren();
    logros.forEach((l) => {
      const li = crear('li', 'insignia ' + (l.desbloqueado ? 'insignia--ganada' : 'insignia--bloqueada'));
      const icono = crear('span', 'insignia__icono insignia__icono--' +
        (ICONOS.includes(l.icono) ? l.icono : 'estrella'));
      icono.setAttribute('aria-hidden', 'true');

      let estado = 'Bloqueado';
      if (l.desbloqueado) {
        const fecha = new Date(l.desbloqueado_en);
        estado = 'Desbloqueado' + (isNaN(fecha) ? '' : ' el ' +
          fecha.toLocaleDateString('es', { day: 'numeric', month: 'long', year: 'numeric' }));
      }
      li.append(
        icono,
        crear('h2', 'insignia__nombre', l.nombre),
        crear('p', 'insignia__descripcion', l.descripcion),
        crear('p', 'insignia__estado', estado)
      );
      lista.appendChild(li);
    });
  }

  async function cargar() {
    $('aviso-error').hidden = true;
    try {
      const yo = await Api.yo();
      if (yo.usuario.rol !== 'estudiante') {
        window.location.replace(Api.rutaInicio(yo.usuario.rol));
        return;
      }
      pintar((await Api.get('/achievements')).logros);
    } catch (error) {
      if (error.estado === 401) {
        window.location.replace('/acceso');
        return;
      }
      $('aviso-error-texto').textContent = error.mensaje || 'No pudimos cargar tus logros.';
      $('aviso-error').hidden = false;
      $('logros-resumen').textContent = '';
    }
  }

  $('boton-reintentar').addEventListener('click', cargar);
  $('boton-salir').addEventListener('click', async () => {
    $('boton-salir').disabled = true;
    try { await Api.logout(); } catch (_) { /* volvemos al inicio igualmente */ }
    window.location.replace('/');
  });

  cargar();
})();