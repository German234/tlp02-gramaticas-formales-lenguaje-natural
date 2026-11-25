"""Experimento LLM: Gemini analiza oraciones siguiendo las reglas de producción
de la CFG formal del proyecto TLP02-2026.

Compara tres enfoques para cada oración del set de prueba:
  1. Parser propio  (semantico_es.clasificar)
  2. Gemini zero-shot  (solo las reglas BNF en el prompt)
  3. Gemini few-shot   (reglas BNF + ejemplos resueltos)

Resultados guardados en:
  resultados/predicciones_llm.json   – detalle por oración
  resultados/logs_llm.md             – prompts y respuestas crudas

Uso:
    python api_llm.py                              # todas las oraciones del set
    python api_llm.py --limite 10                  # solo las primeras 10
    python api_llm.py --oracion "El perro come ."  # una oración directa
    python api_llm.py --modo zero-shot             # solo zero-shot
    python api_llm.py --modo few-shot              # solo few-shot
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

from semantico_es import clasificar

# ---------------------------------------------------------------------------
# 🔑 Pega aquí tu API key de Gemini (Google AI Studio)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = "//ACA VA LA API KEY XD"

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
MODELO = "gemini-2.0-flash"
ARCHIVO_SET = Path("datos/set_prueba.json")
ARCHIVO_PREDICCIONES = Path("resultados/predicciones_llm.json")
ARCHIVO_LOGS = Path("resultados/logs_llm.md")

# ---------------------------------------------------------------------------
# Gramática BNF (se inyecta en el prompt)
# ---------------------------------------------------------------------------
BNF = """\
<oracion>          ::= <sujeto_opcional> <predicado> PUNTO
<sujeto_opcional>  ::= <sujeto> | ε
<sujeto>           ::= <sn> | PRON
<sn>               ::= DET <nominal> | NPROP
<nominal>          ::= <adjetivos> N <adjetivos> <sps_nominales>
<adjetivos>        ::= <sadj> <adjetivos> | ε
<sadj>             ::= <intensificador> ADJ
<intensificador>   ::= INT | ε
<sps_nominales>    ::= <sp> <sps_nominales> | ε
<sp>               ::= PREP <sn> | CONTR <nominal>
<predicado>        ::= <adverbios> <negacion> <sv>
<adverbios>        ::= <sadv> <adverbios> | ε
<sadv>             ::= <intensificador> ADV
<negacion>         ::= NEG | ε
<sv>               ::= V <objeto_opcional> <circunstanciales>
                     | VCOP <atributo> <circunstanciales>
<objeto_opcional>  ::= <sn> | ε
<atributo>         ::= <sadj> | <sn> | <sp>
<circunstanciales> ::= <circunstancial> <circunstanciales> | ε
<circunstancial>   ::= <sp> | <sadv>

Categorías de tokens:
  DET   determinante        (el, la, los, una, mis)
  N     sustantivo común    (perro, manzana, ciudad)
  NPROP nombre propio       (Juan, María)
  PRON  pronombre personal  (yo, tú, ella, nosotros)
  ADJ   adjetivo            (rojo, grande, pequeñas)
  INT   intensificador      (muy, bastante)
  ADV   adverbio            (ayer, siempre, rápidamente)
  NEG   negación            (no)
  V     verbo léxico        (come, caminaron, escribirá)
  VCOP  verbo copulativo    (es, fue, estará)
  PREP  preposición         (a, de, en, con, para)
  CONTR contracción         (al, del)
  PUNTO fin de oración      (.)

Reglas de concordancia (sensibles al contexto, no expresables en CFG):
  C1  DET, ADJ y N concuerdan en género y número dentro del SN.
  C2  El sujeto y el verbo concuerdan en persona y número.
  C3  El sujeto y el atributo concuerdan en género y número (ser/estar).
  C4  "al" y "del" exigen sustantivo masculino singular.
  C5  Un verbo intransitivo no lleva objeto directo.
"""

EJEMPLOS_FEW_SHOT = """\
Oración: "El perro come ."
Veredicto: ok
Razón: DET(masc,sing) + N(masc,sing) concuerdan (C1). V 3.ª sing. concuerda con sujeto sing. (C2). Estructura SVO válida.

Oración: "Los perro come ."
Veredicto: semantico
Razón: DET "los" es plural pero N "perro" es singular: falla C1.

Oración: "Juan caminaron ."
Veredicto: semantico
Razón: NPROP singular, V "caminaron" es 3.ª plural: falla C2.

Oración: "El dinosaurio come ."
Veredicto: lexico
Razón: "dinosaurio" no pertenece al vocabulario de la gramática.

Oración: "Grande el perro ."
Veredicto: sintactico
Razón: La oración comienza con ADJ, que no es inicio válido de <sujeto_opcional> ni de <predicado>.
"""

# ---------------------------------------------------------------------------
# Construcción de prompts
# ---------------------------------------------------------------------------
INSTRUCCION_COMUN = """\
Eres un analizador sintáctico formal. Tu única tarea es aplicar \
estrictamente las reglas de la gramática que se te dan a continuación. \
No uses tu conocimiento general del español; solo la gramática formal.

Responde ÚNICAMENTE con un objeto JSON con dos campos:
  "veredicto": uno de ["ok", "lexico", "sintactico", "semantico"]
  "razon": una explicación breve (máximo 2 líneas)

Definiciones:
  ok         – la oración es válida según la gramática y las reglas de concordancia
  lexico     – contiene una palabra fuera del vocabulario de la gramática
  sintactico – la secuencia de categorías viola la CFG
  semantico  – la CFG la acepta pero falla una regla de concordancia (C1–C5)

No escribas nada fuera del JSON. Sin comillas adicionales, sin markdown.
"""


def prompt_zero_shot(oracion: str) -> str:
    return f"""{INSTRUCCION_COMUN}

=== GRAMÁTICA FORMAL (CFG) ===
{BNF}

=== ORACIÓN A ANALIZAR ===
"{oracion}"
"""


def prompt_few_shot(oracion: str) -> str:
    return f"""{INSTRUCCION_COMUN}

=== GRAMÁTICA FORMAL (CFG) ===
{BNF}

=== EJEMPLOS RESUELTOS ===
{EJEMPLOS_FEW_SHOT}

=== ORACIÓN A ANALIZAR ===
"{oracion}"
"""


# ---------------------------------------------------------------------------
# Llamada a la API de Gemini
# ---------------------------------------------------------------------------
def llamar_gemini(prompt: str) -> dict:
    """Envía el prompt a Gemini y devuelve {'veredicto': ..., 'razon': ...}.

    En caso de error devuelve {'veredicto': 'error', 'razon': <descripción>}.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "pega-tu-key-aqui":
        return {
            "veredicto": "error",
            "razon": "API key de Gemini no configurada. Ver GEMINI_API_KEY en api_llm.py",
        }

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODELO}:generateContent?key={GEMINI_API_KEY}"
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0},
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        texto = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        texto = texto.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(texto)
    except urllib.error.HTTPError as e:
        return {"veredicto": "error", "razon": f"HTTP {e.code}: {e.reason}"}
    except (KeyError, json.JSONDecodeError) as e:
        return {"veredicto": "error", "razon": f"Respuesta inesperada: {e}"}
    except Exception as e:
        return {"veredicto": "error", "razon": str(e)}


# ---------------------------------------------------------------------------
# Análisis de una oración
# ---------------------------------------------------------------------------
def analizar_oracion(oracion: str, modo: str = "ambos") -> dict:
    resultado = {"oracion": oracion}

    # Parser propio
    v_parser, msg_parser = clasificar(oracion)
    resultado["parser"] = {"veredicto": v_parser, "razon": msg_parser}

    # Gemini zero-shot
    if modo in ("zero-shot", "ambos"):
        resultado["zero_shot"] = llamar_gemini(prompt_zero_shot(oracion))
        time.sleep(0.5)

    # Gemini few-shot
    if modo in ("few-shot", "ambos"):
        resultado["few_shot"] = llamar_gemini(prompt_few_shot(oracion))
        time.sleep(0.5)

    return resultado


# ---------------------------------------------------------------------------
# Comparación y aciertos
# ---------------------------------------------------------------------------
def comparar(resultado: dict, esperado: str) -> dict:
    resultado["esperado"] = esperado

    def acierto(enfoque):
        v = resultado.get(enfoque, {}).get("veredicto", "error")
        return v == esperado

    resultado["acierto_parser"] = acierto("parser")
    if "zero_shot" in resultado:
        resultado["acierto_zero_shot"] = acierto("zero_shot")
    if "few_shot" in resultado:
        resultado["acierto_few_shot"] = acierto("few_shot")

    return resultado


# ---------------------------------------------------------------------------
# Escritura de logs Markdown
# ---------------------------------------------------------------------------
def escribir_log(f, i: int, resultado: dict):
    oracion = resultado["oracion"]
    esperado = resultado.get("esperado", "?")

    f.write(f"\n## Caso {i}: `{oracion}`\n\n")
    f.write(f"**Esperado:** `{esperado}`\n\n")

    p = resultado["parser"]
    icono = "✅" if resultado.get("acierto_parser") else "❌"
    f.write(f"### Parser propio {icono}\n")
    f.write(f"- Veredicto: `{p['veredicto']}`\n")
    f.write(f"- Razón: {p['razon']}\n\n")

    if "zero_shot" in resultado:
        z = resultado["zero_shot"]
        icono = "✅" if resultado.get("acierto_zero_shot") else "❌"
        f.write(f"### Gemini zero-shot {icono}\n")
        f.write(f"- Veredicto: `{z.get('veredicto', '?')}`\n")
        f.write(f"- Razón: {z.get('razon', '?')}\n\n")

    if "few_shot" in resultado:
        fs = resultado["few_shot"]
        icono = "✅" if resultado.get("acierto_few_shot") else "❌"
        f.write(f"### Gemini few-shot {icono}\n")
        f.write(f"- Veredicto: `{fs.get('veredicto', '?')}`\n")
        f.write(f"- Razón: {fs.get('razon', '?')}\n\n")

    f.write("---\n")


# ---------------------------------------------------------------------------
# Resumen de métricas
# ---------------------------------------------------------------------------
def imprimir_resumen(resultados: list):
    total = len(resultados)
    if total == 0:
        return

    def tasa(campo):
        n = sum(1 for r in resultados if r.get(campo) is True)
        return n, round(100 * n / total, 1)

    n_p, t_p = tasa("acierto_parser")
    print(f"\n{'='*50}")
    print(f"  RESUMEN  ({total} oraciones)")
    print(f"{'='*50}")
    print(f"  Parser propio    : {n_p}/{total}  ({t_p}%)")

    if any("acierto_zero_shot" in r for r in resultados):
        n_z, t_z = tasa("acierto_zero_shot")
        print(f"  Gemini zero-shot : {n_z}/{total}  ({t_z}%)")

    if any("acierto_few_shot" in r for r in resultados):
        n_f, t_f = tasa("acierto_few_shot")
        print(f"  Gemini few-shot  : {n_f}/{total}  ({t_f}%)")

    print(f"{'='*50}\n")


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Experimento LLM — TLP02-2026")
    ap.add_argument("--oracion", help="Analizar una sola oración entre comillas")
    ap.add_argument("--limite", type=int, default=0,
                    help="Limitar a las primeras N oraciones del set")
    ap.add_argument("--modo", choices=["zero-shot", "few-shot", "ambos"],
                    default="ambos", help="Qué enfoque(s) usar con Gemini")
    args = ap.parse_args()

    Path("resultados").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ---- modo oración única ----
    if args.oracion:
        resultado = analizar_oracion(args.oracion, args.modo)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return

    # ---- modo set completo ----
    casos = json.loads(ARCHIVO_SET.read_text(encoding="utf-8"))
    if args.limite:
        casos = casos[: args.limite]

    resultados = []
    with open(ARCHIVO_LOGS, "w", encoding="utf-8") as log:
        log.write(f"# Logs LLM — TLP02-2026\n\nGenerado: {timestamp}\n")
        log.write(f"Modelo: {MODELO} | Modo: {args.modo} | Oraciones: {len(casos)}\n")

        for i, caso in enumerate(casos, 1):
            oracion = caso["oracion"]
            esperado = caso["resultado_esperado"]
            print(f"[{i}/{len(casos)}] {oracion}")

            resultado = analizar_oracion(oracion, args.modo)
            resultado = comparar(resultado, esperado)
            resultado["id"] = caso.get("id", "")
            resultado["nivel"] = caso.get("nivel", "")
            resultado["fenomeno"] = caso.get("fenomeno", "")

            resultados.append(resultado)
            escribir_log(log, i, resultado)

    ARCHIVO_PREDICCIONES.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    imprimir_resumen(resultados)
    print(f"Predicciones : {ARCHIVO_PREDICCIONES}")
    print(f"Logs         : {ARCHIVO_LOGS}")


if __name__ == "__main__":
    main()