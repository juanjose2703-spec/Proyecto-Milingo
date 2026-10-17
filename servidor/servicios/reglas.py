"""Reglas de Milingo en un solo lugar. Cambiar un número aquí cambia el juego.

XP:
  - Completar una lección da XP_BASE_LECCION (o el xp_base de la lección).
  - Cada respuesta correcta a la primera da XP_POR_ACIERTO.
  - Repetir una lección ya completada da la mitad (FACTOR_REPETICION).
Corazones:
  - Empiezan en CORAZONES_INICIALES; cada error descuenta 1.
  - Con 0 corazones el intento termina sin XP.
  - Se restauran al máximo cuando cambia el día local.
Rachas:
  - Sube como máximo 1 vez por día local con actividad.
"""

CORAZONES_INICIALES = 5
CORAZONES_MAXIMOS = 5
XP_BASE_LECCION = 10
XP_POR_ACIERTO = 2
FACTOR_REPETICION = 0.5
PRECISION_LOGRO_ALTA = 90  # porcentaje para el logro de buena precisión

ROL_ADMIN = "admin"
ROL_ESTUDIANTE = "estudiante"
ROLES = (ROL_ADMIN, ROL_ESTUDIANTE)

ESTADO_EN_CURSO = "en_curso"
ESTADO_COMPLETADO = "completado"
ESTADO_ABANDONADO = "abandonado"
ESTADO_SIN_CORAZONES = "sin_corazones"


XP_POR_NIVEL = 100

LECCION_BLOQUEADA = "bloqueada"
LECCION_DISPONIBLE = "disponible"
LECCION_EN_PROGRESO = "en_progreso"
LECCION_COMPLETADA = "completada"