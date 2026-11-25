"""Gramática libre de contexto del subconjunto controlado del español.

Es la misma gramática de docs/gramatica_espanol.bnf, escrita como datos de
Python para poder calcular automáticamente los conjuntos FIRST y FOLLOW y
detectar los conflictos LL(1).

    - No terminales: en minúscula ('oracion', 'sn', ...).
    - Terminales: categorías del léxico en MAYÚSCULA (DET, N, V, ...).
    - Cada alternativa es una lista de símbolos; [] representa ε.

Ejecutar `python gramatica_es.py` imprime FIRST, FOLLOW y los conflictos.
"""

INICIAL = "oracion"

GRAMATICA = {
    "oracion":          [["sujeto_opcional", "predicado", "PUNTO"]],
    "sujeto_opcional":  [["sujeto"], []],
    "sujeto":           [["sn"], ["PRON"]],
    "sn":               [["DET", "nominal"], ["NPROP"]],
    "nominal":          [["adjetivos", "N", "adjetivos", "sps_nominales"]],
    "adjetivos":        [["sadj", "adjetivos"], []],
    "sadj":             [["intensificador", "ADJ"]],
    "intensificador":   [["INT"], []],
    "sps_nominales":    [["sp", "sps_nominales"], []],
    "sp":               [["PREP", "sn"], ["CONTR", "nominal"]],
    "predicado":        [["adverbios", "negacion", "sv"]],
    "adverbios":        [["sadv", "adverbios"], []],
    "sadv":             [["intensificador", "ADV"]],
    "negacion":         [["NEG"], []],
    "sv":               [["V", "objeto_opcional", "circunstanciales"],
                         ["VCOP", "atributo", "circunstanciales"]],
    "objeto_opcional":  [["sn"], []],
    "atributo":         [["sadj"], ["sn"], ["sp"]],
    "circunstanciales": [["circunstancial", "circunstanciales"], []],
    "circunstancial":   [["sp"], ["sadv"]],
}

EPS = "ε"
FIN = "$"


def es_terminal(simbolo):
    return simbolo not in GRAMATICA


def first_de_secuencia(secuencia, first):
    """FIRST de una secuencia de símbolos α = X1 X2 ... Xn."""
    resultado = set()
    for simbolo in secuencia:
        f = {simbolo} if es_terminal(simbolo) else first[simbolo]
        resultado |= f - {EPS}
        if EPS not in f:
            return resultado
    resultado.add(EPS)
    return resultado


def calcular_first():
    first = {nt: set() for nt in GRAMATICA}
    cambio = True
    while cambio:
        cambio = False
        for nt, alternativas in GRAMATICA.items():
            for alt in alternativas:
                nuevo = first_de_secuencia(alt, first)
                if not nuevo <= first[nt]:
                    first[nt] |= nuevo
                    cambio = True
    return first


def calcular_follow(first):
    follow = {nt: set() for nt in GRAMATICA}
    follow[INICIAL].add(FIN)
    cambio = True
    while cambio:
        cambio = False
        for nt, alternativas in GRAMATICA.items():
            for alt in alternativas:
                for i, simbolo in enumerate(alt):
                    if es_terminal(simbolo):
                        continue
                    resto = first_de_secuencia(alt[i + 1:], first)
                    nuevo = resto - {EPS}
                    if EPS in resto:
                        nuevo |= follow[nt]
                    if not nuevo <= follow[simbolo]:
                        follow[simbolo] |= nuevo
                        cambio = True
    return follow


def conflictos_ll1(first, follow):
    """Devuelve [(no_terminal, terminal, [alternativas en conflicto])]."""
    conflictos = []
    for nt, alternativas in GRAMATICA.items():
        tabla = {}
        for alt in alternativas:
            f = first_de_secuencia(alt, first)
            predict = (f - {EPS}) | (follow[nt] if EPS in f else set())
            for t in predict:
                tabla.setdefault(t, []).append(alt)
        for t, alts in sorted(tabla.items()):
            if len(alts) > 1:
                conflictos.append((nt, t, alts))
    return conflictos


def mostrar_alt(alt):
    return " ".join(alt) if alt else EPS


if __name__ == "__main__":
    first = calcular_first()
    follow = calcular_follow(first)
    n_prod = sum(len(a) for a in GRAMATICA.values())
    terminales = sorted({s for alts in GRAMATICA.values() for a in alts
                         for s in a if es_terminal(s)})

    print(f"No terminales: {len(GRAMATICA)}   Producciones: {n_prod}   "
          f"Terminales: {len(terminales)}")
    print("\n%-18s %-38s %s" % ("NO TERMINAL", "FIRST", "FOLLOW"))
    for nt in GRAMATICA:
        print("%-18s %-38s %s" % (nt, " ".join(sorted(first[nt])),
                                   " ".join(sorted(follow[nt]))))

    conflictos = conflictos_ll1(first, follow)
    print(f"\nConflictos LL(1): {len(conflictos)}")
    for nt, t, alts in conflictos:
        print(f"  <{nt}> con '{t}': " + "  |  ".join(mostrar_alt(a) for a in alts))
