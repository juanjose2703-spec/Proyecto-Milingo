"""Contenido del curso A1 (por ahora, solo la Unidad 1).

Formato de cada pregunta:
  tipo          -> seleccion, completar_opcion, traducir_es_en, traducir_en_es,
                   completar_texto u ordenar_palabras.
  opciones      -> lista de (texto, es_correcta):
      seleccion / completar_opcion: una correcta y varios distractores.
      traducir_* / completar_texto: todas las respuestas ACEPTADAS (todas correctas).
      ordenar_palabras: las fichas en el ORDEN CORRECTO (el servidor las mezcla).

Nota para la 4d: al comparar texto escrito, el servidor ignorará mayúsculas,
tildes, espacios sobrantes y puntuación.
"""


def _op(correcta, *distractores):
    return [(correcta, True)] + [(d, False) for d in distractores]


def _aceptadas(*textos):
    return [(t, True) for t in textos]


def _fichas(*palabras):
    return [(p, True) for p in palabras]


CURSO_A1 = {
    "titulo": "Inglés A1",
    "descripcion": "Tus primeros pasos en inglés, desde cero.",
    "nivel": "A1",
    "orden": 1,
    "unidades": [
        {
            "titulo": "Hello!",
            "descripcion": "Saludos y despedidas",
            "lecciones": [
                {
                    "titulo": "Hola y adiós",
                    "descripcion": "Saluda y despídete en inglés.",
                    "preguntas": [
                        {
                            "tipo": "seleccion",
                            "instrucciones": "Selecciona la traducción correcta",
                            "texto": "Hello",
                            "opciones": _op("Hola", "Adiós", "Gracias", "Por favor"),
                            "explicacion": "«Hello» es el saludo más común en inglés y significa «Hola».",
                        },
                        {
                            "tipo": "seleccion",
                            "instrucciones": "Selecciona la traducción correcta",
                            "texto": "Goodbye",
                            "opciones": _op("Adiós", "Hola", "Gracias", "Perdón"),
                            "explicacion": "«Goodbye» se usa para despedirse: significa «Adiós».",
                        },
                        {
                            "tipo": "completar_opcion",
                            "instrucciones": "Completa la frase: «¡Hola, Ana!»",
                            "texto": "___, Ana!",
                            "opciones": _op("Hello", "Goodbye", "Please", "Sorry"),
                            "explicacion": "Para saludar usamos «Hello». «Goodbye» sirve para despedirse.",
                        },
                        {
                            "tipo": "traducir_es_en",
                            "instrucciones": "Escribe en inglés",
                            "texto": "Hola",
                            "opciones": _aceptadas("Hello", "Hi"),
                            "explicacion": "«Hello» es el saludo estándar. «Hi» también es correcto y es más informal.",
                        },
                        {
                            "tipo": "traducir_en_es",
                            "instrucciones": "Escribe en español",
                            "texto": "Hello, friend!",
                            "opciones": _aceptadas("Hola, amigo", "Hola, amiga"),
                            "explicacion": "«Friend» significa «amigo» o «amiga». «Hello, friend!» es «¡Hola, amigo!».",
                        },
                        {
                            "tipo": "ordenar_palabras",
                            "instrucciones": "Ordena las palabras para formar la frase",
                            "texto": "Hola, mi amigo",
                            "opciones": _fichas("Hello", "my", "friend"),
                            "explicacion": "«My» significa «mi» y en inglés va antes del sustantivo: «my friend».",
                        },
                    ],
                },
                {
                    "titulo": "Buenos días, buenas noches",
                    "descripcion": "Saludos según la hora del día.",
                    "preguntas": [
                        {
                            "tipo": "seleccion",
                            "instrucciones": "Selecciona la traducción correcta",
                            "texto": "Good morning",
                            "opciones": _op("Buenos días", "Buenas tardes", "Hasta luego", "Gracias"),
                            "explicacion": "«Morning» es la mañana. «Good morning» se dice por la mañana, hasta el mediodía.",
                        },
                        {
                            "tipo": "seleccion",
                            "instrucciones": "Selecciona la traducción correcta",
                            "texto": "Good night",
                            "opciones": _op("Buenas noches", "Buenos días", "Buenas tardes", "Hola"),
                            "explicacion": "«Good night» se dice para despedirse de noche o antes de dormir. Para saludar de noche se usa «Good evening».",
                        },
                        {
                            "tipo": "completar_opcion",
                            "instrucciones": "Completa la frase: «¡Buenos días, Ana!»",
                            "texto": "___ morning, Ana!",
                            "opciones": _op("Good", "Night", "Goodbye", "Please"),
                            "explicacion": "«Good morning» significa «Buenos días»: se forma con «Good» + «morning».",
                        },
                        {
                            "tipo": "traducir_es_en",
                            "instrucciones": "Escribe en inglés",
                            "texto": "Buenos días",
                            "opciones": _aceptadas("Good morning"),
                            "explicacion": "«Buenos días» se dice «Good morning».",
                        },
                        {
                            "tipo": "completar_texto",
                            "instrucciones": "Escribe la palabra que falta: «Buenas noches»",
                            "texto": "Good ______",
                            "opciones": _aceptadas("night"),
                            "explicacion": "«Night» significa «noche»: «Good night» es «Buenas noches».",
                        },
                        {
                            "tipo": "ordenar_palabras",
                            "instrucciones": "Ordena las palabras para formar la frase",
                            "texto": "Buenos días, Ana",
                            "opciones": _fichas("Good", "morning", "Ana"),
                            "explicacion": "En inglés primero va el saludo, «Good morning», y después el nombre.",
                        },
                    ],
                },
            ],
        },
    ],
}



# Unidades 2 a 8 (definidas en a1_unidades.py).
from servidor.contenido.a1_unidades import UNIDADES_2_A_8  # noqa: E402

CURSO_A1["unidades"].extend(UNIDADES_2_A_8)