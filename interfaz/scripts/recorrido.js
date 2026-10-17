/* Mapa de aprendizaje. El estado de cada lección lo calcula el servidor;
 * aquí solo se pinta. Se usa textContent, nunca innerHTML con datos. */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);

  const ETIQUETAS = {
    completada: 'Completada',
    en_progreso: 'En progreso',
    disponible: 'Disponible',
    bloqueada: 'Bloqueada',
  };
  // Posición en zigzag: centro, derecha, centro, izquierda.
  const POSICIONES = ['', ' camino__item--der', '', ' camino__item--izq'];

  const detalle = $('detalle');
  let leccionAbierta = null;

  function crear(etiqueta, clase, texto) {
    const e = document.createElement(etiqueta);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  function plural(n, uno, varios) {
    return n + ' ' + (n === 1 ? uno : varios);
  }

  /* ---------- Cuadro de detalle ---------- */
  async function abrirDetalle(unidad, leccion) {
    leccionAbierta = leccion.id;
    const estado = leccion.estado;

    $('detalle-unidad').textContent = 'Unidad ' + unidad.orden + ' · ' + unidad.titulo;
    $('detalle-titulo').textContent = leccion.titulo;
    $('detalle-descripcion').textContent = leccion.descripcion || '';
    $('detalle-meta').textContent = '';

    const chip = $('detalle-estado');
    chip.textContent = ETIQUETAS[estado] || estado;
    chip.className = 'detalle__estado detalle__estado--' + estado;

    const accion = $('detalle-accion');
    if (estado === 'bloqueada') {
      accion.hidden = true;
      $('detalle-nota').textContent = 'Completa la lección anterior para abrir esta.';
    } else {
      accion.hidden = false;
      accion.textContent = 'Próximamente';
      $('detalle-nota').textContent = 'Las lecciones interactivas llegan en la siguiente etapa.';
    }

    detalle.showModal();

    try {
      const datos = await Api.get('/lessons/' + leccion.id);
      if (detalle.open && leccionAbierta === leccion.id) {
        const l = datos.leccion;
        $('detalle-meta').textContent =
          plural(l.num_preguntas, 'pregunta', 'preguntas') + ' · hasta ' + l.xp_base + ' XP o más';
      }
    } catch (_) {
      /* El detalle extra es opcional: si falla, el cuadro se queda sin él. */
    }
  }

  $('detalle-cerrar').addEventListener('click', () => detalle.close());
  // Clic en el fondo oscuro cierra el cuadro.
  detalle.addEventListener('click', (e) => { if (e.target === detalle) detalle.close(); });
  detalle.addEventListener('close', () => { leccionAbierta = null; });

  /* ---------- Mapa ---------- */
  function pintarUnidad(unidad, indice, siguienteId) {
    const tituloId = 'unidad-' + unidad.id;
    const seccion = crear('section', 'unidad' + (indice % 2 === 1 ? ' unidad--rosa' : ''));
    seccion.setAttribute('aria-labelledby', tituloId);

    const hechas = unidad.lecciones.filter((l) => l.estado === 'completada').length;
    const cabecera = crear('header', 'unidad__cabecera');
    const titulo = crear('h2', 'unidad__titulo', unidad.titulo);
    titulo.id = tituloId;
    cabecera.append(
      crear('p', 'unidad__numero', 'Unidad ' + unidad.orden),
      titulo,
      crear('p', 'unidad__descripcion', unidad.descripcion || ''),
      crear('p', 'unidad__progreso',
        hechas + ' de ' + plural(unidad.lecciones.length, 'lección', 'lecciones'))
    );

    const lista = crear('ol', 'camino');
    unidad.lecciones.forEach((leccion, i) => {
      const esSiguiente = leccion.id === siguienteId;
      const item = crear('li', 'camino__item camino__item--' + leccion.estado + POSICIONES[i % 4]);

      if (esSiguiente) {
        item.appendChild(crear('span', 'camino__etiqueta',
          leccion.estado === 'en_progreso' ? 'Continuar' : 'Empezar'));
      }

      const nodo = crear('button', 'nodo nodo--' + leccion.estado + (esSiguiente ? ' nodo--siguiente' : ''));
      nodo.type = 'button';
      nodo.dataset.siguiente = esSiguiente ? 'si' : 'no';
      nodo.setAttribute('aria-label',
        'Lección ' + leccion.orden + ': ' + leccion.titulo + '. ' + (ETIQUETAS[leccion.estado] || '') + '.');
      nodo.addEventListener('click', () => abrirDetalle(unidad, leccion));

      item.append(nodo, crear('span', 'camino__nombre', leccion.titulo));
      lista.appendChild(item);
    });

    seccion.append(cabecera, lista);
    return seccion;
  }

  function pintarMapa(curso, unidades, progreso) {
    $('curso-titulo').textContent = curso.titulo;
    $('curso-resumen').textContent = progreso.total_lecciones === 0
      ? 'Aún no hay lecciones publicadas.'
      : progreso.lecciones_completadas + ' de ' + plural(progreso.total_lecciones, 'lección', 'lecciones') +
        ' completadas (' + progreso.porcentaje + ' %).';

    const siguienteId = progreso.siguiente ? progreso.siguiente.id : null;
    const contenedor = $('unidades');
    contenedor.replaceChildren();
    unidades.forEach((u, i) => contenedor.appendChild(pintarUnidad(u, i, siguienteId)));

    const siguiente = contenedor.querySelector('.nodo[data-siguiente="si"]');
    if (siguiente) {
      const sinMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      siguiente.scrollIntoView({ block: 'center', behavior: sinMovimiento ? 'auto' : 'smooth' });
    }
  }

  function mostrarError(mensaje) {
    $('aviso-error-texto').textContent = mensaje;
    $('aviso-error').hidden = false;
    $('curso-resumen').textContent = '';
  }

  async function cargar() {
    $('aviso-error').hidden = true;
    try {
      const yo = await Api.yo();
      if (yo.usuario.rol !== 'estudiante') {
        window.location.replace(Api.rutaInicio(yo.usuario.rol));
        return;
      }
      const cursos = await Api.get('/courses');
      if (cursos.cursos.length === 0) {
        $('curso-resumen').textContent = 'Aún no hay cursos publicados.';
        return;
      }
      const curso = cursos.cursos[0];
      const [unidades, progreso] = await Promise.all([
        Api.get('/courses/' + curso.id + '/units'),
        Api.get('/progress'),
      ]);
      pintarMapa(curso, unidades.unidades, progreso);
    } catch (error) {
      if (error.estado === 401) {
        window.location.replace('/acceso');
        return;
      }
      mostrarError(error.mensaje || 'No pudimos cargar tu recorrido.');
    }
  }

  $('boton-reintentar').addEventListener('click', cargar);

  $('boton-salir').addEventListener('click', async () => {
    $('boton-salir').disabled = true;
    try {
      await Api.logout();
    } catch (_) {
      /* aunque falle, volvemos al inicio; el servidor decide si la sesión sigue */
    }
    window.location.replace('/');
  });

  cargar();
})();