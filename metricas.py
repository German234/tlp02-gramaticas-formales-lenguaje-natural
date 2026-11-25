"""Calcula métricas, tablas y gráficas a partir de resultados/predicciones_*.json.

Lee todas las predicciones que existan (parser, spacy, hf y, más adelante,
las del LLM) y genera:

    resultados/metricas.md      tablas en Markdown, listas para el informe
    resultados/metricas.json    los mismos números, para otros scripts
    resultados/errores.csv      cada falso positivo / falso negativo, con su causa
    resultados/graficas/*.png   gráficas comparativas

Definiciones (clase positiva = oración gramatical; ver docs/SET_PRUEBA.md):
    precisión          VP / (VP + FP)
    cobertura (recall) VP / (VP + FN)
    rechazo correcto   VN / (VN + FP)
    exactitud          (VP + VN) / total
    etiquetado         palabras con UPOS igual a la referencia / palabras
    adjunción          SP unidos al núcleo correcto / SP con referencia

Uso:
    python metricas.py
"""
import csv
import json
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).parent
RESULTADOS = RAIZ / "resultados"
GRAFICAS = RESULTADOS / "graficas"
ORDEN = ["parser", "spacy", "hf"]
NOMBRES = {"parser": "Parser propio (CFG)", "spacy": "spaCy", "hf": "HuggingFace"}


def nombre(sistema):
    return NOMBRES.get(sistema, sistema.replace("llm_", "LLM ").replace("_", " "))


def division(a, b):
    return a / b if b else float("nan")


def pct(x):
    return "—" if x != x else f"{100 * x:.1f}%"


def cargar():
    datos = json.loads((RAIZ / "datos" / "set_prueba.json").read_text(encoding="utf-8"))
    sistemas = {}
    for archivo in sorted(RESULTADOS.glob("predicciones_*.json")):
        contenido = json.loads(archivo.read_text(encoding="utf-8"))
        sistemas[contenido["sistema"]] = contenido
    orden = [s for s in ORDEN if s in sistemas] + sorted(s for s in sistemas if s not in ORDEN)
    return datos, {s: sistemas[s] for s in orden}


# ------------------------------------------------------------------ métricas
def metricas_aceptacion(datos, pred):
    c = Counter()
    for d in datos:
        p = pred.get(d["id"], {})
        acepta = bool(p.get("acepta"))
        if p.get("acepta") is None:
            c["sin_respuesta"] += 1
        c[("VP" if acepta else "FN") if d["gramatical"] else ("FP" if acepta else "VN")] += 1
    vp, fp, vn, fn = c["VP"], c["FP"], c["VN"], c["FN"]
    return {"VP": vp, "FP": fp, "VN": vn, "FN": fn, "sin_respuesta": c["sin_respuesta"],
            "precision": division(vp, vp + fp), "recall": division(vp, vp + fn),
            "rechazo_correcto": division(vn, vn + fp),
            "exactitud": division(vp + vn, len(datos))}


def metricas_etiquetado(datos, pred):
    aciertos = total = 0
    confusiones = Counter()
    for d in datos:
        upos = pred.get(d["id"], {}).get("upos")
        if not upos:
            continue
        for palabra, ref, sis in zip(d["oracion"].split(), d["upos"], upos):
            total += 1
            if ref == sis:
                aciertos += 1
            else:
                confusiones[(ref, sis, palabra.lower())] += 1
    return {"aciertos": aciertos, "total": total, "errores": total - aciertos,
            "exactitud": division(aciertos, total),
            "confusiones": [{"referencia": r, "sistema": s, "palabra": w, "veces": n}
                            for (r, s, w), n in confusiones.most_common()]}


def metricas_adjuncion(datos, pred):
    correctas = total = respondidas = 0
    por_tipo = Counter()
    for d in datos:
        adj_pred = pred.get(d["id"], {}).get("adjunciones")
        upos = d["upos"]
        for a in d["adjunciones"]:
            tipo = "verbo" if upos[a["nucleo_indice"]] in ("VERB", "AUX") else "sustantivo"
            total += 1
            por_tipo[(tipo, "total")] += 1
            if adj_pred is None or str(a["sp_indice"]) not in adj_pred:
                continue
            respondidas += 1
            if adj_pred[str(a["sp_indice"])] == a["nucleo_indice"]:
                correctas += 1
                por_tipo[(tipo, "ok")] += 1
    if all((p.get("adjunciones") is None) for p in pred.values()):
        return None
    return {"correctas": correctas, "total": total, "respondidas": respondidas,
            "exactitud": division(correctas, total),
            "a_sustantivo": division(por_tipo[("sustantivo", "ok")], por_tipo[("sustantivo", "total")]),
            "a_verbo": division(por_tipo[("verbo", "ok")], por_tipo[("verbo", "total")])}


def por_nivel(datos, pred):
    resultado = {}
    for nivel in (1, 2, 3):
        sub = [d for d in datos if d["nivel"] == nivel]
        resultado[nivel] = metricas_aceptacion(sub, pred)
    return resultado


# ----------------------------------------------------------------- gráficas
def graficas(tabla, sistemas):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    GRAFICAS.mkdir(parents=True, exist_ok=True)
    nombres = [nombre(s) for s in sistemas]
    colores = ["#4c72b0", "#dd8452", "#55a868", "#c44e52", "#8172b3", "#937860"]

    def barras_agrupadas(grupos, series, titulo, archivo, ylabel="%"):
        fig, ax = plt.subplots(figsize=(max(7, 1.6 * len(grupos) * len(series) / 2), 4.5))
        ancho = 0.8 / len(series)
        for k, (etiqueta, valores) in enumerate(series):
            xs = [i + (k - (len(series) - 1) / 2) * ancho for i in range(len(grupos))]
            v = [100 * x if x == x else 0 for x in valores]
            barras = ax.bar(xs, v, ancho, label=etiqueta, color=colores[k % len(colores)])
            for b, x in zip(barras, valores):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1,
                        "—" if x != x else f"{100 * x:.0f}", ha="center", fontsize=8)
        ax.set_xticks(range(len(grupos)))
        ax.set_xticklabels(grupos)
        ax.set_ylim(0, 110)
        ax.set_ylabel(ylabel)
        ax.set_title(titulo)
        ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=min(len(series), 4), frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(GRAFICAS / archivo, dpi=150)
        plt.close(fig)

    metricas = ["precision", "recall", "rechazo_correcto", "exactitud"]
    barras_agrupadas(["Precisión", "Cobertura", "Rechazo correcto", "Exactitud"],
                     [(nombre(s), [tabla[s]["aceptacion"][m] for m in metricas]) for s in sistemas],
                     "Aceptación de oraciones por sistema", "aceptacion.png")

    barras_agrupadas(["Nivel 1", "Nivel 2", "Nivel 3"],
                     [(nombre(s), [tabla[s]["por_nivel"][n]["recall"] for n in (1, 2, 3)])
                      for s in sistemas],
                     "Cobertura (oraciones gramaticales aceptadas) por nivel",
                     "cobertura_por_nivel.png")

    con_pos = [s for s in sistemas if tabla[s]["etiquetado"]["total"]]
    if con_pos:
        barras_agrupadas(["Exactitud UPOS"],
                         [(nombre(s), [tabla[s]["etiquetado"]["exactitud"]]) for s in con_pos],
                         "Etiquetado gramatical (UPOS)", "etiquetado.png")

    con_adj = [s for s in sistemas if tabla[s]["adjuncion"]]
    if con_adj:
        barras_agrupadas(["Total", "SP → sustantivo", "SP → verbo"],
                         [(nombre(s), [tabla[s]["adjuncion"][k] for k in
                                       ("exactitud", "a_sustantivo", "a_verbo")]) for s in con_adj],
                         "Adjunción de frases preposicionales", "adjuncion.png")

    # Tipos de error por sistema (barras apiladas)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    fp = [tabla[s]["aceptacion"]["FP"] for s in sistemas]
    fn = [tabla[s]["aceptacion"]["FN"] for s in sistemas]
    et = [tabla[s]["etiquetado"]["errores"] for s in sistemas]
    ax.bar(nombres, fp, label="Falsos positivos", color="#c44e52")
    ax.bar(nombres, fn, bottom=fp, label="Falsos negativos", color="#dd8452")
    ax.bar(nombres, et, bottom=[a + b for a, b in zip(fp, fn)],
           label="Errores de etiquetado (palabras)", color="#8172b3")
    ax.set_ylabel("Cantidad")
    ax.set_title("Clasificación de errores")
    ax.legend(fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=15)
    fig.tight_layout()
    fig.savefig(GRAFICAS / "tipos_de_error.png", dpi=150)
    plt.close(fig)


# ------------------------------------------------------------------ informe
def markdown(datos, tabla, sistemas, info):
    L = [f"# Resultados de la comparación\n",
         f"Set de prueba: {len(datos)} oraciones "
         f"({sum(d['gramatical'] for d in datos)} gramaticales, "
         f"{sum(not d['gramatical'] for d in datos)} agramaticales).\n",
         "## Aceptación de oraciones\n",
         "| Sistema | VP | FP | VN | FN | Precisión | Cobertura | Rechazo correcto | Exactitud |",
         "|---|---|---|---|---|---|---|---|---|"]
    for s in sistemas:
        a = tabla[s]["aceptacion"]
        L.append(f"| {nombre(s)} | {a['VP']} | {a['FP']} | {a['VN']} | {a['FN']} | "
                 f"{pct(a['precision'])} | {pct(a['recall'])} | "
                 f"{pct(a['rechazo_correcto'])} | {pct(a['exactitud'])} |")

    L += ["\n## Por nivel\n", "| Sistema | " + " | ".join(
        f"N{n} cobertura | N{n} rechazo" for n in (1, 2, 3)) + " |",
          "|---|" + "---|" * 6]
    for s in sistemas:
        pn = tabla[s]["por_nivel"]
        L.append(f"| {nombre(s)} | " + " | ".join(
            f"{pct(pn[n]['recall'])} | {pct(pn[n]['rechazo_correcto'])}" for n in (1, 2, 3)) + " |")

    L += ["\n## Etiquetado gramatical (UPOS)\n",
          "| Sistema | Palabras | Aciertos | Errores | Exactitud | Confusiones más frecuentes |",
          "|---|---|---|---|---|---|"]
    for s in sistemas:
        e = tabla[s]["etiquetado"]
        if not e["total"]:
            continue
        conf = ", ".join(f"{c['palabra']}: {c['referencia']}→{c['sistema']}"
                         for c in e["confusiones"][:4])
        L.append(f"| {nombre(s)} | {e['total']} | {e['aciertos']} | {e['errores']} | "
                 f"{pct(e['exactitud'])} | {conf} |")
    if "parser" in sistemas:
        L.append("\n> El etiquetado del parser propio sale de su propio léxico, que es "
                 "la misma fuente de la que se derivó la referencia (salvo unas pocas correcciones "
                 "manuales). Su exactitud es alta por construcción y no es comparable "
                 "con la de spaCy o HuggingFace.")

    con_adj = [s for s in sistemas if tabla[s]["adjuncion"]]
    if con_adj:
        L += ["\n## Adjunción de frases preposicionales\n",
              "| Sistema | Correctas | Total | Exactitud | SP → sustantivo | SP → verbo |",
              "|---|---|---|---|---|---|"]
        for s in con_adj:
            a = tabla[s]["adjuncion"]
            L.append(f"| {nombre(s)} | {a['correctas']} | {a['total']} | {pct(a['exactitud'])} | "
                     f"{pct(a['a_sustantivo'])} | {pct(a['a_verbo'])} |")

    L += ["\n## Costo computacional\n", "| Sistema | Tiempo total | ms por oración |",
          "|---|---|---|"]
    for s in sistemas:
        i = info[s]
        L.append(f"| {nombre(s)} | {i.get('segundos', '—')} s | {i.get('ms_por_oracion', '—')} |")

    if "parser" in sistemas:
        pred = tabla["parser"]["pred"]
        coinciden = sum(1 for d in datos if _resultado_parser(pred[d["id"]]) == d["resultado_esperado"])
        L.append(f"\nConformidad del parser con su especificación (`resultado_esperado`): "
                 f"{coinciden}/{len(datos)}.")
    return "\n".join(L) + "\n"


def _resultado_parser(p):
    if p.get("acepta"):
        return "ok"
    detalle = p.get("detalle", "")
    for clave, valor in (("léxico", "lexico"), ("sintáctico", "sintactico"), ("semántico", "semantico")):
        if clave in detalle:
            return valor
    return "?"


def main():
    datos, sistemas = cargar()
    if not sistemas:
        print("No hay predicciones. Ejecute primero: python comparar_nlp.py")
        return
    tabla, info = {}, {}
    for s, contenido in sistemas.items():
        pred = {p["id"]: p for p in contenido["predicciones"]}
        info[s] = contenido.get("info", {})
        tabla[s] = {"pred": pred,
                    "aceptacion": metricas_aceptacion(datos, pred),
                    "por_nivel": por_nivel(datos, pred),
                    "etiquetado": metricas_etiquetado(datos, pred),
                    "adjuncion": metricas_adjuncion(datos, pred)}

    orden = list(sistemas)
    texto = markdown(datos, tabla, orden, info)
    (RESULTADOS / "metricas.md").write_text(texto, encoding="utf-8")
    (RESULTADOS / "metricas.json").write_text(json.dumps(
        {s: {k: v for k, v in t.items() if k != "pred"} for s, t in tabla.items()},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    with open(RESULTADOS / "errores.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sistema", "id", "nivel", "tipo", "oracion", "fenomeno", "detalle"])
        for s in orden:
            for d in datos:
                p = tabla[s]["pred"].get(d["id"], {})
                acepta = bool(p.get("acepta"))
                if acepta and not d["gramatical"]:
                    tipo = "falso positivo"
                elif not acepta and d["gramatical"]:
                    tipo = "falso negativo"
                else:
                    continue
                w.writerow([s, d["id"], d["nivel"], tipo, d["oracion"], d["fenomeno"],
                            p.get("detalle", "")])

    try:
        graficas(tabla, orden)
    except ImportError:
        print("matplotlib no está instalado: no se generaron gráficas.")
    print(texto)
    print(f"Archivos en {RESULTADOS}/ (metricas.md, metricas.json, errores.csv, graficas/)")


if __name__ == "__main__":
    main()
