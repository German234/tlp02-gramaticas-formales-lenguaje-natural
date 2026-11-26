"""Experimento LLM: Gemini analiza oraciones siguiendo la gramática formal.

Se le da a Gemini, en el prompt, la gramática libre de contexto (generada de
gramatica_es.py), el vocabulario por categoría (de lexico_es.py) y las reglas
de concordancia C1-C5, y se le pide clasificar cada oración del set con el
mismo veredicto que da nuestro analizador:

    ok          la oración cumple la gramática y la concordancia
    lexico      tiene una palabra que no está en el vocabulario
    sintactico  la secuencia de categorías no la genera la gramática
    semantico   la gramática la genera, pero falla una regla de concordancia

Dos condiciones:
    zero-shot   solo las reglas
    few-shot    las reglas + 10 ejemplos resueltos. Los ejemplos NO están en
                el set de prueba, y su veredicto se comprueba con nuestro
                analizador al iniciar (ver EJEMPLOS_FEW_SHOT).

El veredicto se compara con `resultado_esperado` del set: lo que la gramática
formal dice que debe salir. Así se mide si el LLM aplica las reglas o se
desvía hacia su conocimiento general del español (p. ej. si responde "ok" en
las oraciones del nivel 3, que son español válido pero están fuera de la
gramática).

Salida:
    resultados/predicciones_llm_zero_shot.json   formato común: lo lee metricas.py
    resultados/predicciones_llm_few_shot.json
    resultados/llm_logs/prompt_<modo>.txt        el prompt completo enviado
    resultados/llm_logs/respuestas_<modo>.jsonl  cada respuesta textual de la API
    resultados/logs_llm.md                       resumen legible por oración

La clave se lee de la variable de entorno GEMINI_API_KEY (no se escribe en
el código, para no subirla al repositorio):
    PowerShell:   $env:GEMINI_API_KEY = "su-clave"
    cmd:          set GEMINI_API_KEY=su-clave
    Linux/macOS:  export GEMINI_API_KEY="su-clave"

Uso:
    python api_llm.py                                  # set completo, ambos modos
    python api_llm.py --modo zero-shot
    python api_llm.py --limite 5                       # prueba rápida (no afecta las métricas)
    python api_llm.py --oracion "El perro come ."      # una oración, muestra todo
    python api_llm.py --modelo gemini-3.5-flash-lite
    python api_llm.py --listar-modelos                 # modelos que acepta la clave
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from gramatica_es import GRAMATICA
from lexico_es import LEXICO, VERBOS_REGULARES
from semantico_es import clasificar

RAIZ = Path(__file__).parent
SET_PRUEBA = RAIZ / "datos" / "set_prueba.json"
RESULTADOS = RAIZ / "resultados"
LOGS = RESULTADOS / "llm_logs"

MODELO_POR_DEFECTO = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
URL_API = "https://generativelanguage.googleapis.com/v1beta/models"
VEREDICTOS = ("ok", "lexico", "sintactico", "semantico")
PAUSA_ENTRE_LLAMADAS = 1.0      # segundos; súbanla si aparecen muchos HTTP 429


# =============================================================================
#  Construcción del prompt
# =============================================================================
def gramatica_bnf():
    """La gramática de gramatica_es.py escrita en BNF (una sola fuente)."""
    lineas = []
    ancho = max(len(nt) for nt in GRAMATICA) + 2
    for nt, alternativas in GRAMATICA.items():
        partes = [" ".join(s if s.isupper() else f"<{s}>" for s in alt) or "ε"
                  for alt in alternativas]
        lineas.append(f"{'<' + nt + '>':{ancho + 2}} ::= " + " | ".join(partes))
    return "\n".join(lineas)


CATEGORIAS_GRAMATICA = ["DET", "N", "NPROP", "PRON", "ADJ", "INT", "ADV", "NEG",
                        "V", "VCOP", "PREP", "CONTR", "PUNTO"]
CATEGORIAS_FUERA = ["CONJ", "SUB", "CLIT", "AUX", "PART", "COMP", "INTERR", "SIGNO"]


def vocabulario():
    """Las palabras del léxico agrupadas por categoría."""
    por_cat = {}
    for palabra, analisis in LEXICO.items():
        por_cat.setdefault(analisis[0]["cat"], []).append(palabra)
    lineas = ["Categorías que usa la gramática:"]
    for cat in CATEGORIAS_GRAMATICA:
        lineas.append(f"  {cat}: {', '.join(sorted(por_cat.get(cat, [])))}")
    lineas.append("\nCategorías que están en el vocabulario pero que NINGUNA regla usa "
                  "(una oración que las contenga es 'sintactico', no 'lexico'):")
    for cat in CATEGORIAS_FUERA:
        lineas.append(f"  {cat}: {', '.join(sorted(por_cat.get(cat, [])))}")
    intransitivos = sorted(v for v, t in VERBOS_REGULARES.items() if t == "i")
    lineas.append(f"\nVerbos intransitivos (no admiten objeto directo): "
                  f"{', '.join(intransitivos)}")
    return "\n".join(lineas)


INSTRUCCIONES = """\
Eres un analizador sintáctico formal. Tu única tarea es decidir si una oración
pertenece al lenguaje definido por la gramática y el vocabulario que siguen,
aplicándolos ESTRICTAMENTE. No uses tu conocimiento general del español: una
oración correcta en español pero que estas reglas no generan es 'sintactico'.

Procedimiento:
1. Cada palabra (y el punto) es un token separado por espacios. Si una palabra
   no aparece en el vocabulario -> 'lexico'.
2. Reemplaza cada palabra por su categoría. Si la secuencia de categorías no
   se puede derivar desde <oracion> con la gramática -> 'sintactico'.
3. Si se puede derivar, revisa la concordancia (C1-C5). Si alguna falla
   -> 'semantico'.
4. Si todo se cumple -> 'ok'.

Reglas de concordancia:
  C1  Dentro del sintagma nominal, DET, ADJ y N concuerdan en género y número.
      Las formas comunes ("grande", "estudiante", "mi") van con ambos géneros.
  C2  El sujeto y el verbo concuerdan en persona y número. Un nombre propio o
      un sintagma nominal es 3.ª persona. Si no hay sujeto, no se revisa.
  C3  Con ser/estar, el sujeto y el atributo concuerdan en género y número.
  C4  "al" y "del" solo van con un sustantivo masculino singular.
  C5  Un verbo intransitivo no lleva objeto directo.

Responde ÚNICAMENTE con un objeto JSON, sin texto adicional:
  {"veredicto": "ok" | "lexico" | "sintactico" | "semantico",
   "regla": "C1" | "C2" | "C3" | "C4" | "C5" | null,
   "razon": "explicación breve, máximo 2 líneas"}
"""

# Ejemplos para el few-shot. Ninguno está en el set de prueba (se comprueba al
# iniciar) y su veredicto es el que da nuestro analizador.
EJEMPLOS_FEW_SHOT = [
    ("La niña bebe .", "ok", None,
     "DET(f,s) N(f,s) V(3s). Deriva <sujeto> <predicado> PUNTO y concuerda."),
    ("Mis gatos pequeños corren en el jardín .", "ok", None,
     "SN con adjetivo pospuesto y SP circunstancial; C1 y C2 se cumplen."),
    ("Ellas estudiaron ayer en la casa de Pedro .", "ok", None,
     "PRON(3p) V(3p) ADV SP; el SP 'de Pedro' modifica a 'casa'."),
    ("Las casa es bonita .", "semantico", "C1",
     "'Las' es plural y 'casa' singular."),
    ("Pedro bailaron .", "semantico", "C2",
     "Nombre propio (3s) con verbo en 3.ª plural."),
    ("Luis es bonita .", "semantico", "C3",
     "Sujeto masculino con atributo femenino."),
    ("Sofía camina la escuela .", "semantico", "C5",
     "'caminar' es intransitivo y aquí lleva objeto directo."),
    ("El dinosaurio corre .", "lexico", None,
     "'dinosaurio' no está en el vocabulario."),
    ("Bonito el gato corre .", "sintactico", None,
     "Ninguna regla permite empezar con ADJ seguido de DET."),
    ("Ana y Luis bailan .", "sintactico", None,
     "'y' es CONJ: está en el vocabulario, pero ninguna regla la usa."),
]


def texto_ejemplos():
    bloques = []
    for oracion, veredicto, regla, razon in EJEMPLOS_FEW_SHOT:
        respuesta = json.dumps({"veredicto": veredicto, "regla": regla, "razon": razon},
                               ensure_ascii=False)
        bloques.append(f"Oración: {oracion}\nRespuesta: {respuesta}")
    return "\n\n".join(bloques)


def prompt_base(modo):
    partes = [INSTRUCCIONES,
              "=== GRAMÁTICA (BNF) ===", gramatica_bnf(),
              "=== VOCABULARIO ===", vocabulario()]
    if modo == "few-shot":
        partes += ["=== EJEMPLOS RESUELTOS ===", texto_ejemplos()]
    return "\n\n".join(partes)


def prompt_completo(modo, oracion):
    return f"{prompt_base(modo)}\n\n=== ORACIÓN A ANALIZAR ===\n{oracion}\n"


def comprobar_ejemplos(datos):
    """Los ejemplos no deben estar en el set y deben ser correctos."""
    oraciones_set = {d["oracion"] for d in datos}
    for oracion, veredicto, _, _ in EJEMPLOS_FEW_SHOT:
        if oracion in oraciones_set:
            sys.exit(f"El ejemplo few-shot '{oracion}' está en el set de prueba.")
        obtenido, _ = clasificar(oracion)
        if obtenido != veredicto:
            sys.exit(f"El ejemplo '{oracion}' dice '{veredicto}' pero el analizador "
                     f"da '{obtenido}'.")


# =============================================================================
#  API de Gemini
# =============================================================================
def clave_api():
    clave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not clave:
        sys.exit("Falta la clave. Defina la variable de entorno GEMINI_API_KEY "
                 "(ver el encabezado de api_llm.py).")
    return clave


def pedir(url, clave, cuerpo=None):
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method="POST" if datos else "GET",
                                 headers={"Content-Type": "application/json",
                                          "x-goog-api-key": clave})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def llamar_gemini(prompt, modelo, clave, reintentos=5):
    """Devuelve (texto crudo de la respuesta, error o None)."""
    cuerpo = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 0,
                                   "responseMimeType": "application/json"}}
    espera = 5
    for intento in range(1, reintentos + 1):
        try:
            data = pedir(f"{URL_API}/{modelo}:generateContent", clave, cuerpo)
            partes = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in partes).strip(), None
        except urllib.error.HTTPError as e:
            detalle = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 503) and intento < reintentos:
                print(f"    HTTP {e.code}, reintento {intento} en {espera} s ...")
                time.sleep(espera)
                espera *= 2
                continue
            return "", f"HTTP {e.code}: {detalle}"
        except (KeyError, IndexError):
            return json.dumps(data, ensure_ascii=False)[:500], "respuesta sin texto"
        except Exception as e:
            return "", f"{type(e).__name__}: {e}"
    return "", "sin respuesta"


def interpretar(texto):
    """Extrae {'veredicto', 'regla', 'razon'} del texto de la respuesta."""
    limpio = texto.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    try:
        r = json.loads(limpio)
    except json.JSONDecodeError:
        inicio, fin = limpio.find("{"), limpio.rfind("}")
        try:
            r = json.loads(limpio[inicio:fin + 1])
        except (ValueError, json.JSONDecodeError):
            return {"veredicto": "error", "regla": None, "razon": "no es JSON válido"}
    v = str(r.get("veredicto", "")).strip().lower()
    v = {"léxico": "lexico", "sintáctico": "sintactico", "semántico": "semantico"}.get(v, v)
    if v not in VEREDICTOS:
        return {"veredicto": "error", "regla": None, "razon": f"veredicto no válido: {v!r}"}
    return {"veredicto": v, "regla": r.get("regla"), "razon": r.get("razon", "")}


def listar_modelos(clave):
    data = pedir(URL_API, clave)
    for m in data.get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(m["name"].removeprefix("models/"))


# =============================================================================
#  Experimento
# =============================================================================
def correr_modo(modo, casos, modelo, clave, guardar):
    """Analiza `casos` con un modo. Devuelve la lista de resultados."""
    sistema = "llm_" + modo.replace("-", "_")
    if guardar:
        LOGS.mkdir(parents=True, exist_ok=True)
        (LOGS / f"prompt_{modo}.txt").write_text(
            prompt_completo(modo, "<la oración del set>"), encoding="utf-8")
        log = open(LOGS / f"respuestas_{modo}.jsonl", "w", encoding="utf-8")

    resultados, inicio = [], time.perf_counter()
    for i, caso in enumerate(casos, 1):
        prompt = prompt_completo(modo, caso["oracion"])
        t0 = time.perf_counter()
        crudo, error = llamar_gemini(prompt, modelo, clave)
        ms = round(1000 * (time.perf_counter() - t0))
        r = ({"veredicto": "error", "regla": None, "razon": error} if error
             else interpretar(crudo))
        esperado = caso.get("resultado_esperado")
        marca = "" if esperado is None else ("✓" if r["veredicto"] == esperado else "✗")
        print(f"  [{modo} {i}/{len(casos)}] {marca} {r['veredicto']:10} "
              f"(esperado {esperado})  {caso['oracion']}")
        resultados.append({**caso, **r, "respuesta_cruda": crudo, "ms": ms})
        if guardar:
            log.write(json.dumps({"id": caso.get("id"), "oracion": caso["oracion"],
                                  "modo": modo, "modelo": modelo,
                                  "fecha": datetime.now().isoformat(timespec="seconds"),
                                  "respuesta_cruda": crudo, "error": error,
                                  "veredicto": r["veredicto"], "ms": ms},
                                 ensure_ascii=False) + "\n")
            log.flush()
        time.sleep(PAUSA_ENTRE_LLAMADAS)

    if guardar:
        log.close()
        segundos = round(time.perf_counter() - inicio, 2)
        errores = sum(r["veredicto"] == "error" for r in resultados)
        predicciones = [{
            "id": r["id"],
            "acepta": None if r["veredicto"] == "error" else r["veredicto"] == "ok",
            "veredicto": r["veredicto"], "regla": r["regla"],
            "upos": None, "adjunciones": None,
            "detalle": f"{r['veredicto']}: {r['razon']}",
        } for r in resultados]
        RESULTADOS.mkdir(exist_ok=True)
        (RESULTADOS / f"predicciones_{sistema}.json").write_text(json.dumps({
            "sistema": sistema,
            "info": {"modelo": modelo, "modo": modo, "temperatura": 0,
                     "ejemplos_few_shot": len(EJEMPLOS_FEW_SHOT) if modo == "few-shot" else 0,
                     "errores_api": errores, "segundos": segundos,
                     "ms_por_oracion": round(1000 * segundos / len(casos), 1),
                     "descripcion": f"Gemini {modo} con la gramática en el prompt"},
            "predicciones": predicciones}, ensure_ascii=False, indent=1), encoding="utf-8")
        if errores:
            print(f"  AVISO: {errores} oraciones sin respuesta válida (ver llm_logs).")
    return resultados


def escribir_resumen_md(por_modo, modelo):
    """Resumen legible: una sección por oración con el parser y cada modo."""
    modos = list(por_modo)
    with open(RESULTADOS / "logs_llm.md", "w", encoding="utf-8") as f:
        f.write(f"# Experimento LLM — TLP02-2026\n\nGenerado: "
                f"{datetime.now():%Y-%m-%d %H:%M}  \nModelo: `{modelo}`  \n"
                f"Modos: {', '.join(modos)}  \n"
                f"Prompts completos: `llm_logs/prompt_<modo>.txt`  \n"
                f"Respuestas textuales: `llm_logs/respuestas_<modo>.jsonl`\n")
        for j, caso in enumerate(por_modo[modos[0]]):
            esperado = caso["resultado_esperado"]
            parser, _ = clasificar(caso["oracion"])
            f.write(f"\n## {caso['id']} (nivel {caso['nivel']}): `{caso['oracion']}`\n\n"
                    f"Fenómeno: {caso['fenomeno']}  \n"
                    f"Esperado: `{esperado}` · Parser: `{parser}`\n\n")
            for modo in modos:
                r = por_modo[modo][j]
                marca = "✅" if r["veredicto"] == esperado else "❌"
                f.write(f"- **{modo}** {marca} `{r['veredicto']}`"
                        f"{' (' + r['regla'] + ')' if r.get('regla') else ''}: {r['razon']}\n")


def imprimir_resumen(por_modo):
    print("\n" + "=" * 58)
    for modo, resultados in por_modo.items():
        n = len(resultados)
        ok = sum(r["veredicto"] == r["resultado_esperado"] for r in resultados)
        n3 = [r for r in resultados if r["nivel"] == 3 and r["gramatical"]]
        desvios = sum(r["veredicto"] == "ok" for r in n3)
        print(f"  {modo:10} coincide con la gramática: {ok}/{n} ({100 * ok / n:.1f}%)")
        if n3:
            print(f"  {'':10} nivel 3 válido aceptado como 'ok' (desvío): {desvios}/{len(n3)}")
    print("=" * 58)


def main():
    ap = argparse.ArgumentParser(description="Experimento LLM con la gramática formal")
    ap.add_argument("--oracion", help="analizar una sola oración y mostrar todo")
    ap.add_argument("--limite", type=int, default=0,
                    help="solo las primeras N oraciones (prueba; no guarda predicciones)")
    ap.add_argument("--modo", default="ambos", help="zero-shot, few-shot o ambos")
    ap.add_argument("--modelo", default=MODELO_POR_DEFECTO)
    ap.add_argument("--listar-modelos", action="store_true")
    args = ap.parse_args()
    if args.modo not in ("zero-shot", "few-shot", "ambos"):
        ap.error("--modo debe ser zero-shot, few-shot o ambos")
    modos = ["zero-shot", "few-shot"] if args.modo == "ambos" else [args.modo]

    clave = clave_api()                       # la clave se lee una sola vez
    if args.listar_modelos:
        listar_modelos(clave)
        return

    datos = json.loads(SET_PRUEBA.read_text(encoding="utf-8"))
    comprobar_ejemplos(datos)

    if args.oracion:
        caso = {"oracion": args.oracion}
        for modo in modos:
            r = correr_modo(modo, [caso], args.modelo, clave, guardar=False)[0]
            print(json.dumps({k: r[k] for k in ("veredicto", "regla", "razon",
                                                 "respuesta_cruda", "ms")},
                             ensure_ascii=False, indent=2))
        print(f"Parser propio: {clasificar(args.oracion)}")
        return

    casos = datos[:args.limite] if args.limite else datos
    guardar = not args.limite
    print(f"Modelo: {args.modelo} · {len(casos)} oraciones · modos: {', '.join(modos)}"
          + ("" if guardar else "  (prueba: no se guardan predicciones)"))
    por_modo = {m: correr_modo(m, casos, args.modelo, clave, guardar) for m in modos}
    imprimir_resumen(por_modo)
    if guardar:
        escribir_resumen_md(por_modo, args.modelo)
        print(f"\nResultados en {RESULTADOS}/ (predicciones_llm_*.json, logs_llm.md, "
              f"llm_logs/). Ahora ejecute: python metricas.py")


if __name__ == "__main__":
    main()
