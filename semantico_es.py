"""Analizador semántico para el subconjunto del español (Fase 2).

Recorre el árbol que construye parser_es.py y verifica la CONCORDANCIA, que la
gramática libre de contexto no expresa (ver docs/gramatica_espanol.bnf):

    C1  Dentro del sintagma nominal: DET, ADJ y N concuerdan en género y número.
    C2  Sujeto y verbo concuerdan en persona y número.
    C3  Sujeto y atributo concuerdan en género y número (verbos ser / estar).
    C4  "al" y "del" van con un sustantivo masculino singular.
    C5  Un verbo intransitivo no lleva objeto directo.

Cumple el mismo papel que semantico.py en la Fase 1: allí la tabla de símbolos
"recordaba" el tipo de cada variable; aquí cada sintagma nominal calcula sus
rasgos (género, número, persona) y los sube por el árbol para compararlos con
el verbo o el atributo, que pueden estar lejos.

Rasgo '*' = forma común ("grande", "estudiante", "mi", "yo"): concuerda con
cualquier género. Cuando una forma común se combina con una que sí lo marca
("la estudiante"), el sintagma toma el género marcado.

Uso:
    python semantico_es.py "Los niños corren ."
    python semantico_es.py ejemplos/oraciones_es.txt
"""
import sys
from pathlib import Path

from lexer_es import ErrorLexico
from parser_es import ErrorSintactico, analizar

GENERO = {"m": "masculino", "f": "femenino", "*": "común"}
NUMERO = {"s": "singular", "p": "plural"}


class ErrorSemantico(Exception):
    pass


def _error(token, mensaje):
    raise ErrorSemantico(f"Línea {token.linea}, columna {token.columna}: {mensaje}")


def _texto(nodo):
    """Las palabras que cubre un nodo, en orden: 'la casa roja'."""
    return " ".join(h.token.valor for h in nodo.hojas())


def _describir(rasgos):
    partes = []
    if "per" in rasgos:
        partes.append(f"{rasgos['per']}.ª persona")
    if "gen" in rasgos:
        partes.append(GENERO[rasgos["gen"]])
    if "num" in rasgos:
        partes.append(NUMERO[rasgos["num"]])
    return " ".join(partes)


def _unir_genero(actual, nuevo):
    """Combina dos géneros. Devuelve el resultado o None si chocan."""
    if actual == "*":
        return nuevo
    if nuevo in ("*", actual):
        return actual
    return None


class AnalizadorSemantico:
    def __init__(self):
        # Lista de verificaciones superadas, para mostrar en la demostración.
        self.informe = []

    # ------------------------------------------------------- C1 y C4 (SN)
    def rasgos_nominal(self, nominal, det=None):
        """Calcula género y número de <nominal> verificando C1 (y C4 si `det`
        es una contracción). Devuelve {'gen', 'num', 'per': 3}."""
        nucleo = next(h for h in nominal.hijos if h.es_hoja() and h.nombre == "N")
        n = nucleo.token.rasgos[0]
        gen, num = n["gen"], n["num"]

        if det is not None:
            d = det.token.rasgos[0]
            nuevo_gen = _unir_genero(gen, d["gen"])
            if d["num"] != num or nuevo_gen is None:
                if det.nombre == "CONTR":
                    _error(det.token, f"'{det.token.valor}' solo va con un sustantivo "
                                      f"masculino singular, pero '{nucleo.token.valor}' es "
                                      f"{_describir(n)} [C4]")
                rasgo = "número" if d["num"] != num else "género"
                _error(det.token, f"el determinante '{det.token.valor}' ({_describir(d)}) "
                                  f"no concuerda en {rasgo} con '{nucleo.token.valor}' "
                                  f"({_describir(n)}) [C1]")
            gen = nuevo_gen

        for sadj in (h for h in nominal.hijos if h.nombre == "sadj"):
            adj = sadj.hijos[-1]
            a = adj.token.rasgos[0]
            nuevo_gen = _unir_genero(gen, a["gen"])
            if a["num"] != num or nuevo_gen is None:
                rasgo = "número" if a["num"] != num else "género"
                _error(adj.token, f"el adjetivo '{adj.token.valor}' ({_describir(a)}) "
                                  f"no concuerda en {rasgo} con '{nucleo.token.valor}' "
                                  f"({_describir({'gen': gen, 'num': num})}) [C1]")
            gen = nuevo_gen

        # Las frases preposicionales dentro del nominal tienen su propio SN.
        for sp in (h for h in nominal.hijos if h.nombre == "sp"):
            self.verificar_sp(sp)

        rasgos = {"gen": gen, "num": num, "per": 3}
        regla = "C1+C4" if det is not None and det.nombre == "CONTR" else "C1"
        texto = (det.token.valor + " " if det is not None else "") + _texto(nominal)
        self.informe.append(f"[{regla}] SN '{texto}': {_describir(rasgos)}")
        return rasgos

    def rasgos_sn(self, sn):
        primero = sn.hijos[0]
        if primero.nombre == "NPROP":
            return dict(primero.token.rasgos[0])
        return self.rasgos_nominal(sn.hijos[1], det=primero)

    def verificar_sp(self, sp):
        enlace, termino = sp.hijos
        if enlace.nombre == "CONTR":
            return self.rasgos_nominal(termino, det=enlace)
        return self.rasgos_sn(termino)

    # ------------------------------------------------------------ oración
    def verificar(self, arbol):
        sujeto = next((h for h in arbol.hijos if h.nombre == "sujeto"), None)
        predicado = next(h for h in arbol.hijos if h.nombre == "predicado")
        sv = predicado.hijos[-1]

        rasgos_sujeto = None
        if sujeto is not None:
            nucleo = sujeto.hijos[0]
            if nucleo.nombre == "PRON":
                rasgos_sujeto = dict(nucleo.token.rasgos[0])
            else:
                rasgos_sujeto = self.rasgos_sn(nucleo)

        verbo = sv.hijos[0]
        self.verificar_sujeto_verbo(sujeto, rasgos_sujeto, verbo)

        for hijo in sv.hijos[1:]:
            if hijo.nombre == "objeto":
                self.verificar_objeto(verbo, hijo)
            elif hijo.nombre == "atributo":
                self.verificar_atributo(sujeto, rasgos_sujeto, hijo)
            elif hijo.nombre == "circunstancial" and hijo.hijos[0].nombre == "sp":
                self.verificar_sp(hijo.hijos[0])
        return self.informe

    # ----------------------------------------------------------------- C2
    def verificar_sujeto_verbo(self, sujeto, rasgos_sujeto, verbo):
        analisis = verbo.token.rasgos
        if rasgos_sujeto is None:
            tiempos = sorted({a["tiempo"] for a in analisis})
            self.informe.append(f"[C2] Sujeto omitido: se deduce de '{verbo.token.valor}' "
                                f"({_describir(analisis[0])}, {'/'.join(tiempos)})")
            return
        validos = [a for a in analisis if a["per"] == rasgos_sujeto["per"]
                   and a["num"] == rasgos_sujeto["num"]]
        if not validos:
            _error(verbo.token, f"el verbo '{verbo.token.valor}' ({_describir(analisis[0])}) "
                                f"no concuerda con el sujeto '{_texto(sujeto)}' "
                                f"({rasgos_sujeto['per']}.ª persona "
                                f"{NUMERO[rasgos_sujeto['num']]}) [C2]")
        tiempos = sorted({a["tiempo"] for a in validos})
        nota = " (ambiguo en tiempo)" if len(tiempos) > 1 else ""
        self.informe.append(f"[C2] Sujeto '{_texto(sujeto)}' y verbo '{verbo.token.valor}': "
                            f"{rasgos_sujeto['per']}.ª persona {NUMERO[rasgos_sujeto['num']]}, "
                            f"{'/'.join(tiempos)}{nota}")

    # ----------------------------------------------------------------- C3
    def verificar_atributo(self, sujeto, rasgos_sujeto, atributo):
        contenido = atributo.hijos[0]
        if contenido.nombre == "sp":                # "está en la casa": sin concordancia
            self.verificar_sp(contenido)
            return
        if contenido.nombre == "sadj":
            adj = contenido.hijos[-1]
            rasgos_attr, token = adj.token.rasgos[0], adj.token
        else:                                       # sintagma nominal
            rasgos_attr = self.rasgos_sn(contenido)
            token = contenido.hojas()[0].token
        if rasgos_sujeto is None:
            return                                  # sujeto omitido: no hay con qué comparar
        if (rasgos_attr["num"] != rasgos_sujeto["num"]
                or _unir_genero(rasgos_sujeto["gen"], rasgos_attr["gen"]) is None):
            rasgo = "número" if rasgos_attr["num"] != rasgos_sujeto["num"] else "género"
            _error(token, f"el atributo '{_texto(contenido)}' "
                          f"({_describir({k: rasgos_attr[k] for k in ('gen', 'num')})}) "
                          f"no concuerda en {rasgo} con el sujeto '{_texto(sujeto)}' "
                          f"({GENERO[rasgos_sujeto['gen']]} {NUMERO[rasgos_sujeto['num']]}) [C3]")
        self.informe.append(f"[C3] Sujeto '{_texto(sujeto)}' y atributo '{_texto(contenido)}': "
                            f"concuerdan a través del verbo copulativo")

    # ----------------------------------------------------------------- C5
    def verificar_objeto(self, verbo, objeto):
        if all(a["trans"] == "i" for a in verbo.token.rasgos):
            _error(objeto.hojas()[0].token,
                   f"'{verbo.token.rasgos[0]['lema']}' es intransitivo y no puede llevar "
                   f"objeto directo ('{_texto(objeto)}') [C5]")
        self.rasgos_sn(objeto.hijos[0])
        self.informe.append(f"[C5] '{verbo.token.rasgos[0]['lema']}' admite objeto directo "
                            f"'{_texto(objeto)}'")


def analizar_oracion(texto):
    """Análisis completo: léxico, sintáctico y semántico.

    Devuelve (arbol, informe). Lanza ErrorLexico, ErrorSintactico o ErrorSemantico.
    """
    arbol = analizar(texto)
    informe = AnalizadorSemantico().verificar(arbol)
    return arbol, informe


def clasificar(texto):
    """Devuelve ('ok' | 'lexico' | 'sintactico' | 'semantico', mensaje)."""
    try:
        analizar_oracion(texto)
        return "ok", "oración válida"
    except ErrorLexico as e:
        return "lexico", f"Error léxico: {e}"
    except ErrorSintactico as e:
        return "sintactico", f"Error sintáctico: {e}"
    except ErrorSemantico as e:
        return "semantico", f"Error semántico: {e}"


def _oraciones_de_entrada(argv):
    if len(argv) > 1:
        ruta = Path(argv[1])
        if ruta.is_file():
            return [l.strip() for l in ruta.read_text(encoding="utf-8").splitlines()
                    if l.strip() and not l.lstrip().startswith("#")]
        return [" ".join(argv[1:])]
    return ["Los perro roja come ."]


if __name__ == "__main__":
    codigo_salida = 0
    for oracion in _oraciones_de_entrada(sys.argv):
        print(f"Oración: {oracion}")
        try:
            _, informe = analizar_oracion(oracion)
        except ErrorLexico as e:
            print(f"  Error léxico: {e}\n")
            codigo_salida = 1
            continue
        except ErrorSintactico as e:
            print(f"  Error sintáctico: {e}\n")
            codigo_salida = 1
            continue
        except ErrorSemantico as e:
            print(f"  Error semántico: {e}\n")
            codigo_salida = 1
            continue
        print("  Análisis semántico correcto. Concordancias verificadas:")
        for linea in informe:
            print(f"    {linea}")
        print()
    sys.exit(codigo_salida)
