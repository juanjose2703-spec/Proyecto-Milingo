/* Motor de lecciones (navegador). Solo muestra preguntas y envía lo que el
 * estudiante elige: el servidor evalúa, descuenta corazones y calcula el resultado.
 * Se usa textContent y nunca innerHTML con datos. */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);

  function crear(etiqueta, clase, texto) {
    const e = document.createElement(etiqueta);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  const partes = window.location.pathname.split('/').filter(Boolean);
  const leccionId = Number(partes[partes.length - 1]);

  const PANTALLAS = ['cargando', 'ejercicio', 'resultados', 'sincorazones', 'error'];
  const ACIERTOS = ['¡Correcto!', '¡Muy bien!', '¡Excelente!', '¡Eso es!'];
  const boton = $('boton-principal');
  const dialogo = $('dialogo-salir');

  const estado = {
    intentoId: null, total: 0, respondidas: 0, corazones: 0, maximos: 5,
    pregunta: null, fase: 'cargando', // 'responder' | 'continuar'
    siguiente: null, terminado: null, listo: false, ocupado: false,
  };
  let ejercicio = null; // { obtener, bloquear, marcar, enfocar? }

  /* ---------- Pantallas ---------- */
  function mostrarPantalla(nombre) {
    PANTALLAS.forEach((p) => { $('pantalla-' + p).hidden = p !== nombre; });
    const enEjercicio = nombre === 'ejercicio';
    $('cab-leccion').hidden = !enEjercicio;
    $('pie-leccion').hidden = !enEjercicio;
    if (nombre === 'resultados' || nombre === 'sincorazones' || nombre === 'error') {
      const titulo = $('pantalla-' + nombre).querySelector('h1');
      if (titulo) titulo.focus();
    }
  }

  function mostrarPantallaError(mensaje, conReintento) {
    $('error-texto').textContent = mensaje;
    $('error-reintentar').hidden = !conReintento;
    mostrarPantalla('error');
  }

  /* ---------- Cabecera ---------- */
  function pintarProgreso() {
    const p = estado.total ? Math.round((100 * estado.respondidas) / estado.total) : 0;
    const barra = $('barra-leccion');
    barra.setAttribute('aria-valuenow', String(p));
    barra.firstElementChild.style.width = p + '%';
  }

  function pintarCorazones(perdio) {
    $('corazones-num').textContent = String(estado.corazones);
    const caja = $('vidas-leccion');
    caja.setAttribute('aria-label', estado.corazones + ' de ' + estado.maximos + ' corazones');
    if (perdio) {
      caja.classList.remove('vidas-leccion--perdida');
      void caja.offsetWidth;
      caja.classList.add('vidas-leccion--perdida');
    }
  }

  /* ---------- Botón principal ---------- */
  function actualizarBoton() {
    let deshabilitado = estado.ocupado;
    if (!deshabilitado && estado.fase === 'responder') {
      deshabilitado = !(ejercicio && ejercicio.obtener());
    }
    boton.disabled = deshabilitado;
  }

  function ponerOcupado(si) {
    estado.ocupado = si;
    boton.setAttribute('aria-busy', String(si));
    actualizarBoton();
  }

  /* ---------- Retroalimentación ---------- */
  function limpiarRetro() {
    const pie = $('pie-leccion');
    pie.classList.remove('pie-leccion--ok', 'pie-leccion--mal');
    $('retro-contenido').hidden = true;
    $('retro-error').hidden = true;
  }

  function mostrarErrorInline(mensaje) {
    $('retro-error').textContent = mensaje;
    $('retro-error').hidden = false;
  }

  function mostrarRetro(r) {
    const pie = $('pie-leccion');
    pie.classList.remove('pie-leccion--ok', 'pie-leccion--mal');
    pie.classList.add(r.correcta ? 'pie-leccion--ok' : 'pie-leccion--mal');
    $('retro-titulo').textContent = r.correcta
      ? ACIERTOS[r.respondidas % ACIERTOS.length]
      : 'Respuesta incorrecta';
    const correcta = $('retro-correcta');
    if (r.correcta) {
      correcta.hidden = true;
    } else {
      correcta.textContent = 'Respuesta correcta: ' + r.respuesta_correcta;
      correcta.hidden = false;
    }
    $('retro-explicacion').textContent = r.explicacion || '';
    $('retro-contenido').hidden = false;
  }

  /* ---------- Tipos de ejercicio ---------- */
  function renderOpciones(p, cont) {
    const grupo = crear('fieldset', 'opciones');
    grupo.appendChild(crear('legend', 'solo-lectores', p.instrucciones || 'Elige una opción'));
    p.opciones.forEach((o, i) => {
      const etiqueta = crear('label', 'opcion');
      const radio = crear('input');
      radio.type = 'radio';
      radio.name = 'opcion';
      radio.value = String(o.id);
      radio.addEventListener('change', actualizarBoton);
      const caja = crear('span', 'opcion__caja');
      caja.append(crear('span', 'opcion__num', String(i + 1)), crear('span', 'opcion__texto', o.texto));
      etiqueta.append(radio, caja);
      grupo.appendChild(etiqueta);
    });
    cont.appendChild(grupo);

    return {
      obtener: () => {
        const r = grupo.querySelector('input:checked');
        return r ? { opcion: Number(r.value) } : null;
      },
      bloquear: () => { grupo.disabled = true; },
      marcar: (ok, correcto) => {
        grupo.querySelectorAll('.opcion').forEach((et) => {
          const marcada = et.querySelector('input').checked;
          const texto = et.querySelector('.opcion__texto').textContent;
          if (marcada) et.classList.add(ok ? 'opcion--ok' : 'opcion--mal');
          else if (!ok && texto === correcto) et.classList.add('opcion--ok');
        });
      },
    };
  }

  function renderTexto(p, cont) {
    const etiqueta = crear('label', 'solo-lectores', p.instrucciones || 'Tu respuesta');
    etiqueta.htmlFor = 'respuesta';
    const entrada = crear('input', 'entrada entrada--grande');
    entrada.id = 'respuesta';
    entrada.type = 'text';
    entrada.maxLength = 300;
    entrada.placeholder = 'Escribe aquí…';
    entrada.setAttribute('autocomplete', 'off');
    entrada.setAttribute('autocapitalize', 'none');
    entrada.setAttribute('autocorrect', 'off');
    entrada.setAttribute('spellcheck', 'false');
    entrada.addEventListener('input', actualizarBoton);
    cont.append(etiqueta, entrada);

    return {
      obtener: () => (entrada.value.trim() ? { texto: entrada.value.trim() } : null),
      bloquear: () => { entrada.readOnly = true; },
      marcar: (ok) => { entrada.classList.add(ok ? 'entrada--ok' : 'entrada--mal'); },
      enfocar: () => entrada.focus(),
    };
  }

  function renderOrden(p, cont) {
    const contenedor = crear('div', 'orden');
    const respuesta = crear('div', 'orden__respuesta');
    respuesta.setAttribute('role', 'group');
    respuesta.setAttribute('aria-label', 'Tu frase');
    respuesta.dataset.vacio = 'Toca las palabras para armar la frase';
    const banco = crear('div', 'orden__banco');
    banco.setAttribute('role', 'group');
    banco.setAttribute('aria-label', 'Palabras disponibles');

    const elegidas = [];
    let bloqueado = false;
    const botones = [];

    p.fichas.forEach((f) => {
      const b = crear('button', 'ficha', f.texto);
      b.type = 'button';
      b.addEventListener('click', () => {
        if (bloqueado) return;
        const i = elegidas.indexOf(f.id);
        if (i === -1) {
          elegidas.push(f.id);
          respuesta.appendChild(b);
        } else {
          elegidas.splice(i, 1);
          banco.appendChild(b);
        }
        b.focus(); // mover el botón de sitio le quita el foco: se lo devolvemos
        actualizarBoton();
      });
      botones.push(b);
      banco.appendChild(b);
    });
    contenedor.append(respuesta, banco);
    cont.appendChild(contenedor);

    return {
      obtener: () => (elegidas.length === p.fichas.length ? { orden: elegidas.slice() } : null),
      bloquear: () => { bloqueado = true; botones.forEach((b) => { b.disabled = true; }); },
      marcar: (ok) => { respuesta.classList.add(ok ? 'orden__respuesta--ok' : 'orden__respuesta--mal'); },
    };
  }

  const RENDER = {
    seleccion: renderOpciones,
    completar_opcion: renderOpciones,
    traducir_es_en: renderTexto,
    traducir_en_es: renderTexto,
    completar_texto: renderTexto,
    ordenar_palabras: renderOrden,
  };

  /* ---------- Flujo ---------- */
  function mostrarPregunta(p) {
    const render = RENDER[p.tipo];
    if (!render) {
      mostrarPantallaError('Este tipo de ejercicio todavía no está disponible.', false);
      return;
    }
    estado.pregunta = p;
    estado.fase = 'responder';
    limpiarRetro();

    $('instrucciones').textContent = p.instrucciones || 'Responde';
    $('enunciado').textContent = p.texto;
    const cont = $('ejercicio');
    cont.replaceChildren();
    ejercicio = render(p, cont);

    $('boton-principal-texto').textContent = 'Comprobar';
    const tarjeta = $('tarjeta-pregunta');
    tarjeta.classList.remove('entrada-suave');
    void tarjeta.offsetWidth;
    tarjeta.classList.add('entrada-suave');

    mostrarPantalla('ejercicio');
    actualizarBoton();
    if (ejercicio.enfocar) ejercicio.enfocar();
    else $('instrucciones').focus();
  }

  function manejarError(error, textoPorDefecto) {
    if (error.estado === 401) {
      window.location.replace('/acceso');
      return;
    }
    const recuperable = error.estado === 0 || error.estado === 400
      || error.estado === 429 || error.estado >= 500;
    if (recuperable) {
      mostrarErrorInline(error.mensaje || textoPorDefecto);
      return;
    }
    mostrarPantallaError(error.mensaje || textoPorDefecto, false);
  }

  function aplicarRespuesta(r) {
    $('nota-reanudado').hidden = true;
    estado.respondidas = r.respondidas;
    estado.total = r.total;
    estado.corazones = r.corazones;
    estado.siguiente = r.siguiente_pregunta;
    estado.terminado = r.terminado;
    estado.listo = r.listo_para_completar;

    pintarProgreso();
    pintarCorazones(!r.correcta && !r.repetida);
    ejercicio.bloquear();
    ejercicio.marcar(r.correcta, r.respuesta_correcta);
    mostrarRetro(r);

    estado.fase = 'continuar';
    $('boton-principal-texto').textContent =
      !estado.terminado && estado.listo ? 'Ver resultados' : 'Continuar';
    actualizarBoton();
    boton.focus();
  }

  async function comprobar() {
    const cuerpo = ejercicio && ejercicio.obtener();
    if (!cuerpo || estado.ocupado) return;
    $('retro-error').hidden = true;
    ponerOcupado(true);
    try {
      const r = await Api.post(
        '/attempts/' + estado.intentoId + '/answers',
        Object.assign({ pregunta_id: estado.pregunta.id }, cuerpo)
      );
      ponerOcupado(false);
      aplicarRespuesta(r);
    } catch (error) {
      ponerOcupado(false);
      manejarError(error, 'No pudimos comprobar tu respuesta.');
    }
  }

  function mensajeMotivador(precision) {
    if (precision === 100) return '¡Perfecto! Ni un solo error.';
    if (precision >= 80) return '¡Muy bien! Estás aprendiendo muy rápido.';
    if (precision >= 50) return '¡Buen trabajo! Cada repaso te acerca más.';
    return 'Lo importante es seguir intentando. ¡La próxima te irá mejor!';
  }

  function pintarResultados(r) {
    $('res-aciertos').textContent = String(r.aciertos);
    $('res-errores').textContent = String(r.errores);
    $('res-precision').textContent = r.precision + ' %';
    $('res-xp').textContent = '+' + r.xp_ganado;
    $('resultados-mensaje').textContent = mensajeMotivador(r.precision);

    const extra = [];
    if (r.repeticion) extra.push('Como ya habías completado esta lección, ganaste la mitad de XP.');
    const racha = r.estadisticas.racha_actual;
    if (racha > 0) extra.push(racha === 1 ? '¡Racha de 1 día!' : '¡Racha de ' + racha + ' días!');
    const lineaExtra = $('res-extra');
    lineaExtra.textContent = extra.join(' ');
    lineaExtra.hidden = extra.length === 0;

    const lista = $('res-logros');
    lista.replaceChildren();
    r.logros_nuevos.forEach((l) => {
      lista.appendChild(crear('li', 'logro-nuevo', 'Nuevo logro: ' + l.nombre));
    });

    const seguir = $('res-continuar');
    if (r.siguiente_leccion) {
      seguir.href = '/leccion/' + r.siguiente_leccion.id;
      seguir.hidden = false;
    } else {
      seguir.hidden = true;
    }
  }

  async function terminarLeccion() {
    $('retro-error').hidden = true;
    ponerOcupado(true);
    try {
      const r = await Api.post('/attempts/' + estado.intentoId + '/complete');
      ponerOcupado(false);
      pintarResultados(r);
      mostrarPantalla('resultados');
    } catch (error) {
      ponerOcupado(false);
      manejarError(error, 'No pudimos cerrar la lección.');
    }
  }

  async function continuar() {
    if (estado.terminado === 'sin_corazones') {
      mostrarPantalla('sincorazones');
      return;
    }
    if (estado.listo) {
      await terminarLeccion();
      return;
    }
    if (estado.siguiente) mostrarPregunta(estado.siguiente);
  }

  function accionPrincipal() {
    if (estado.ocupado || boton.disabled) return;
    if (estado.fase === 'responder') comprobar();
    else if (estado.fase === 'continuar') continuar();
  }

  function aplicarIntento(d) {
    estado.intentoId = d.intento_id;
    estado.total = d.total;
    estado.respondidas = d.respondidas;
    estado.corazones = d.corazones;
    estado.maximos = d.corazones_maximos;
    pintarProgreso();
    pintarCorazones(false);
    $('nota-reanudado').hidden = !(d.reanudado && d.respondidas > 0);

    if (d.pregunta) {
      mostrarPregunta(d.pregunta);
      return;
    }
    // Ya estaban todas respondidas: solo falta cerrar la lección.
    ejercicio = null;
    estado.fase = 'continuar';
    estado.listo = true;
    $('instrucciones').textContent = '¡Terminaste las preguntas!';
    $('enunciado').textContent = 'Solo falta ver tu resultado.';
    $('ejercicio').replaceChildren();
    $('boton-principal-texto').textContent = 'Ver resultados';
    limpiarRetro();
    mostrarPantalla('ejercicio');
    actualizarBoton();
    boton.focus();
  }

  async function iniciar() {
    mostrarPantalla('cargando');
    if (!Number.isInteger(leccionId) || leccionId < 1) {
      mostrarPantallaError('No encontramos esa lección.', false);
      return;
    }
    try {
      const yo = await Api.yo();
      if (yo.usuario.rol !== 'estudiante') {
        window.location.replace(Api.rutaInicio(yo.usuario.rol));
        return;
      }
      aplicarIntento(await Api.post('/lessons/' + leccionId + '/attempts'));
    } catch (error) {
      if (error.estado === 401) {
        window.location.replace('/acceso');
        return;
      }
      if (error.codigo === 'sin_corazones') {
        mostrarPantalla('sincorazones');
        return;
      }
      mostrarPantallaError(
        error.mensaje || 'No pudimos abrir la lección.',
        error.estado === 0 || error.estado >= 500
      );
    }
  }

  /* ---------- Eventos ---------- */
  boton.addEventListener('click', accionPrincipal);
  $('error-reintentar').addEventListener('click', iniciar);

  $('boton-salir').addEventListener('click', () => dialogo.showModal());
  $('dialogo-seguir').addEventListener('click', () => dialogo.close());
  $('dialogo-confirmar').addEventListener('click', async () => {
    $('dialogo-confirmar').disabled = true;
    try {
      if (estado.intentoId) await Api.post('/attempts/' + estado.intentoId + '/abandon');
    } catch (_) {
      /* si falla, el intento queda en curso y se reanuda la próxima vez */
    }
    window.location.assign('/recorrido');
  });

  document.addEventListener('keydown', (e) => {
    if (dialogo.open || $('pantalla-ejercicio').hidden) return;
    if (e.key === 'Enter' && !e.target.closest('button') && !boton.disabled) {
      e.preventDefault();
      accionPrincipal();
      return;
    }
    // Teclas 1-9 eligen la opción correspondiente.
    if (estado.fase === 'responder' && /^[1-9]$/.test(e.key)
        && !e.target.matches('input[type="text"]')) {
      const radios = document.querySelectorAll('input[name="opcion"]');
      const radio = radios[Number(e.key) - 1];
      if (radio) {
        radio.checked = true;
        radio.focus();
        actualizarBoton();
      }
    }
  });

  iniciar();
})();