"""Batería automática de pruebas del analizador del español (Fase 2).

Cada caso indica el resultado esperado:
    'ok'          la oración es válida
    'lexico'      palabra fuera del vocabulario o carácter inválido
    'sintactico'  la secuencia de categorías no está en la gramática
    'semantico'   la gramática la acepta, pero falla la concordancia (C1-C5)

Uso:
    python pruebas_es.py
"""
from semantico_es import clasificar

CASOS = [
    # ----------------------------------------------------------- válidas
    ("ok", "SVO simple", "María compra una manzana ."),
    ("ok", "Intransitivo con complemento", "Los niños corrieron en el parque ."),
    ("ok", "Futuro con pronombre", "Yo escribiré una carta ."),
    ("ok", "Copulativo con adjetivo", "La casa es muy grande ."),
    ("ok", "Copulativo con SN", "Juan es un profesor inteligente ."),
    ("ok", "Adjetivos antes y después", "La pequeña niña come una manzana roja ."),
    ("ok", "Negación y adverbio", "Mis profesores no trabajaron ayer ."),
    ("ok", "Sujeto omitido", "Comimos el pan de Ana muy rápidamente ."),
    ("ok", "Contracción al + masc. sing.", "Pedro camina al parque ."),
    ("ok", "Contracción del", "El perro del niño corre ."),
    ("ok", "Género común definido por DET", "La estudiante está cansada ."),
    ("ok", "Género común con plural", "Mis estudiantes son felices ."),
    ("ok", "Transitivo sin objeto", "Ana come temprano ."),
    ("ok", "Atributo con SP", "Ellos están en la ciudad ."),
    ("ok", "Tiempo ambiguo (presente/pretérito)", "Nosotros compramos unos libros ."),
    # -------------------------------------------------- errores semánticos
    ("semantico", "C1: DET y N en número", "Los perro come ."),
    ("semantico", "C1: DET y N en género", "La libro es nuevo ."),
    ("semantico", "C1: ADJ y N en género", "El gato blanca corre ."),
    ("semantico", "C1: ADJ y N en número", "Una flor rojas está en la mesa ."),
    ("semantico", "C1: dentro de un SP", "Ana vive en las ciudad ."),
    ("semantico", "C1: género común con DET y ADJ en choque", "La estudiante alto canta ."),
    ("semantico", "C2: sujeto plural, verbo singular", "Los niños corre ."),
    ("semantico", "C2: persona", "Yo come una manzana ."),
    ("semantico", "C2: nombre propio con verbo plural", "Juan caminaron ."),
    ("semantico", "C3: atributo en género", "María es alto ."),
    ("semantico", "C3: atributo en número", "Los gatos son pequeño ."),
    ("semantico", "C3: atributo SN en número", "Juan es unos profesores ."),
    ("semantico", "C4: al + femenino", "Ana camina al escuela ."),
    ("semantico", "C4: del + plural", "El perro del niñas corre ."),
    ("semantico", "C5: intransitivo con objeto", "Pedro camina el parque ."),
    # -------------------------------------------------- errores sintácticos
    ("sintactico", "Sustantivo sin determinante", "Juan come pan ."),
    ("sintactico", "Clítico antes del verbo", "Juan la mira ."),
    ("sintactico", "Sin verbo", "El perro grande ."),
    ("sintactico", "Sin punto final", "El perro come"),
    ("sintactico", "Objeto después de un adverbio", "El perro come ayer el pan ."),
    # ------------------------------------------------------ errores léxicos
    ("sintactico", "Coordinación (y)", "Juan y María comen ."),
    ("sintactico", "Pregunta (¿ ?)", "¿Come Juan ?"),
    ("lexico", "Carácter no válido", "El perro come 5 manzanas ."),
    ("lexico", "Palabra desconocida", "El dinosaurio come ."),
]


def main():
    correctos = 0
    for esperado, descripcion, oracion in CASOS:
        obtenido, mensaje = clasificar(oracion)
        ok = obtenido == esperado
        correctos += ok
        print(f"[{'PASA' if ok else 'FALLA'}] {descripcion}: {oracion}")
        if not ok:
            print(f"        esperado: {esperado}, obtenido: {obtenido}")
        print(f"        -> {mensaje}")
    print(f"\n{correctos}/{len(CASOS)} casos correctos")
    return correctos == len(CASOS)


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
