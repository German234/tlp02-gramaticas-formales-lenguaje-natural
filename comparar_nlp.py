"""Procesa el set de prueba con el parser propio y con herramientas de NLP.

Sistemas:
    parser   Nuestro analizador (lexer_es + parser_es + semantico_es).
    spacy    spaCy (es_core_news_md por defecto): etiquetas UPOS, árbol de
             dependencias y rasgos morfológicos. Para decidir si acepta una
             oración se revisa la concordancia sobre SU análisis (ver
             concordancia_ud): spaCy no juzga gramaticalidad por sí solo.
    hf       HuggingFace Transformers, dos modelos:
               - etiquetado UPOS:  PlanTL-GOB-ES/roberta-base-bne-capitel-pos
               - aceptabilidad:    pseudo-log-verosimilitud (PLL) de un modelo
                 de lenguaje enmascarado (PlanTL-GOB-ES/roberta-base-bne). Se
                 enmascara cada subpalabra, se mide qué tan probable la
                 considera el modelo y se promedia. El umbral entre "acepta" y
                 "rechaza" se elige con validación cruzada dejando uno fuera
                 (cada oración se clasifica con el umbral aprendido de las
                 otras 75), para no ajustar el umbral con la misma oración.

Cada sistema guarda sus predicciones en resultados/predicciones_<sistema>.json.
Después, `python metricas.py` calcula las métricas y las gráficas.

Instalación (una sola vez):
    pip install spacy transformers torch matplotlib
    python -m spacy download es_core_news_md

Uso:
    python comparar_nlp.py                       # los tres sistemas
    python comparar_nlp.py parser spacy          # solo algunos
    python comparar_nlp.py spacy --modelo-spacy es_core_news_lg
"""
import argparse
import json
import math
import time
from pathlib import Path

RAIZ = Path(__file__).parent
SET_PRUEBA = RAIZ / "datos" / "set_prueba.json"
RESULTADOS = RAIZ / "resultados"

UPOS_VALIDAS = {"ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM",
                "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB", "X"}

# Categorías de nuestra gramática -> UPOS (misma tabla que docs/SET_PRUEBA.md)
CATEGORIA_A_UPOS = {"DET": "DET", "N": "NOUN", "NPROP": "PROPN", "PRON": "PRON",
                    "ADJ": "ADJ", "INT": "ADV", "ADV": "ADV", "NEG": "ADV",
                    "V": "VERB", "VCOP": "AUX", "PREP": "ADP", "CONTR": "ADP",
                    "PUNTO": "PUNCT", "CONJ": "CCONJ", "SUB": "SCONJ", "CLIT": "PRON",
                    "AUX": "AUX", "PART": "VERB", "COMP": "ADV", "INTERR": "PRON",
                    "SIGNO": "PUNCT"}


def cargar_set():
    return json.loads(SET_PRUEBA.read_text(encoding="utf-8"))


def guardar(sistema, predicciones, info):
    RESULTADOS.mkdir(exist_ok=True)
    archivo = RESULTADOS / f"predicciones_{sistema}.json"
    archivo.write_text(json.dumps({"sistema": sistema, "info": info,
                                   "predicciones": predicciones},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  -> {archivo}")


# =============================================================================
#  1. Parser propio
# =============================================================================
def correr_parser(datos):
    from lexer_es import ErrorLexico, tokenizar
    from parser_es import ErrorSintactico, analizar
    from semantico_es import ErrorSemantico, AnalizadorSemantico

    predicciones = []
    for d in datos:
        p = {"id": d["id"], "acepta": None, "upos": None, "adjunciones": {}, "detalle": ""}
        try:
            p["upos"] = [CATEGORIA_A_UPOS[t.tipo] for t in tokenizar(d["oracion"])[:-1]]
        except ErrorLexico as e:
            p["detalle"] = f"Error léxico: {e}"
        try:
            arbol = analizar(d["oracion"])
            AnalizadorSemantico().verificar(arbol)
            p["acepta"] = True
            p["detalle"] = "aceptada"
            p["adjunciones"] = adjunciones_del_arbol(arbol)
        except ErrorLexico as e:
            p["acepta"], p["detalle"] = False, f"Error léxico: {e}"
        except ErrorSintactico as e:
            p["acepta"], p["detalle"] = False, f"Error sintáctico: {e}"
        except ErrorSemantico as e:
            p["acepta"], p["detalle"] = False, f"Error semántico: {e}"
            # La sintaxis sí se analizó: las adjunciones del árbol son válidas.
            p["adjunciones"] = adjunciones_del_arbol(analizar(d["oracion"]))
        predicciones.append(p)
    return predicciones, {"descripcion": "CFG + parser descendente recursivo + concordancia"}


def adjunciones_del_arbol(arbol):
    """{índice de la preposición: índice de la palabra que modifica}.

    Si el SP está dentro de un <nominal>, modifica al sustantivo (N) de ese
    nominal. Si es <circunstancial> o <atributo>, modifica al verbo del <sv>.
    """
    hojas = arbol.hojas()
    indice = {id(h): i for i, h in enumerate(hojas)}
    resultado = {}

    def recorrer(nodo, padre, verbo):
        if nodo.es_hoja():
            return
        if nodo.nombre == "sv":
            verbo = nodo.hijos[0]
        if nodo.nombre == "sp":
            prep = nodo.hijos[0]
            if padre.nombre == "nominal":
                nucleo = next(h for h in padre.hijos if h.es_hoja() and h.nombre == "N")
            else:
                nucleo = verbo
            if nucleo is not None:
                resultado[str(indice[id(prep)])] = indice[id(nucleo)]
        for hijo in nodo.hijos:
            recorrer(hijo, nodo, verbo)

    recorrer(arbol, None, None)
    return resultado


# =============================================================================
#  2. spaCy
# =============================================================================
def concordancia_ud(tokens):
    """Revisa la concordancia sobre un análisis de dependencias Universal.

    `tokens`: lista de dicts {i, texto, upos, head, dep, morph}, donde morph
    es un dict como {'Gender': 'Fem', 'Number': 'Sing', 'Person': '3'}.
    Devuelve la lista de violaciones (vacía = la oración se acepta).

    Reglas equivalentes a C1-C3 de nuestro analizador:
      - det / amod: el determinante o adjetivo concuerda con su sustantivo
        en Gender y Number.
      - nsubj: el sujeto concuerda con el verbo finito en Number y Person.
        Si el núcleo no es finito (copulativas, pasivas, tiempos compuestos),
        se busca el hijo cop/aux finito. Un sujeto coordinado cuenta como plural.
      - en copulativas, el sujeto concuerda con el atributo adjetival o
        nominal en Gender y Number.
    """
    violaciones = []
    hijos = {t["i"]: [] for t in tokens}
    for t in tokens:
        if t["head"] != t["i"]:
            hijos[t["head"]].append(t)
    por_i = {t["i"]: t for t in tokens}

    def choca(a, b, rasgo):
        va, vb = a["morph"].get(rasgo), b["morph"].get(rasgo)
        return va is not None and vb is not None and va != vb

    for t in tokens:
        cabeza = por_i[t["head"]]
        dep = t["dep"].split(":")[0]

        if dep in ("det", "amod") and cabeza["upos"] in ("NOUN", "PROPN"):
            for rasgo in ("Gender", "Number"):
                if choca(t, cabeza, rasgo):
                    violaciones.append(f"{dep}: '{t['texto']}' y '{cabeza['texto']}' "
                                       f"difieren en {rasgo}")

        if dep == "nsubj":
            sujeto = dict(t["morph"])
            if t["upos"] in ("NOUN", "PROPN"):
                sujeto.setdefault("Person", "3")
            if any(h["dep"] == "conj" for h in hijos[t["i"]]):
                sujeto["Number"] = "Plur"
            suj = {"morph": sujeto}

            finito = cabeza if cabeza["morph"].get("VerbForm") == "Fin" else next(
                (h for h in hijos[cabeza["i"]] if h["dep"].split(":")[0] in ("cop", "aux")
                 and h["morph"].get("VerbForm") == "Fin"), None)
            if finito is not None:
                for rasgo in ("Number", "Person"):
                    if choca(suj, finito, rasgo):
                        violaciones.append(f"nsubj: '{t['texto']}' y '{finito['texto']}' "
                                           f"difieren en {rasgo}")

            es_copulativa = any(h["dep"] == "cop" for h in hijos[cabeza["i"]])
            if es_copulativa and cabeza["upos"] in ("ADJ", "NOUN"):
                for rasgo in ("Gender", "Number"):
                    if choca(suj, cabeza, rasgo):
                        violaciones.append(f"atributo: '{t['texto']}' y '{cabeza['texto']}' "
                                           f"difieren en {rasgo}")
    return violaciones


def correr_spacy(datos, modelo):
    import spacy
    from spacy.tokens import Doc

    nlp = spacy.load(modelo)
    # Se usan las mismas palabras del set (separadas por espacios) para que
    # las etiquetas queden alineadas con la referencia.
    nlp.tokenizer = lambda texto: Doc(nlp.vocab, words=texto.split())

    predicciones = []
    for d in datos:
        doc = nlp(d["oracion"])
        tokens = [{"i": t.i, "texto": t.text, "upos": t.pos_, "head": t.head.i,
                   "dep": t.dep_, "morph": t.morph.to_dict()} for t in doc]
        violaciones = concordancia_ud(tokens)

        adjunciones = {}
        for adj in d["adjunciones"]:
            prep = doc[adj["sp_indice"]]
            # En UD la preposición depende del sustantivo del SP (relación
            # 'case'); ese sustantivo depende de la palabra que el SP modifica.
            termino = prep.head if prep.dep_ == "case" else prep
            adjunciones[str(adj["sp_indice"])] = termino.head.i

        predicciones.append({
            "id": d["id"], "acepta": not violaciones,
            "upos": [t.pos_ for t in doc], "adjunciones": adjunciones,
            "detalle": "; ".join(violaciones) or "sin problemas de concordancia",
            "dependencias": [f"{t.text}/{t.dep_}->{t.head.text}" for t in doc],
        })
    return predicciones, {"modelo": modelo, "spacy": spacy.__version__,
                          "descripcion": "spaCy + reglas de concordancia sobre su análisis"}


# =============================================================================
#  3. HuggingFace Transformers
# =============================================================================
MODELO_POS = "PlanTL-GOB-ES/roberta-base-bne-capitel-pos"
MODELO_LM = "PlanTL-GOB-ES/roberta-base-bne"


def normalizar_etiqueta(etiqueta, desconocidas):
    """Lleva la etiqueta del modelo a UPOS ('B-NOUN' -> 'NOUN')."""
    e = etiqueta.upper().split("-")[-1]
    e = {"CONJ": "CCONJ", "PROPNOUN": "PROPN"}.get(e, e)
    if e not in UPOS_VALIDAS:
        desconocidas.add(etiqueta)
    return e


def etiquetar_hf(datos):
    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(MODELO_POS, add_prefix_space=True)
    modelo = AutoModelForTokenClassification.from_pretrained(MODELO_POS).eval()
    desconocidas = set()
    resultado = []
    for d in datos:
        palabras = d["oracion"].split()
        enc = tok(palabras, is_split_into_words=True, return_tensors="pt")
        with torch.no_grad():
            ids = modelo(**enc).logits[0].argmax(-1).tolist()
        etiquetas, vistos = [None] * len(palabras), set()
        for pos, w in enumerate(enc.word_ids()):
            if w is not None and w not in vistos:      # primera subpalabra
                vistos.add(w)
                etiquetas[w] = normalizar_etiqueta(modelo.config.id2label[ids[pos]],
                                                   desconocidas)
        resultado.append(etiquetas)
    return resultado, sorted(desconocidas)


def pll_hf(datos):
    """Pseudo-log-verosimilitud promedio por subpalabra de cada oración."""
    import torch
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(MODELO_LM)
    modelo = AutoModelForMaskedLM.from_pretrained(MODELO_LM).eval()
    puntajes = []
    for d in datos:
        ids = tok(d["oracion"], return_tensors="pt")["input_ids"][0]
        posiciones = list(range(1, len(ids) - 1))              # sin <s> ni </s>
        lote = ids.repeat(len(posiciones), 1)
        for fila, pos in enumerate(posiciones):
            lote[fila, pos] = tok.mask_token_id
        with torch.no_grad():
            logp = torch.log_softmax(modelo(input_ids=lote).logits, dim=-1)
        total = sum(logp[fila, pos, ids[pos]].item() for fila, pos in enumerate(posiciones))
        puntajes.append(total / len(posiciones))
    return puntajes


def umbral_optimo(puntajes, etiquetas):
    """Umbral que maximiza la exactitud: acepta si puntaje >= umbral."""
    candidatos = sorted(set(puntajes))
    candidatos = [candidatos[0] - 1] + [(a + b) / 2 for a, b in zip(candidatos, candidatos[1:])] \
                 + [candidatos[-1] + 1]
    mejor, mejor_exactitud = candidatos[0], -1
    for u in candidatos:
        exactitud = sum((p >= u) == e for p, e in zip(puntajes, etiquetas))
        if exactitud > mejor_exactitud:
            mejor, mejor_exactitud = u, exactitud
    return mejor


def umbral_dejando_uno_fuera(puntajes, etiquetas):
    """Para cada oración, el umbral aprendido con todas las demás."""
    return [umbral_optimo(puntajes[:i] + puntajes[i + 1:], etiquetas[:i] + etiquetas[i + 1:])
            for i in range(len(puntajes))]


def correr_hf(datos):
    import transformers

    print("  etiquetado UPOS ...")
    etiquetas_upos, desconocidas = etiquetar_hf(datos)
    if desconocidas:
        print(f"  AVISO: etiquetas que no son UPOS: {desconocidas}")
    print("  pseudo-log-verosimilitud ...")
    puntajes = pll_hf(datos)
    gold = [d["gramatical"] for d in datos]
    umbrales = umbral_dejando_uno_fuera(puntajes, gold)

    predicciones = [{
        "id": d["id"], "acepta": p >= u, "upos": up, "adjunciones": None,
        "detalle": f"PLL={p:.3f} (umbral {u:.3f})", "pll": p,
    } for d, p, u, up in zip(datos, puntajes, umbrales, etiquetas_upos)]
    return predicciones, {"modelo_pos": MODELO_POS, "modelo_lm": MODELO_LM,
                          "transformers": transformers.__version__,
                          "umbral_global": umbral_optimo(puntajes, gold),
                          "etiquetas_no_upos": desconocidas,
                          "descripcion": "RoBERTa-BNE: POS + aceptabilidad por PLL"}


# =============================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    # Sin `choices`: con nargs="*" y una lista por defecto, algunas versiones de
    # argparse validan la lista completa como si fuera una sola opción.
    validos = ["parser", "spacy", "hf"]
    ap.add_argument("sistemas", nargs="*", help="parser, spacy y/o hf (por defecto, los tres)")
    ap.add_argument("--modelo-spacy", default="es_core_news_md")
    args = ap.parse_args()
    args.sistemas = args.sistemas or validos
    invalidos = [s for s in args.sistemas if s not in validos]
    if invalidos:
        ap.error(f"sistema no válido: {', '.join(invalidos)} (opciones: {', '.join(validos)})")

    datos = cargar_set()
    print(f"Set de prueba: {len(datos)} oraciones")
    for sistema in args.sistemas:
        print(f"\n[{sistema}]")
        inicio = time.perf_counter()
        try:
            if sistema == "parser":
                pred, info = correr_parser(datos)
            elif sistema == "spacy":
                pred, info = correr_spacy(datos, args.modelo_spacy)
            else:
                pred, info = correr_hf(datos)
        except ImportError as e:
            print(f"  No se pudo ejecutar ({e}). Revise la instalación en el encabezado.")
            continue
        except OSError as e:
            print(f"  No se pudo cargar el modelo ({e}).")
            continue
        info["segundos"] = round(time.perf_counter() - inicio, 2)
        info["ms_por_oracion"] = round(1000 * info["segundos"] / len(datos), 1)
        print(f"  {info['segundos']} s ({info['ms_por_oracion']} ms por oración)")
        guardar(sistema, pred, info)
    print("\nAhora ejecute: python metricas.py")


if __name__ == "__main__":
    main()
