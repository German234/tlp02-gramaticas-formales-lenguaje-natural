"""Léxico del subconjunto controlado del español (Fase 2, TLP02-2026).

Cada palabra se asocia a una LISTA de análisis posibles. Cada análisis es un
diccionario con la categoría gramatical ('cat') y sus rasgos:

    gen  : 'm' (masculino), 'f' (femenino) o '*' (común a ambos)
    num  : 's' (singular) o 'p' (plural)
    per  : 1, 2 o 3 (persona; en verbos y pronombres)
    tiempo: 'presente', 'preterito' o 'futuro' (solo verbos)
    trans: 't' (transitivo), 'i' (intransitivo) o 'ti' (ambos)  (solo verbos)
    lema : forma base de la palabra

Una palabra puede tener varios análisis. Por ejemplo, 'comemos' es solo
presente, pero 'compramos' puede ser presente o pretérito. Esa ambigüedad
léxica se conserva y la resuelve (o la reporta) el analizador semántico.

Categorías (son los terminales de la gramática, ver gramatica_es.py):
    DET    determinante              el, una, estos, mi
    N      sustantivo común          perro, manzanas
    NPROP  nombre propio             Juan, María
    PRON   pronombre personal sujeto yo, ellas
    ADJ    adjetivo                  rojo, grandes
    INT    intensificador            muy, bastante
    ADV    adverbio                  ayer, rápidamente
    NEG    negación                  no
    V      verbo léxico              come, caminaron
    VCOP   verbo copulativo          es, estaba... (ser / estar)
    PREP   preposición               a, de, con
    CONTR  contracción prep. + art.  al, del
    PUNTO  signo final               .

Ejecutar `python lexico_es.py` muestra un resumen del vocabulario.
"""

LEXICO = {}


def agregar(palabra, cat, **rasgos):
    """Registra un análisis más para `palabra`."""
    LEXICO.setdefault(palabra, []).append({"cat": cat, **rasgos})


# ---------------------------------------------------------------------------
# Determinantes: (forma, género, número)
# ---------------------------------------------------------------------------
for forma, gen, num in [
    ("el", "m", "s"), ("la", "f", "s"), ("los", "m", "p"), ("las", "f", "p"),
    ("un", "m", "s"), ("una", "f", "s"), ("unos", "m", "p"), ("unas", "f", "p"),
    ("este", "m", "s"), ("esta", "f", "s"), ("estos", "m", "p"), ("estas", "f", "p"),
    ("mi", "*", "s"), ("mis", "*", "p"),
]:
    agregar(forma, "DET", gen=gen, num=num, lema=forma)

# Contracciones: preposición + artículo masculino singular
agregar("al", "CONTR", prep="a", gen="m", num="s", lema="a+el")
agregar("del", "CONTR", prep="de", gen="m", num="s", lema="de+el")

# ---------------------------------------------------------------------------
# Sustantivos comunes: (singular, plural, género)
# ---------------------------------------------------------------------------
for sing, plur, gen in [
    ("perro", "perros", "m"), ("gato", "gatos", "m"), ("niño", "niños", "m"),
    ("niña", "niñas", "f"), ("hombre", "hombres", "m"), ("mujer", "mujeres", "f"),
    ("profesor", "profesores", "m"), ("profesora", "profesoras", "f"),
    ("estudiante", "estudiantes", "*"), ("libro", "libros", "m"),
    ("carta", "cartas", "f"), ("manzana", "manzanas", "f"), ("pan", "panes", "m"),
    ("casa", "casas", "f"), ("parque", "parques", "m"), ("escuela", "escuelas", "f"),
    ("ciudad", "ciudades", "f"), ("mesa", "mesas", "f"), ("árbol", "árboles", "m"),
    ("flor", "flores", "f"), ("carro", "carros", "m"), ("telescopio", "telescopios", "m"),
    ("cuchara", "cucharas", "f"), ("jardín", "jardines", "m"), ("ventana", "ventanas", "f"),
]:
    agregar(sing, "N", gen=gen, num="s", lema=sing)
    agregar(plur, "N", gen=gen, num="p", lema=sing)

# ---------------------------------------------------------------------------
# Nombres propios (3.ª persona singular)
# ---------------------------------------------------------------------------
for nombre, gen in [("Juan", "m"), ("Pedro", "m"), ("Luis", "m"),
                    ("María", "f"), ("Ana", "f"), ("Sofía", "f")]:
    agregar(nombre, "NPROP", gen=gen, num="s", per=3, lema=nombre)

# ---------------------------------------------------------------------------
# Pronombres personales de sujeto: (forma, persona, número, género)
# ---------------------------------------------------------------------------
for forma, per, num, gen in [
    ("yo", 1, "s", "*"), ("tú", 2, "s", "*"), ("él", 3, "s", "m"), ("ella", 3, "s", "f"),
    ("usted", 3, "s", "*"), ("nosotros", 1, "p", "m"), ("nosotras", 1, "p", "f"),
    ("ellos", 3, "p", "m"), ("ellas", 3, "p", "f"), ("ustedes", 3, "p", "*"),
]:
    agregar(forma, "PRON", per=per, num=num, gen=gen, lema=forma)

# ---------------------------------------------------------------------------
# Adjetivos
#   - terminados en -o: cuatro formas (rojo, roja, rojos, rojas)
#   - invariables en género: dos formas (grande, grandes)
# ---------------------------------------------------------------------------
for raiz in ["roj", "pequeñ", "alt", "bonit", "nuev", "viej", "cansad", "rápid", "blanc"]:
    lema = raiz + "o"
    agregar(raiz + "o", "ADJ", gen="m", num="s", lema=lema)
    agregar(raiz + "a", "ADJ", gen="f", num="s", lema=lema)
    agregar(raiz + "os", "ADJ", gen="m", num="p", lema=lema)
    agregar(raiz + "as", "ADJ", gen="f", num="p", lema=lema)

for sing, plur in [("grande", "grandes"), ("inteligente", "inteligentes"),
                   ("feliz", "felices"), ("verde", "verdes")]:
    agregar(sing, "ADJ", gen="*", num="s", lema=sing)
    agregar(plur, "ADJ", gen="*", num="p", lema=sing)

# ---------------------------------------------------------------------------
# Intensificadores, adverbios, negación, preposiciones y puntuación
# ---------------------------------------------------------------------------
for forma in ["muy", "bastante"]:
    agregar(forma, "INT", lema=forma)

for forma in ["rápidamente", "lentamente", "hoy", "ayer", "siempre",
              "bien", "mal", "aquí", "allí", "temprano"]:
    agregar(forma, "ADV", lema=forma)

agregar("no", "NEG", lema="no")

for forma in ["a", "de", "en", "con", "por", "para", "sin", "sobre", "hacia"]:
    agregar(forma, "PREP", lema=forma)

agregar(".", "PUNTO", lema=".")

# ---------------------------------------------------------------------------
# Verbos regulares en tres tiempos del indicativo.
# Personas cubiertas: 1s, 2s, 3s, 1p, 3p (se omite "vosotros"; "ustedes" usa 3p).
# ---------------------------------------------------------------------------
PERSONAS = [(1, "s"), (2, "s"), (3, "s"), (1, "p"), (3, "p")]

TERMINACIONES = {
    "ar": {"presente": ["o", "as", "a", "amos", "an"],
           "preterito": ["é", "aste", "ó", "amos", "aron"]},
    "er": {"presente": ["o", "es", "e", "emos", "en"],
           "preterito": ["í", "iste", "ió", "imos", "ieron"]},
    "ir": {"presente": ["o", "es", "e", "imos", "en"],
           "preterito": ["í", "iste", "ió", "imos", "ieron"]},
}
# El futuro se forma sobre el infinitivo completo, igual en las tres conjugaciones.
FUTURO = ["é", "ás", "á", "emos", "án"]

VERBOS_REGULARES = {
    # infinitivo: transitividad
    "comer": "ti", "beber": "ti", "comprar": "t", "mirar": "t", "cocinar": "ti",
    "escribir": "ti", "abrir": "t", "estudiar": "ti", "cantar": "ti",
    "caminar": "i", "correr": "i", "trabajar": "i", "bailar": "i", "vivir": "i",
}

for infinitivo, trans in VERBOS_REGULARES.items():
    raiz, conj = infinitivo[:-2], infinitivo[-2:]
    for tiempo in ("presente", "preterito"):
        for (per, num), term in zip(PERSONAS, TERMINACIONES[conj][tiempo]):
            agregar(raiz + term, "V", per=per, num=num, tiempo=tiempo,
                    trans=trans, lema=infinitivo)
    for (per, num), term in zip(PERSONAS, FUTURO):
        agregar(infinitivo + term, "V", per=per, num=num, tiempo="futuro",
                trans=trans, lema=infinitivo)

# ---------------------------------------------------------------------------
# Verbos copulativos irregulares: ser y estar
# ---------------------------------------------------------------------------
COPULATIVOS = {
    "ser": {"presente": ["soy", "eres", "es", "somos", "son"],
            "preterito": ["fui", "fuiste", "fue", "fuimos", "fueron"],
            "futuro": ["seré", "serás", "será", "seremos", "serán"]},
    "estar": {"presente": ["estoy", "estás", "está", "estamos", "están"],
              "preterito": ["estuve", "estuviste", "estuvo", "estuvimos", "estuvieron"],
              "futuro": ["estaré", "estarás", "estará", "estaremos", "estarán"]},
}
for infinitivo, tiempos in COPULATIVOS.items():
    for tiempo, formas in tiempos.items():
        for (per, num), forma in zip(PERSONAS, formas):
            agregar(forma, "VCOP", per=per, num=num, tiempo=tiempo, lema=infinitivo)


# ---------------------------------------------------------------------------
# Vocabulario FUERA de la gramática (para el nivel 3 del set de prueba)
#
# Estas palabras están en el léxico pero sus categorías no aparecen en ninguna
# producción de la gramática. Así, una oración con coordinación, cláusulas
# relativas, clíticos, tiempos compuestos, voz pasiva o preguntas se rechaza
# con un error SINTÁCTICO, que es lo que se quiere medir, y no con un error
# léxico ("la palabra no está en el vocabulario").
# ---------------------------------------------------------------------------
for forma in ["y", "o", "pero"]:
    agregar(forma, "CONJ", lema=forma)                 # coordinación

for forma in ["que", "porque", "cuando"]:
    agregar(forma, "SUB", lema=forma)                  # subordinación / relativo

for forma in ["lo", "le", "les", "se", "nos"]:
    agregar(forma, "CLIT", lema=forma)                 # pronombres clíticos

for forma, per, num in [("he", 1, "s"), ("has", 2, "s"), ("ha", 3, "s"),
                        ("hemos", 1, "p"), ("han", 3, "p")]:
    agregar(forma, "AUX", per=per, num=num, lema="haber")   # tiempos compuestos

for forma in ["comido", "comprado", "cocinado", "mirado", "estudiado", "cantado",
              "escrito", "escrita", "abierto", "abierta"]:
    agregar(forma, "PART", lema=forma)                 # participios

agregar("más", "COMP", lema="más")                     # comparativo
for forma in ["qué", "dónde"]:
    agregar(forma, "INTERR", lema=forma)               # interrogativos
for forma in ["¿", "?", "¡", "!", ","]:
    agregar(forma, "SIGNO", lema=forma)                # otros signos


def buscar(palabra):
    """Devuelve la lista de análisis de `palabra`, o [] si no está en el léxico.

    Primero busca la forma exacta (para nombres propios con mayúscula) y luego
    en minúsculas (para la palabra que inicia la oración).
    """
    return LEXICO.get(palabra) or LEXICO.get(palabra.lower(), [])


if __name__ == "__main__":
    from collections import Counter

    por_categoria = Counter()
    for analisis in LEXICO.values():
        for cat in {a["cat"] for a in analisis}:
            por_categoria[cat] += 1
    ambiguas = {p: a for p, a in LEXICO.items() if len(a) > 1}

    print(f"Formas distintas en el léxico: {len(LEXICO)}")
    for cat, n in sorted(por_categoria.items()):
        print(f"  {cat:6} {n}")
    print(f"\nFormas con más de un análisis: {len(ambiguas)}")
    for palabra in sorted(ambiguas)[:10]:
        descr = [f"{a['cat']}:{a.get('tiempo', '')}{a.get('per', '')}{a.get('num', '')}"
                 for a in ambiguas[palabra]]
        print(f"  {palabra:12} {', '.join(descr)}")
