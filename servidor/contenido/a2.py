"""Curso A2 de Milingo: 6 unidades, 2 lecciones cada una, 8 preguntas por lección.

Cada lección tiene 3 ejercicios de audio y 5 variados.
  escuchar_elegir   -> la frase en inglés es el texto que suena; las opciones están en español.
  escuchar_escribir -> la frase que suena debe estar entre las respuestas aceptadas.
Para ordenar palabras no se repite ninguna palabra dentro de la misma frase.
"""
from servidor.contenido.ayudas import aceptadas, fichas, op

ELEGIR = "Selecciona la traducción correcta"
EN_INGLES = "Escribe en inglés"
EN_ESPANOL = "Escribe en español"
ORDENAR = "Ordena las palabras para formar la frase"
OIR_ELEGIR = "Escucha y elige lo que significa"
OIR_ESCRIBIR = "Escucha y escribe lo que oyes"


def _p(tipo, instrucciones, texto, opciones, explicacion):
    return {
        "tipo": tipo, "instrucciones": instrucciones, "texto": texto,
        "opciones": opciones, "explicacion": explicacion,
    }


def _oir_elegir(frase, correcta, d1, d2, d3, explicacion):
    return _p("escuchar_elegir", OIR_ELEGIR, frase, op(correcta, d1, d2, d3), explicacion)


def _oir_escribir(frase, explicacion, *otras):
    return _p("escuchar_escribir", OIR_ESCRIBIR, frase, aceptadas(frase, *otras), explicacion)


def _elegir(texto, correcta, d1, d2, d3, explicacion):
    return _p("seleccion", ELEGIR, texto, op(correcta, d1, d2, d3), explicacion)


def _completar(frase_es, texto, correcta, d1, d2, d3, explicacion):
    return _p("completar_opcion", f"Completa la frase: «{frase_es}»", texto,
              op(correcta, d1, d2, d3), explicacion)


def _hueco(frase_es, texto, respuestas, explicacion):
    return _p("completar_texto", f"Escribe la palabra que falta: «{frase_es}»", texto,
              aceptadas(*respuestas), explicacion)


def _a_ingles(frase_es, respuestas, explicacion):
    return _p("traducir_es_en", EN_INGLES, frase_es, aceptadas(*respuestas), explicacion)


def _a_espanol(frase_en, respuestas, explicacion):
    return _p("traducir_en_es", EN_ESPANOL, frase_en, aceptadas(*respuestas), explicacion)


def _ordenar(frase_es, palabras, explicacion):
    return _p("ordenar_palabras", ORDENAR, frase_es, fichas(*palabras), explicacion)


def _leccion(titulo, descripcion, preguntas):
    return {"titulo": titulo, "descripcion": descripcion, "preguntas": preguntas}


CURSO_A2 = {
    "titulo": "Inglés A2",
    "descripcion": "Da el siguiente paso: ciudad, compras, pasado, planes, salud y viajes.",
    "nivel": "A2",
    "orden": 2,
    "unidades": [
        # ---------------------------------------------------------- Unidad 1
        {
            "titulo": "Around Town",
            "descripcion": "Lugares y direcciones",
            "lecciones": [
                _leccion("¿Dónde está?", "Lugares de la ciudad y dónde quedan.", [
                    _oir_elegir(
                        "Where is the bank?", "¿Dónde está el banco?",
                        "¿Dónde está la escuela?", "¿Qué hora es en el banco?",
                        "¿Cómo se llama el banco?",
                        "«Where» significa «dónde». «Where is the bank?» es «¿Dónde está el banco?»."),
                    _elegir(
                        "Library", "Biblioteca", "Librería", "Escuela", "Museo",
                        "«Library» es «biblioteca». «Librería» se dice «bookstore»: es un falso amigo."),
                    _completar(
                        "El banco está al lado del parque", "The bank is ___ the park.",
                        "next to", "of", "with", "from",
                        "«Next to» significa «al lado de»."),
                    _oir_escribir(
                        "The library is near the park",
                        "«Near» significa «cerca de»: «La biblioteca está cerca del parque»."),
                    _a_ingles(
                        "¿Dónde está la farmacia?",
                        ["Where is the pharmacy", "Where's the pharmacy"],
                        "«Pharmacy» es «farmacia». Se pregunta con «Where is...?»."),
                    _oir_elegir(
                        "The supermarket is next to the school",
                        "El supermercado está al lado de la escuela",
                        "El supermercado está frente a la escuela",
                        "El supermercado está lejos de la escuela",
                        "El supermercado está detrás de la escuela",
                        "«Next to» es «al lado de». «In front of» sería «frente a»."),
                    _ordenar(
                        "El museo está cerca de aquí",
                        ["The", "museum", "is", "near", "here"],
                        "«Near here» significa «cerca de aquí»."),
                    _a_espanol(
                        "Where is the museum?",
                        ["Dónde está el museo", "Dónde queda el museo"],
                        "«Where is...?» pregunta por la ubicación de algo."),
                ]),
                _leccion("Cómo llegar", "Pide y da indicaciones.", [
                    _oir_elegir(
                        "Turn left", "Gira a la izquierda", "Gira a la derecha",
                        "Sigue derecho", "Para aquí",
                        "«Turn» es «girar» y «left» es «izquierda»."),
                    _elegir(
                        "Straight ahead", "Todo derecho", "A la izquierda",
                        "Detrás de", "Cerca de",
                        "«Straight ahead» significa «todo derecho»."),
                    _oir_escribir(
                        "Turn right at the bank",
                        "«Right» es «derecha» y «at the bank» es «en el banco»."),
                    _completar(
                        "Gira a la derecha", "Turn ___.",
                        "right", "left", "next", "near",
                        "«Right» significa «derecha»."),
                    _a_ingles(
                        "Sigue derecho",
                        ["Go straight", "Go straight ahead", "Keep going straight",
                         "Continue straight"],
                        "«Go straight» es la forma más común de decir «sigue derecho»."),
                    _oir_elegir(
                        "Go straight and turn left at the school",
                        "Sigue derecho y gira a la izquierda en la escuela",
                        "Gira a la derecha y sigue derecho hasta la escuela",
                        "Sigue derecho hasta la escuela y para",
                        "Gira a la izquierda y luego a la derecha",
                        "Dos indicaciones unidas por «and»: seguir derecho y girar a la izquierda."),
                    _ordenar(
                        "Sigue derecho y gira a la izquierda",
                        ["Go", "straight", "and", "turn", "left"],
                        "Dos órdenes unidas con «and»."),
                    _hueco(
                        "El parque está al final de la calle",
                        "The park is at the ___ of the street.", ["end"],
                        "«End» significa «final»."),
                ]),
            ],
        },
        # ---------------------------------------------------------- Unidad 2
        {
            "titulo": "Shopping",
            "descripcion": "Compras y ropa",
            "lecciones": [
                _leccion("¿Cuánto cuesta?", "Precios y cosas que quieres comprar.", [
                    _oir_elegir(
                        "How much is this shirt?", "¿Cuánto cuesta esta camisa?",
                        "¿De qué color es esta camisa?", "¿Dónde compraste esta camisa?",
                        "¿Esta camisa es tuya?",
                        "«How much» sirve para preguntar el precio."),
                    _elegir(
                        "Cheap", "Barato", "Caro", "Grande", "Pequeño",
                        "«Cheap» es «barato». Lo contrario es «expensive»."),
                    _completar(
                        "¿Cuánto cuesta?", "How ___ is it?",
                        "much", "many", "old", "long",
                        "Para preguntar precios se usa «How much»."),
                    _oir_escribir(
                        "It is too expensive",
                        "«Too expensive» significa «demasiado caro».",
                        "It's too expensive"),
                    _a_ingles(
                        "Es muy barato",
                        ["It is very cheap", "It's very cheap"],
                        "«Very» significa «muy» y va antes del adjetivo."),
                    _oir_elegir(
                        "I want to buy a blue jacket", "Quiero comprar una chaqueta azul",
                        "Quiero vender una chaqueta azul", "Quiero comprar una camisa azul",
                        "Tengo una chaqueta azul",
                        "«Buy» es «comprar» y «jacket» es «chaqueta»."),
                    _ordenar(
                        "¿Cuánto cuestan los zapatos?",
                        ["How", "much", "are", "the", "shoes"],
                        "Con plural se dice «How much are...?»."),
                    _a_espanol(
                        "I like this dress", ["Me gusta este vestido"],
                        "«Dress» es «vestido» y «this» es «este»."),
                ]),
                _leccion("En la tienda de ropa", "Tallas, probarse ropa y pagar.", [
                    _oir_elegir(
                        "Can I try it on?", "¿Puedo probármelo?",
                        "¿Puedo comprarlo?", "¿Puedo devolverlo?",
                        "¿Puedo pagar con tarjeta?",
                        "«Try on» significa «probarse» una prenda."),
                    _elegir(
                        "Size", "Talla", "Precio", "Color", "Tienda",
                        "«Size» es «talla» o «tamaño»."),
                    _completar(
                        "Necesito una talla más grande", "I need a ___ size.",
                        "bigger", "smaller", "cheaper", "newer",
                        "«Bigger» significa «más grande»."),
                    _oir_escribir(
                        "I would like to pay by card",
                        "«Would like» es una forma amable de pedir algo.",
                        "I'd like to pay by card"),
                    _a_ingles(
                        "Quiero pagar en efectivo",
                        ["I want to pay in cash", "I want to pay with cash",
                         "I would like to pay in cash", "I would like to pay with cash",
                         "I'd like to pay in cash", "I'd like to pay with cash"],
                        "«Cash» significa «efectivo»."),
                    _oir_elegir(
                        "The red shoes are on sale", "Los zapatos rojos están en oferta",
                        "Los zapatos rojos están agotados", "Los zapatos rojos son muy caros",
                        "Los zapatos rojos son de mi hermana",
                        "«On sale» significa «en oferta»."),
                    _ordenar(
                        "¿Puedo pagar con tarjeta?",
                        ["Can", "I", "pay", "by", "card"],
                        "«Can I...?» sirve para pedir permiso o preguntar si es posible."),
                    _hueco(
                        "Estos zapatos son muy caros",
                        "These shoes are very ___.", ["expensive"],
                        "«Expensive» significa «caro»."),
                ]),
            ],
        },
        # ---------------------------------------------------------- Unidad 3
        {
            "titulo": "Last Weekend",
            "descripcion": "Habla del pasado",
            "lecciones": [
                _leccion("Ayer", "Cuenta lo que hiciste ayer.", [
                    _oir_elegir(
                        "I went to the cinema yesterday", "Ayer fui al cine",
                        "Mañana voy al cine", "Ayer vi una película en casa",
                        "Hoy voy al cine",
                        "«Went» es el pasado de «go». «Yesterday» significa «ayer»."),
                    _elegir(
                        "Yesterday", "Ayer", "Mañana", "Hoy", "Anoche",
                        "«Yesterday» es «ayer». «Tomorrow» es «mañana»."),
                    _completar(
                        "Ayer fui al parque", "Yesterday I ___ to the park.",
                        "went", "go", "goes", "going",
                        "«Went» es el pasado de «go»."),
                    _oir_escribir(
                        "She played tennis on Saturday",
                        "«Played» es el pasado de «play»: «Ella jugó tenis el sábado»."),
                    _a_ingles(
                        "Ayer estuve en casa",
                        ["Yesterday I was at home", "I was at home yesterday",
                         "Yesterday I was home", "I was home yesterday"],
                        "«Was» es el pasado de «am» con «I»."),
                    _oir_elegir(
                        "We watched a movie last night", "Anoche vimos una película",
                        "Anoche compramos una película", "Mañana veremos una película",
                        "Anoche escuchamos música",
                        "«Watched» es el pasado de «watch» y «last night» es «anoche»."),
                    _ordenar(
                        "Ayer visité a mi madre",
                        ["Yesterday", "I", "visited", "my", "mother"],
                        "Los verbos regulares forman el pasado con «-ed»: «visited»."),
                    _a_espanol(
                        "He was tired",
                        ["Él estaba cansado", "Estaba cansado", "Él estuvo cansado",
                         "Estuvo cansado"],
                        "«Was» es el pasado de «is». «Tired» significa «cansado»."),
                ]),
                _leccion("El fin de semana", "Actividades del fin de semana pasado.", [
                    _oir_elegir(
                        "Last weekend I cooked with my family",
                        "El fin de semana pasado cociné con mi familia",
                        "El próximo fin de semana cocinaré con mi familia",
                        "El fin de semana pasado comí con mi familia",
                        "Cada fin de semana cocino solo",
                        "«Cooked» es el pasado de «cook». «Last weekend» es «el fin de semana pasado»."),
                    _elegir(
                        "Weekend", "Fin de semana", "Entre semana", "Cumpleaños", "Vacaciones",
                        "«Weekend» es sábado y domingo."),
                    _hueco(
                        "Ayer jugué fútbol", "Yesterday I ___ soccer.", ["played"],
                        "El pasado de «play» es «played»."),
                    _oir_escribir(
                        "We ate pizza on Sunday",
                        "«Ate» es el pasado irregular de «eat»: «Comimos pizza el domingo»."),
                    _a_ingles(
                        "Visité a mis abuelos",
                        ["I visited my grandparents", "I went to see my grandparents"],
                        "«Grandparents» significa «abuelos»."),
                    _oir_elegir(
                        "They didn't go to school on Monday",
                        "No fueron a la escuela el lunes",
                        "Fueron a la escuela el lunes",
                        "No van a ir a la escuela el lunes",
                        "No fueron a la escuela el martes",
                        "«Didn't» niega el pasado: «didn't go» es «no fueron»."),
                    _ordenar(
                        "Fuimos a la playa",
                        ["We", "went", "to", "the", "beach"],
                        "«Went to» significa «fue a / fuimos a»."),
                    _completar(
                        "No fui a trabajar", "I ___ go to work.",
                        "didn't", "don't", "won't", "wasn't",
                        "Para negar el pasado se usa «didn't» + el verbo base."),
                ]),
            ],
        },
        # ---------------------------------------------------------- Unidad 4
        {
            "titulo": "Plans and Weather",
            "descripcion": "Planes y clima",
            "lecciones": [
                _leccion("Voy a...", "Habla de tus planes.", [
                    _oir_elegir(
                        "I am going to travel next week", "Voy a viajar la próxima semana",
                        "Viajé la semana pasada", "Viajo todos los días",
                        "Voy a trabajar la próxima semana",
                        "«Am going to» + verbo expresa un plan futuro."),
                    _elegir(
                        "Tomorrow", "Mañana (el día siguiente)", "Ayer", "Hoy", "Anoche",
                        "«Tomorrow» es el día siguiente. «Morning» es la mañana."),
                    _completar(
                        "Voy a estudiar", "I am ___ to study.",
                        "going", "go", "went", "goes",
                        "Para planes se usa «am going to» + verbo."),
                    _oir_escribir(
                        "She is going to visit her friend",
                        "«Is going to visit» es «va a visitar»."),
                    _a_ingles(
                        "Mañana voy a trabajar",
                        ["Tomorrow I am going to work", "I am going to work tomorrow",
                         "Tomorrow I'm going to work", "I'm going to work tomorrow"],
                        "«Tomorrow» puede ir al inicio o al final de la frase."),
                    _oir_elegir(
                        "We are going to eat at home tonight",
                        "Esta noche vamos a comer en casa",
                        "Anoche comimos en casa", "Esta noche vamos a comer afuera",
                        "Mañana comemos en casa",
                        "«Tonight» significa «esta noche»."),
                    _ordenar(
                        "Voy a dormir",
                        ["I", "am", "going", "to", "sleep"],
                        "«I am going to» + verbo es el plan más usado."),
                    _a_espanol(
                        "They are going to play tomorrow",
                        ["Ellos van a jugar mañana", "Van a jugar mañana",
                         "Mañana van a jugar", "Mañana ellos van a jugar"],
                        "«They are going to play» es «van a jugar»."),
                ]),
                _leccion("El clima", "Cómo está el tiempo hoy.", [
                    _oir_elegir(
                        "It is cold and windy today", "Hoy hace frío y viento",
                        "Hoy hace calor y sol", "Hoy llueve mucho",
                        "Ayer hizo frío y viento",
                        "«Cold» es «frío» y «windy» es «con viento»."),
                    _elegir(
                        "Rainy", "Lluvioso", "Soleado", "Nublado", "Nevado",
                        "«Rainy» viene de «rain» (lluvia)."),
                    _completar(
                        "Hoy hace sol", "It is ___ today.",
                        "sunny", "rainy", "windy", "snowy",
                        "«Sunny» viene de «sun» (sol)."),
                    _oir_escribir(
                        "It is going to rain tomorrow",
                        "«Going to rain» es «va a llover»."),
                    _a_ingles(
                        "Hoy hace calor",
                        ["It is hot today", "It's hot today", "Today it is hot",
                         "Today it's hot", "It is hot", "It's hot"],
                        "El clima se dice con «It is...»: «It is hot»."),
                    _oir_elegir(
                        "It was sunny yesterday, but today it is raining",
                        "Ayer hizo sol, pero hoy está lloviendo",
                        "Ayer llovió, pero hoy hace sol",
                        "Ayer hizo sol y hoy también",
                        "Mañana lloverá, pero hoy hace sol",
                        "«Was» es pasado (ayer) e «is raining» es presente (hoy)."),
                    _ordenar(
                        "Hoy hace mucho frío",
                        ["It", "is", "very", "cold", "today"],
                        "«Very cold» significa «muy frío»."),
                    _hueco(
                        "Hoy está nublado", "It is ___ today.", ["cloudy"],
                        "«Cloudy» viene de «cloud» (nube)."),
                ]),
            ],
        },
        # ---------------------------------------------------------- Unidad 5
        {
            "titulo": "Health",
            "descripcion": "Salud y cuerpo",
            "lecciones": [
                _leccion("Me duele...", "Dolores y cómo te sientes.", [
                    _oir_elegir(
                        "I have a headache", "Tengo dolor de cabeza",
                        "Tengo dolor de estómago", "Tengo fiebre", "Tengo tos",
                        "«Headache» es «dolor de cabeza»: «head» (cabeza) + «ache» (dolor)."),
                    _elegir(
                        "Throat", "Garganta", "Cabeza", "Espalda", "Rodilla",
                        "«Throat» significa «garganta»."),
                    _completar(
                        "Me duele la cabeza", "My ___ hurts.",
                        "head", "foot", "hand", "ear",
                        "«Head» es «cabeza». «Hurts» significa «duele»."),
                    _oir_escribir(
                        "I feel very tired",
                        "«Feel» es «sentir(se)» y «tired» es «cansado»."),
                    _a_ingles(
                        "Tengo fiebre",
                        ["I have a fever", "I have a temperature"],
                        "«Fever» significa «fiebre»."),
                    _oir_elegir(
                        "You should drink water and rest",
                        "Deberías beber agua y descansar",
                        "Deberías comer más y trabajar", "Debes ir al trabajo hoy",
                        "Puedes tomar café y salir",
                        "«Should» se usa para dar consejos."),
                    _ordenar(
                        "Necesito ver a un médico",
                        ["I", "need", "to", "see", "a", "doctor"],
                        "«Need to» significa «necesitar»."),
                    _a_espanol(
                        "I have a cold",
                        ["Tengo un resfriado", "Estoy resfriado", "Estoy resfriada",
                         "Tengo catarro", "Tengo gripe"],
                        "«Cold» también es «resfriado», además de «frío»."),
                ]),
                _leccion("En el médico", "Habla con el médico.", [
                    _oir_elegir(
                        "How do you feel today?", "¿Cómo te sientes hoy?",
                        "¿Cuántos años tienes hoy?", "¿Dónde te duele hoy?",
                        "¿Qué comiste hoy?",
                        "«How do you feel?» pregunta cómo te sientes."),
                    _elegir(
                        "Medicine", "Medicamento", "Médico", "Enfermera", "Hospital",
                        "«Medicine» es el medicamento. «Doctor» es el médico."),
                    _completar(
                        "Debes descansar", "You ___ rest.",
                        "should", "can", "did", "are",
                        "«Should» se usa para recomendar: «deberías»."),
                    _oir_escribir(
                        "Take this medicine twice a day",
                        "«Twice a day» significa «dos veces al día»."),
                    _a_ingles(
                        "Me siento mal",
                        ["I feel bad", "I feel sick", "I feel ill", "I do not feel well",
                         "I don't feel well"],
                        "«Feel» + adjetivo describe cómo te sientes."),
                    _oir_elegir(
                        "My throat hurts and I have a cough",
                        "Me duele la garganta y tengo tos",
                        "Me duele la cabeza y tengo fiebre",
                        "Me duele la garganta y tengo hambre",
                        "Me duele la espalda y tengo tos",
                        "«Throat» es «garganta» y «cough» es «tos»."),
                    _ordenar(
                        "Hoy me siento mejor",
                        ["I", "feel", "better", "today"],
                        "«Better» significa «mejor»."),
                    _hueco(
                        "Bebo agua todos los días", "I drink ___ every day.", ["water"],
                        "«Water» significa «agua»."),
                ]),
            ],
        },
        # ---------------------------------------------------------- Unidad 6
        {
            "titulo": "Restaurants and Travel",
            "descripcion": "Restaurantes y viajes",
            "lecciones": [
                _leccion("En el restaurante", "Pide una mesa, comida y la cuenta.", [
                    _oir_elegir(
                        "I would like a table for two", "Quisiera una mesa para dos",
                        "Quisiera dos mesas", "Quisiera la cuenta para dos",
                        "Quisiera una mesa para cuatro",
                        "«I would like» es una forma amable de pedir algo."),
                    _elegir(
                        "Bill", "La cuenta", "El menú", "La propina", "El postre",
                        "En un restaurante, «bill» es «la cuenta»."),
                    _completar(
                        "¿Puedo ver el menú, por favor?", "Can I see the ___, please?",
                        "menu", "bill", "table", "water",
                        "«Menu» es «menú»."),
                    _oir_escribir(
                        "I would like a glass of water, please",
                        "«A glass of water» significa «un vaso de agua».",
                        "I'd like a glass of water, please"),
                    _a_ingles(
                        "La cuenta, por favor",
                        ["The bill, please", "The check, please", "Can I have the bill, please",
                         "Can we have the bill, please"],
                        "«Bill» (o «check») es la cuenta."),
                    _oir_elegir(
                        "I am allergic to nuts", "Soy alérgico a los frutos secos",
                        "Me gustan los frutos secos", "Soy alérgico a la leche",
                        "No tengo hambre",
                        "«Allergic to» significa «alérgico a»."),
                    _ordenar(
                        "¿Me puede dar el menú, por favor?",
                        ["Can", "I", "have", "the", "menu", "please"],
                        "«Can I have...?» es una forma educada de pedir algo."),
                    _a_espanol(
                        "The food is delicious",
                        ["La comida es deliciosa", "La comida está deliciosa",
                         "La comida está rica", "La comida es rica"],
                        "«Delicious» significa «delicioso»."),
                ]),
                _leccion("De viaje", "Transporte, hotel y aeropuerto.", [
                    _oir_elegir(
                        "The train leaves at seven thirty", "El tren sale a las siete y media",
                        "El tren llega a las siete y media", "El tren sale a las siete en punto",
                        "El tren sale a las ocho y media",
                        "«Thirty» es «treinta»: «seven thirty» son las siete y media."),
                    _elegir(
                        "Ticket", "Boleto (billete)", "Maleta", "Pasaporte", "Hotel",
                        "«Ticket» es el boleto o billete para viajar."),
                    _completar(
                        "Reservé una habitación", "I ___ a room.",
                        "booked", "book", "books", "booking",
                        "«Booked» es el pasado de «book» (reservar)."),
                    _oir_escribir(
                        "Where is the airport?",
                        "«Airport» significa «aeropuerto».",
                        "Where's the airport"),
                    _a_ingles(
                        "Necesito mi pasaporte",
                        ["I need my passport"],
                        "«Passport» significa «pasaporte»."),
                    _oir_elegir(
                        "We are going to stay in a hotel near the beach",
                        "Nos vamos a quedar en un hotel cerca de la playa",
                        "Nos quedamos en un hotel lejos de la playa",
                        "Vamos a comer en un hotel cerca de la playa",
                        "Nos quedamos en casa de un amigo cerca de la playa",
                        "«Stay» es «quedarse» y «near the beach» es «cerca de la playa»."),
                    _ordenar(
                        "Mi vuelo sale mañana",
                        ["My", "flight", "leaves", "tomorrow"],
                        "«Flight» significa «vuelo»."),
                    _hueco(
                        "Voy a viajar en avión", "I am going to travel by ___.",
                        ["plane", "airplane"],
                        "«By plane» significa «en avión»."),
                ]),
            ],
        },
    ],
}