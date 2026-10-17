/* Panel del estudiante. Todos los datos vienen de la API (MySQL);
 * aquí solo se pintan. Se usa textContent y nunca innerHTML con datos. */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);

  function crear(etiqueta, clase, texto) {
    const e = document.createElement(etiqueta);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  function plural(n, uno, varios) {
    return n + ' ' + (n === 1 ? uno : varios);
  }

  function pintarBarra(barra, porcentaje) {
    const p = Math.max(0, Math.min(100, Number(porcentaje) || 0));
    barra.setAttribute('aria-valuenow', String(p));
    barra.firstElementChild.style.width = p + '%';
  }

  function pintarSaludo(usuario, stats) {
    $('saludo').textContent = 'Hola, ' + usuario.nombre_mostrar;
    $('saludo-detalle').textContent = stats.practico_hoy
      ? 'Ya practicaste hoy. ¡Qué bien lo estás haciendo!'
      : 'Hoy es un buen día para aprender algo nuevo, de a poquito.';
  }

  function pintarStats(stats) {
    $('xp-valor').textContent = String(stats.xp_total);
    $('racha-valor').textContent = String(stats.racha_actual);
    $('racha-etiqueta').textContent = stats.racha_actual === 1 ? 'día de racha' : 'días de racha';

    const contenedor = $('vidas');
    contenedor.replaceChildren();
    for (let i = 0; i < stats.corazones_maximos; i++) {
      const vida = crear('span', i < stats.corazones ? 'vida' : 'vida vida--vacia');
      vida.setAttribute('aria-hidden', 'true');
      contenedor.appendChild(vida);
    }
    const textoVidas = stats.corazones + ' de ' + stats.corazones_maximos + ' corazones';
    contenedor.setAttribute('aria-label', textoVidas);
    $('vidas-texto').textContent = textoVidas;

    $('nivel').textContent = String(stats.nivel);
    $('nivel-texto').textContent = stats.xp_en_nivel + ' / ' + stats.xp_por_nivel + ' XP';
    pintarBarra($('barra-nivel'), (100 * stats.xp_en_nivel) / stats.xp_por_nivel);
  }

    function pintarProgreso(progreso) {
    $('curso-texto').textContent =
      progreso.lecciones_completadas + ' de ' + plural(progreso.total_lecciones, 'lección', 'lecciones');
    pintarBarra($('barra-curso'), progreso.porcentaje);

    const boton = $('leccion-boton');
    const s = progreso.siguiente;
    if (s) {
      $('leccion-etiqueta').textContent =
        s.estado === 'en_progreso' ? 'Continúa con tu lección' : 'Tu próxima lección';
      $('leccion-unidad').textContent = s.unidad_titulo;
      $('leccion-titulo').textContent = s.titulo;
      $('leccion-descripcion').textContent = s.descripcion || '';
      boton.href = '/leccion/' + s.id;
      boton.textContent = s.estado === 'en_progreso' ? 'Continuar' : 'Empezar';
    } else {
      boton.href = '/recorrido';
      boton.textContent = 'Ver mi camino';
      $('leccion-unidad').textContent = '';
      $('leccion-descripcion').textContent = '';
      if (progreso.total_lecciones === 0) {
        $('leccion-etiqueta').textContent = 'Sin lecciones';
        $('leccion-titulo').textContent = 'Aún no hay lecciones publicadas';
      } else {
        $('leccion-etiqueta').textContent = '¡Bien hecho!';
        $('leccion-titulo').textContent = 'Completaste todo el recorrido disponible';
        $('leccion-descripcion').textContent = 'Pronto habrá más lecciones.';
      }
    }
  }

  function pintarSemana(dias) {
    const lista = $('semana');
    lista.replaceChildren();
    let xp = 0;
    let lecciones = 0;

    dias.forEach((d, i) => {
      xp += d.xp;
      lecciones += d.lecciones;
      const fecha = new Date(d.fecha + 'T12:00:00');
      let clase = 'dia';
      if (d.activo) clase += ' dia--activo';
      if (i === dias.length - 1) clase += ' dia--hoy';

      const li = crear('li', clase);
      li.setAttribute('aria-label',
        fecha.toLocaleDateString('es', { weekday: 'long' }) +
        (d.activo ? ': con actividad' : ': sin actividad'));
      const nombre = crear('div', 'dia__nombre', fecha.toLocaleDateString('es', { weekday: 'narrow' }));
      nombre.setAttribute('aria-hidden', 'true');
      const punto = crear('div', 'dia__punto');
      punto.setAttribute('aria-hidden', 'true');
      li.append(nombre, punto);
      lista.appendChild(li);
    });

    $('semana-resumen').textContent = (xp === 0 && lecciones === 0)
      ? 'Aún no practicaste esta semana. ¡Hoy es un buen día para empezar!'
      : 'Esta semana: ' + xp + ' XP · ' + plural(lecciones, 'lección', 'lecciones') + '.';
  }

  function pintarLogros(logros) {
    const lista = $('logros');
    lista.replaceChildren();
    const recientes = logros.slice(0, 3);
    $('logros-vacio').hidden = recientes.length > 0;

    recientes.forEach((l) => {
      const li = crear('li', 'logro');
      const icono = crear('span', 'logro__icono');
      icono.setAttribute('aria-hidden', 'true');
      const texto = crear('div');
      texto.append(crear('span', 'logro__nombre', l.nombre), crear('span', 'logro__descripcion', l.descripcion));
      li.append(icono, texto);
      lista.appendChild(li);
    });
  }

  function mostrarError(mensaje) {
    $('aviso-error-texto').textContent = mensaje;
    $('aviso-error').hidden = false;
    $('saludo-detalle').textContent = '';
  }

  async function cargar() {
    $('aviso-error').hidden = true;
    try {
      const yo = await Api.yo();
      const usuario = yo.usuario;
      if (usuario.rol !== 'estudiante') {
        window.location.replace(Api.rutaInicio(usuario.rol));
        return;
      }
      const [stats, progreso, actividad, logros] = await Promise.all([
        Api.get('/stats'),
        Api.get('/progress'),
        Api.get('/activity'),
        Api.get('/achievements/unlocked'),
      ]);
      pintarSaludo(usuario, stats);
      pintarStats(stats);
      pintarProgreso(progreso);
      pintarSemana(actividad.dias);
      pintarLogros(logros.logros);
    } catch (error) {
      if (error.estado === 401) {
        window.location.replace('/acceso');
        return;
      }
      mostrarError(error.mensaje || 'No pudimos cargar tus datos.');
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