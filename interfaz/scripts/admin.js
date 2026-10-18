/* Panel de administración. Toda la lógica y las validaciones reales viven en el
 * servidor; aquí solo se piden y se muestran datos. Se usa textContent, nunca
 * innerHTML con datos. */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);

  function crear(etiqueta, clase, texto) {
    const e = document.createElement(etiqueta);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  function boton(texto, clase, alHacerClic, etiqueta) {
    const b = crear('button', 'boton boton--chico ' + clase, texto);
    b.type = 'button';
    if (etiqueta) b.setAttribute('aria-label', etiqueta);
    b.addEventListener('click', alHacerClic);
    return b;
  }

  const COL = { curso: 'courses', unidad: 'units', leccion: 'lessons', pregunta: 'questions' };
  const CAMPO_PUBLICADO = { curso: 'publicado', unidad: 'publicado', leccion: 'publicada', pregunta: 'publicada' };
  const TIPOS = {
    seleccion: 'Elegir la traducción',
    completar_opcion: 'Completar con opciones',
    traducir_es_en: 'Traducir al inglés (escribir)',
    traducir_en_es: 'Traducir al español (escribir)',
    completar_texto: 'Completar escribiendo',
    ordenar_palabras: 'Ordenar palabras',
  };
  const TIPOS_ELEGIR = ['seleccion', 'completar_opcion'];
  const TIPOS_HUECO = ['completar_opcion', 'completar_texto'];
  const ESTADOS = {
    completada: 'Completada', en_progreso: 'En progreso',
    disponible: 'Disponible', bloqueada: 'Bloqueada',
  };

  /* ---------- Utilidades ---------- */
  async function ejecutar(accion, zona) {
    zona.hidden = true;
    try {
      await accion();
      return true;
    } catch (error) {
      if (error.estado === 401) {
        window.location.replace('/acceso');
        return false;
      }
      zona.textContent = error.mensaje || 'Algo salió mal. Inténtalo de nuevo.';
      zona.hidden = false;
      return false;
    }
  }

  function confirmar(titulo, texto, textoBoton) {
    return new Promise((resolver) => {
      const d = $('dialogo-conf');
      let respuesta = false;
      $('conf-titulo').textContent = titulo;
      $('conf-texto').textContent = texto;
      $('conf-ok').textContent = textoBoton || 'Confirmar';
      $('conf-ok').onclick = () => { respuesta = true; d.close(); };
      $('conf-no').onclick = () => { d.close(); };
      d.onclose = () => resolver(respuesta);
      d.showModal();
    });
  }

  function fechaCorta(iso) {
    if (!iso) return '';
    const f = new Date(iso.length === 10 ? iso + 'T12:00:00' : iso);
    return isNaN(f) ? '' : f.toLocaleDateString('es', { day: 'numeric', month: 'short' });
  }

  function chipPublicado(publicado) {
    return crear('span', 'estado-chip' + (publicado ? ' estado-chip--ok' : ''),
      publicado ? 'Publicado' : 'Borrador');
  }

  /* ---------- Acciones comunes ---------- */
  function barraAcciones(opc) {
    const { tipo, obj, zona, recargar, editar } = opc;
    const publicado = obj[CAMPO_PUBLICADO[tipo]];
    const barra = crear('div', 'fila-acciones');
    (opc.extras || []).forEach((x) => barra.appendChild(x));

    const mover = (direccion) => ejecutar(async () => {
      await Api.post('/admin/' + COL[tipo] + '/' + obj.id + '/move', { direccion });
      await recargar();
    }, zona);

    barra.append(
      boton(publicado ? 'Despublicar' : 'Publicar', 'boton--secundario', () => ejecutar(async () => {
        await Api.patch('/admin/' + COL[tipo] + '/' + obj.id, { [CAMPO_PUBLICADO[tipo]]: !publicado });
        await recargar();
      }, zona)),
      boton('↑', 'boton--secundario', () => mover('arriba'), 'Subir'),
      boton('↓', 'boton--secundario', () => mover('abajo'), 'Bajar'),
      boton('Editar', 'boton--secundario', editar),
      boton('Borrar', 'boton--peligro', async () => {
        const nombre = obj.titulo || obj.texto;
        const si = await confirmar('¿Borrar «' + nombre + '»?',
          'Se borra también todo lo que contiene. Esta acción no se puede deshacer.', 'Borrar');
        if (!si) return;
        await ejecutar(async () => {
          await Api.borrar('/admin/' + COL[tipo] + '/' + obj.id);
          await recargar();
        }, zona);
      })
    );
    return barra;
  }

  /* ---------- Formulario genérico (curso, unidad, lección) ---------- */
  let formActual = null;

  function abrirFormulario(cfg) {
    formActual = cfg;
    $('form-titulo').textContent = cfg.titulo;
    $('form-error').hidden = true;
    const cont = $('form-campos');
    cont.replaceChildren();
    cfg.campos.forEach((c) => {
      const caja = crear('div', 'campo');
      const id = 'f-' + c.nombre;
      const etiqueta = crear('label', '', c.etiqueta);
      etiqueta.htmlFor = id;
      let entrada;
      if (c.tipo === 'textarea') {
        entrada = crear('textarea', 'entrada');
      } else {
        entrada = crear('input', 'entrada');
        entrada.type = c.tipo === 'number' ? 'number' : 'text';
        if (c.tipo === 'number') { entrada.min = '0'; entrada.max = '1000'; }
      }
      entrada.id = id;
      if (c.max) entrada.maxLength = c.max;
      if (c.requerido) entrada.required = true;
      entrada.value = c.valor === null || c.valor === undefined ? '' : String(c.valor);
      caja.append(etiqueta, entrada);
      cont.appendChild(caja);
    });
    $('dialogo-form').showModal();
    cont.querySelector('input, textarea').focus();
  }

  function recogerFormulario() {
    const datos = {};
    formActual.campos.forEach((c) => {
      const v = $('f-' + c.nombre).value.trim();
      if (c.tipo === 'number') {
        if (v !== '') datos[c.nombre] = Number(v);
      } else if (!(c.omitirVacio && v === '')) {
        datos[c.nombre] = v;
      }
    });
    return datos;
  }

  $('form-cancelar').addEventListener('click', () => $('dialogo-form').close());
  $('form-generico').addEventListener('submit', async (e) => {
    e.preventDefault();
    const guardar = $('form-guardar');
    guardar.disabled = true;
    const ok = await ejecutar(() => formActual.guardar(recogerFormulario()), $('form-error'));
    guardar.disabled = false;
    if (ok) {
      $('dialogo-form').close();
      await cargarArbol();
    }
  });

  function camposDe(tipo, o) {
    o = o || {};
    const titulo = { nombre: 'titulo', etiqueta: 'Título', max: 120, requerido: true, valor: o.titulo };
    if (tipo === 'curso') {
      return [
        titulo,
        { nombre: 'descripcion', etiqueta: 'Descripción', tipo: 'textarea', max: 2000, valor: o.descripcion },
        { nombre: 'nivel', etiqueta: 'Nivel (por ejemplo A1 o A2)', max: 10, omitirVacio: true, valor: o.nivel || 'A1' },
      ];
    }
    const descripcion = { nombre: 'descripcion', etiqueta: 'Descripción', max: 255, valor: o.descripcion };
    if (tipo === 'unidad') return [titulo, descripcion];
    return [titulo, descripcion,
      { nombre: 'xp_base', etiqueta: 'XP base de la lección', tipo: 'number', valor: o.xp_base === undefined ? 10 : o.xp_base }];
  }

  const TITULOS_FORM = {
    curso: ['Nuevo curso', 'Editar curso'],
    unidad: ['Nueva unidad', 'Editar unidad'],
    leccion: ['Nueva lección', 'Editar lección'],
  };

  function formularioElemento(tipo, obj, padreId) {
    const nuevo = !obj;
    abrirFormulario({
      titulo: TITULOS_FORM[tipo][nuevo ? 0 : 1],
      campos: camposDe(tipo, obj),
      guardar: (datos) => {
        if (!nuevo) return Api.patch('/admin/' + COL[tipo] + '/' + obj.id, datos);
        const ruta = tipo === 'curso' ? '/admin/courses'
          : tipo === 'unidad' ? '/admin/courses/' + padreId + '/units'
          : '/admin/units/' + padreId + '/lessons';
        return Api.post(ruta, datos);
      },
    });
  }

  /* ---------- Árbol de contenido ---------- */
  let contenido = [];

  function pintarLeccion(leccion, unidad) {
    const li = crear('li', 'n-leccion');
    const cab = crear('div', 'fila-cab');
    const titulo = crear('div', 'fila-cab__titulo');
    titulo.append(
      crear('h4', '', leccion.orden + '. ' + leccion.titulo),
      chipPublicado(leccion.publicada),
      crear('span', 'ayuda', leccion.num_publicadas + ' de ' + leccion.num_preguntas + ' preguntas publicadas')
    );
    cab.append(titulo, barraAcciones({
      tipo: 'leccion', obj: leccion, zona: $('mensaje'), recargar: cargarArbol,
      editar: () => formularioElemento('leccion', leccion),
      extras: [boton('Preguntas', '', () => abrirPreguntas(leccion))],
    }));
    li.appendChild(cab);
    return li;
  }

  function pintarUnidad(unidad) {
    const li = crear('li', 'n-unidad');
    const cab = crear('div', 'fila-cab');
    const titulo = crear('div', 'fila-cab__titulo');
    titulo.append(crear('h3', '', 'Unidad ' + unidad.orden + ' · ' + unidad.titulo), chipPublicado(unidad.publicado));
    cab.append(titulo, barraAcciones({
      tipo: 'unidad', obj: unidad, zona: $('mensaje'), recargar: cargarArbol,
      editar: () => formularioElemento('unidad', unidad),
    }));
    li.appendChild(cab);
    if (unidad.descripcion) li.appendChild(crear('p', 'ayuda', unidad.descripcion));

    const lista = crear('ul', 'lecciones');
    unidad.lecciones.forEach((l) => lista.appendChild(pintarLeccion(l, unidad)));
    li.appendChild(lista);
    const pie = crear('div', 'pie-nodo');
    pie.appendChild(boton('+ Nueva lección', 'boton--secundario', () => formularioElemento('leccion', null, unidad.id)));
    li.appendChild(pie);
    return li;
  }

  function pintarCurso(curso) {
    const art = crear('article', 'tarjeta');
    const cab = crear('div', 'fila-cab');
    const titulo = crear('div', 'fila-cab__titulo');
    titulo.append(crear('h2', '', curso.titulo), crear('span', 'estado-chip', curso.nivel), chipPublicado(curso.publicado));
    cab.append(titulo, barraAcciones({
      tipo: 'curso', obj: curso, zona: $('mensaje'), recargar: cargarArbol,
      editar: () => formularioElemento('curso', curso),
    }));
    art.appendChild(cab);
    if (curso.descripcion) art.appendChild(crear('p', 'ayuda', curso.descripcion));

    const lista = crear('ul', 'unidades');
    curso.unidades.forEach((u) => lista.appendChild(pintarUnidad(u)));
    art.appendChild(lista);
    const pie = crear('div', 'pie-nodo');
    pie.appendChild(boton('+ Nueva unidad', 'boton--secundario', () => formularioElemento('unidad', null, curso.id)));
    art.appendChild(pie);
    return art;
  }

  function pintarArbol() {
    const cont = $('arbol');
    cont.replaceChildren();
    if (contenido.length === 0) {
      cont.appendChild(crear('p', 'vacio', 'Aún no hay cursos. Crea el primero.'));
      return;
    }
    contenido.forEach((c) => cont.appendChild(pintarCurso(c)));
  }

  async function cargarArbol() {
    await ejecutar(async () => {
      contenido = (await Api.get('/admin/content')).cursos;
      pintarArbol();
    }, $('mensaje'));
  }

  $('nuevo-curso').addEventListener('click', () => formularioElemento('curso', null));

  /* ---------- Preguntas de una lección ---------- */
  let leccionActual = null;

  async function cargarPreguntas() {
    await ejecutar(async () => {
      const datos = await Api.get('/admin/lessons/' + leccionActual.id + '/questions');
      const lista = $('preguntas-lista');
      lista.replaceChildren();
      if (datos.preguntas.length === 0) {
        lista.appendChild(crear('li', 'vacio', 'Esta lección todavía no tiene preguntas.'));
        return;
      }
      datos.preguntas.forEach((p) => {
        const li = crear('li', 'fila-pregunta');
        const texto = crear('div', 'fila-pregunta__texto');
        texto.append(
          crear('span', 'fila-pregunta__enunciado', p.orden + '. ' + p.texto),
          crear('span', 'fila-pregunta__tipo', TIPOS[p.tipo] || p.tipo),
          chipPublicado(p.publicada)
        );
        li.append(texto, barraAcciones({
          tipo: 'pregunta', obj: p, zona: $('preguntas-error'), recargar: recargarPreguntas,
          editar: () => abrirEditorPregunta(p),
        }));
        lista.appendChild(li);
      });
    }, $('preguntas-error'));
  }

  async function recargarPreguntas() {
    await cargarPreguntas();
    await cargarArbol();
  }

  function abrirPreguntas(leccion) {
    leccionActual = leccion;
    $('preguntas-titulo').textContent = 'Preguntas · ' + leccion.titulo;
    $('preguntas-error').hidden = true;
    $('preguntas-lista').replaceChildren();
    $('dialogo-preguntas').showModal();
    cargarPreguntas();
  }

  $('preguntas-cerrar').addEventListener('click', () => $('dialogo-preguntas').close());
  $('pregunta-nueva').addEventListener('click', () => abrirEditorPregunta(null));

  /* ---------- Editor de pregunta ---------- */
  let ep = null; // { id, tipo, opciones: [{texto, es_correcta}], ordenTexto }

  function opcionesVacias(tipo) {
    if (tipo === 'ordenar_palabras') return [];
    const n = TIPOS_ELEGIR.includes(tipo) ? 3 : 2;
    return Array.from({ length: n }, () => ({ texto: '', es_correcta: false }));
  }

  function normalizarOpciones() {
    if (TIPOS_ELEGIR.includes(ep.tipo)) {
      while (ep.opciones.length < 2) ep.opciones.push({ texto: '', es_correcta: false });
      if (!ep.opciones.some((o) => o.es_correcta)) ep.opciones[0].es_correcta = true;
    } else if (ep.tipo !== 'ordenar_palabras' && ep.opciones.length === 0) {
      ep.opciones.push({ texto: '', es_correcta: false });
    }
  }

  function pintarOpciones() {
    const cont = $('p-opciones');
    cont.replaceChildren();
    const tipo = ep.tipo;
    $('p-ayuda-texto').textContent = TIPOS_HUECO.includes(tipo)
      ? 'Debe incluir el hueco ___ (tres guiones bajos).' : '';

    if (tipo === 'ordenar_palabras') {
      const caja = crear('div', 'campo');
      const etiqueta = crear('label', '', 'Frase en el orden correcto');
      etiqueta.htmlFor = 'p-orden';
      const area = crear('textarea', 'entrada');
      area.id = 'p-orden';
      area.value = ep.ordenTexto;
      area.addEventListener('input', () => { ep.ordenTexto = area.value; });
      caja.append(etiqueta, area,
        crear('p', 'ayuda', 'Cada palabra será una ficha. El estudiante las verá mezcladas.'));
      cont.appendChild(caja);
      return;
    }

    const elegir = TIPOS_ELEGIR.includes(tipo);
    cont.appendChild(crear('p', 'campo-titulo',
      elegir ? 'Opciones (marca la correcta)' : 'Respuestas aceptadas (todas valen)'));
    ep.opciones.forEach((o, i) => {
      const fila = crear('div', 'opcion-fila');
      if (elegir) {
        const radio = crear('input');
        radio.type = 'radio';
        radio.name = 'correcta';
        radio.checked = o.es_correcta;
        radio.setAttribute('aria-label', 'Opción ' + (i + 1) + ' es la correcta');
        radio.addEventListener('change', () => ep.opciones.forEach((x, j) => { x.es_correcta = j === i; }));
        fila.appendChild(radio);
      }
      const entrada = crear('input', 'entrada');
      entrada.type = 'text';
      entrada.maxLength = 255;
      entrada.value = o.texto;
      entrada.setAttribute('aria-label', (elegir ? 'Texto de la opción ' : 'Respuesta ') + (i + 1));
      entrada.addEventListener('input', () => { o.texto = entrada.value; });
      fila.append(entrada, boton('Quitar', 'boton--secundario', () => {
        ep.opciones.splice(i, 1);
        normalizarOpciones();
        pintarOpciones();
      }));
      cont.appendChild(fila);
    });
    const mas = boton(elegir ? '+ Añadir opción' : '+ Añadir respuesta', 'boton--secundario', () => {
      ep.opciones.push({ texto: '', es_correcta: false });
      pintarOpciones();
    });
    mas.classList.add('mt');
    cont.appendChild(mas);
  }

  function cambiarTipo(nuevo) {
    const cambioDeGrupo = (ep.tipo === 'ordenar_palabras') !== (nuevo === 'ordenar_palabras');
    ep.tipo = nuevo;
    if (cambioDeGrupo) {
      ep.opciones = opcionesVacias(nuevo);
      ep.ordenTexto = '';
    }
    normalizarOpciones();
    pintarOpciones();
  }

  function abrirEditorPregunta(p) {
    const select = $('p-tipo');
    if (select.options.length === 0) {
      Object.keys(TIPOS).forEach((k) => {
        const op = crear('option', '', TIPOS[k]);
        op.value = k;
        select.appendChild(op);
      });
      select.addEventListener('change', () => cambiarTipo(select.value));
    }
    const tipo = p ? p.tipo : 'seleccion';
    ep = {
      id: p ? p.id : null,
      tipo,
      opciones: p && tipo !== 'ordenar_palabras'
        ? p.opciones.map((o) => ({ texto: o.texto, es_correcta: o.es_correcta }))
        : opcionesVacias(tipo),
      ordenTexto: p && tipo === 'ordenar_palabras' ? p.opciones.map((o) => o.texto).join(' ') : '',
    };
    $('p-titulo').textContent = p ? 'Editar pregunta' : 'Nueva pregunta';
    select.value = tipo;
    $('p-instrucciones').value = p && p.instrucciones ? p.instrucciones : '';
    $('p-texto').value = p ? p.texto : '';
    $('p-explicacion').value = p && p.explicacion ? p.explicacion : '';
    $('p-publicada').checked = p ? p.publicada : true;
    $('p-error').hidden = true;
    normalizarOpciones();
    pintarOpciones();
    $('dialogo-pregunta').showModal();
    $('p-texto').focus();
  }

  function recogerOpciones() {
    if (ep.tipo === 'ordenar_palabras') {
      return ep.ordenTexto.split(/\s+/).filter(Boolean).map((t) => ({ texto: t, es_correcta: true }));
    }
    const llenas = ep.opciones.filter((o) => o.texto.trim());
    if (TIPOS_ELEGIR.includes(ep.tipo)) {
      return llenas.map((o) => ({ texto: o.texto.trim(), es_correcta: o.es_correcta }));
    }
    return llenas.map((o) => ({ texto: o.texto.trim(), es_correcta: true }));
  }

  $('p-cancelar').addEventListener('click', () => $('dialogo-pregunta').close());
  $('form-pregunta').addEventListener('submit', async (e) => {
    e.preventDefault();
    const cuerpo = {
      tipo: ep.tipo,
      instrucciones: $('p-instrucciones').value.trim(),
      texto: $('p-texto').value.trim(),
      explicacion: $('p-explicacion').value.trim(),
      publicada: $('p-publicada').checked,
      opciones: recogerOpciones(),
    };
    const guardar = $('p-guardar');
    guardar.disabled = true;
    const ok = await ejecutar(() => (ep.id
      ? Api.patch('/admin/questions/' + ep.id, cuerpo)
      : Api.post('/admin/lessons/' + leccionActual.id + '/questions', cuerpo)), $('p-error'));
    guardar.disabled = false;
    if (ok) {
      $('dialogo-pregunta').close();
      await recargarPreguntas();
    }
  });

  /* ---------- Estudiantes ---------- */
  let alumnoId = null;
  let alumnosCargados = false;

  function pintarAlumnos(alumnos) {
    const cont = $('lista-alumnos');
    cont.replaceChildren();
    if (alumnos.length === 0) {
      cont.appendChild(crear('p', 'vacio', 'Todavía no hay estudiantes. Créalos con el comando crear-usuario.'));
      return;
    }
    alumnos.forEach((a) => {
      const t = crear('article', 'tarjeta alumno');
      t.append(
        crear('h3', '', a.nombre_mostrar),
        crear('p', '', '@' + a.nombre_usuario),
        crear('p', '', a.xp_total + ' XP · nivel ' + a.nivel + ' · racha ' + a.racha_actual +
          ' · ' + a.corazones + ' corazones'),
        crear('p', '', a.lecciones_completadas + ' de ' + a.total_lecciones + ' lecciones' +
          (a.ultima_actividad ? ' · última actividad: ' + fechaCorta(a.ultima_actividad) : '')),
        boton('Ver y administrar', '', () => abrirDetalle(a.id))
      );
      cont.appendChild(t);
    });
  }

  async function cargarEstudiantes() {
    await ejecutar(async () => {
      pintarAlumnos((await Api.get('/admin/students')).estudiantes);
      alumnosCargados = true;
    }, $('alumno-error'));
  }

  function accionAlumno(accion) {
    return ejecutar(async () => {
      await accion();
      await recargarDetalle();
    }, $('alumno-error'));
  }

  async function recargarDetalle() {
    const d = await Api.get('/admin/students/' + alumnoId);
    pintarDetalle(d);
  }

  function abrirDetalle(id) {
    alumnoId = id;
    return ejecutar(async () => {
      await recargarDetalle();
      $('lista-alumnos-caja').hidden = true;
      $('detalle-alumno').hidden = false;
    }, $('alumno-error'));
  }

  function tarjeta(titulo) {
    const t = crear('section', 'tarjeta');
    t.appendChild(crear('h3', '', titulo));
    return t;
  }

  function pintarDetalle(d) {
    const cont = $('detalle-alumno');
    cont.replaceChildren();
    const a = d.estudiante;
    const e = d.estadisticas;

    cont.append(
      boton('← Volver al listado', 'boton--secundario', () => {
        $('detalle-alumno').hidden = true;
        $('lista-alumnos-caja').hidden = false;
        cargarEstudiantes();
      }),
      crear('h2', '', a.nombre_mostrar + ' (@' + a.nombre_usuario + ')')
    );

    // Estadísticas
    const est = tarjeta('Estadísticas');
    const cifras = crear('dl', 'cifras-admin');
    [['XP', e.xp_total], ['Nivel', e.nivel], ['Racha', e.racha_actual],
      ['Mejor racha', e.mejor_racha], ['Corazones', e.corazones + ' / ' + e.corazones_maximos]]
      .forEach(([k, v]) => {
        const caja = crear('div', 'cifra-admin');
        caja.append(crear('dt', '', k), crear('dd', '', String(v)));
        cifras.appendChild(caja);
      });
    est.appendChild(cifras);

    const form = crear('form', 'form-fila');
    const campoXp = crear('div', 'campo');
    const etXp = crear('label', '', 'XP total'); etXp.htmlFor = 'al-xp';
    const inXp = crear('input', 'entrada'); inXp.id = 'al-xp'; inXp.type = 'number';
    inXp.min = '0'; inXp.max = '1000000'; inXp.value = String(e.xp_total); inXp.required = true;
    campoXp.append(etXp, inXp);
    const campoCo = crear('div', 'campo');
    const etCo = crear('label', '', 'Corazones'); etCo.htmlFor = 'al-co';
    const inCo = crear('input', 'entrada'); inCo.id = 'al-co'; inCo.type = 'number';
    inCo.min = '0'; inCo.max = String(e.corazones_maximos); inCo.value = String(e.corazones); inCo.required = true;
    campoCo.append(etCo, inCo);
    const enviar = crear('button', 'boton boton--chico', 'Guardar cambios');
    enviar.type = 'submit';
    form.append(campoXp, campoCo, enviar);
    form.addEventListener('submit', (ev) => {
      ev.preventDefault();
      accionAlumno(() => Api.patch('/admin/students/' + alumnoId + '/stats',
        { xp_total: Number(inXp.value), corazones: Number(inCo.value) }));
    });
    est.append(form, crear('p', 'ayuda', 'Fijar los corazones evita que se restauren hasta mañana.'));
    cont.appendChild(est);

    // Lecciones
    const lec = tarjeta('Lecciones');
    const lista = crear('ul', 'lista-al');
    let unidadPrevia = null;
    d.lecciones.forEach((l) => {
      if (l.unidad_orden !== unidadPrevia) {
        unidadPrevia = l.unidad_orden;
        lista.appendChild(crear('li', 'grupo', 'Unidad ' + l.unidad_orden + ' · ' + l.unidad_titulo));
      }
      const li = crear('li');
      const info = crear('span', '', l.orden + '. ' + l.titulo + ' ');
      info.appendChild(crear('span',
        'estado-chip' + (l.estado === 'completada' ? ' estado-chip--ok'
          : l.estado === 'bloqueada' ? '' : ' estado-chip--rosa'),
        ESTADOS[l.estado] || l.estado));
      if (l.veces_completada > 0) {
        info.appendChild(crear('span', 'ayuda', ' · mejor precisión ' + l.mejor_precision + ' %'));
      }
      const acciones = crear('div', 'fila-acciones');
      acciones.appendChild(boton('Completar hasta aquí', 'boton--secundario', async () => {
        const si = await confirmar('¿Completar hasta «' + l.titulo + '»?',
          'Se marcan como completadas esta lección y todas las anteriores. No da XP, racha ni logros.', 'Completar');
        if (si) accionAlumno(() => Api.post('/admin/students/' + alumnoId + '/lessons/' + l.id + '/complete-until'));
      }));
      if (l.estado === 'completada' || l.estado === 'en_progreso') {
        acciones.appendChild(boton('Reiniciar', 'boton--secundario', async () => {
          const si = await confirmar('¿Reiniciar «' + l.titulo + '»?',
            'Se borra su progreso y se abandonan los intentos en curso. El XP ya ganado no se descuenta.', 'Reiniciar');
          if (si) accionAlumno(() => Api.post('/admin/students/' + alumnoId + '/lessons/' + l.id + '/reset'));
        }));
      }
      li.append(info, acciones);
      lista.appendChild(li);
    });
    lec.appendChild(lista);
    cont.appendChild(lec);

    // Actividad
    const act = tarjeta('Últimos 14 días');
    const semana = crear('ul', 'semana-admin');
    d.actividad.forEach((x) => {
      const li = crear('li', x.activo ? 'activo' : '');
      li.setAttribute('aria-label', fechaCorta(x.fecha) + (x.activo ? ': ' + x.xp + ' XP' : ': sin actividad'));
      li.title = fechaCorta(x.fecha) + (x.activo ? ' · ' + x.xp + ' XP' : '');
      semana.appendChild(li);
    });
    act.appendChild(semana);
    cont.appendChild(act);

    // Logros
    const log = tarjeta('Logros');
    const chips = crear('ul', 'chips');
    d.logros.forEach((l) => {
      chips.appendChild(crear('li', 'estado-chip' + (l.desbloqueado ? ' estado-chip--rosa' : ''),
        l.nombre + (l.desbloqueado ? '' : ' (bloqueado)')));
    });
    log.appendChild(chips);
    cont.appendChild(log);

    // Intentos
    const intentos = tarjeta('Últimos intentos');
    if (d.intentos.length === 0) {
      intentos.appendChild(crear('p', 'vacio', 'Todavía no hay intentos.'));
    } else {
      const li = crear('ul', 'lista-al');
      d.intentos.forEach((i) => {
        const fila = crear('li');
        fila.append(
          crear('span', '', i.leccion_titulo + ' · ' + i.estado.replace('_', ' ')),
          crear('span', 'ayuda', i.aciertos + ' aciertos, ' + i.errores + ' errores, ' + i.xp_ganado +
            ' XP · ' + fechaCorta(i.iniciado_en))
        );
        li.appendChild(fila);
      });
      intentos.appendChild(li);
    }
    cont.appendChild(intentos);

    // Zona de peligro
    const peligro = tarjeta('Zona de peligro');
    peligro.classList.add('zona-peligro');
    peligro.append(
      crear('p', 'ayuda', 'Borra progreso, intentos, actividad y logros, y deja XP, racha y corazones como al inicio.'),
      crear('div', 'pie-nodo')
    );
    peligro.lastChild.appendChild(boton('Reiniciar todo el progreso', 'boton--peligro', async () => {
      const si = await confirmar('¿Reiniciar todo el progreso de ' + a.nombre_mostrar + '?',
        'Esta acción no se puede deshacer.', 'Reiniciar todo');
      if (si) accionAlumno(() => Api.post('/admin/students/' + alumnoId + '/reset', { confirmar: true }));
    }));
    cont.appendChild(peligro);
  }

  /* ---------- Pestañas, sesión e inicio ---------- */
  function mostrarVista(vista) {
    const contenidoActivo = vista === 'contenido';
    $('vista-contenido').hidden = !contenidoActivo;
    $('vista-estudiantes').hidden = contenidoActivo;
    $('pestana-contenido').setAttribute('aria-pressed', String(contenidoActivo));
    $('pestana-estudiantes').setAttribute('aria-pressed', String(!contenidoActivo));
    if (!contenidoActivo && !alumnosCargados) cargarEstudiantes();
  }

  $('pestana-contenido').addEventListener('click', () => mostrarVista('contenido'));
  $('pestana-estudiantes').addEventListener('click', () => mostrarVista('estudiantes'));

  $('boton-salir').addEventListener('click', async () => {
    $('boton-salir').disabled = true;
    try { await Api.logout(); } catch (_) { /* volvemos al inicio igualmente */ }
    window.location.replace('/');
  });

  async function iniciar() {
    try {
      const yo = await Api.yo();
      if (yo.usuario.rol !== 'admin') {
        window.location.replace(Api.rutaInicio(yo.usuario.rol));
        return;
      }
      $('admin-nombre').textContent = 'Sesión de ' + yo.usuario.nombre_mostrar + ' (administrador)';
    } catch (error) {
      if (error.estado === 401) {
        window.location.replace('/acceso');
        return;
      }
      $('mensaje').textContent = error.mensaje || 'No pudimos cargar el panel.';
      $('mensaje').hidden = false;
      return;
    }
    await cargarArbol();
  }

  iniciar();
})();