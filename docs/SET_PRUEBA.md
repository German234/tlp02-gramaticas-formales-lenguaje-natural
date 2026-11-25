# Set de prueba — Fase 2

Archivos: `datos/set_prueba.json` (lo leen los scripts) y `datos/set_prueba.csv` (se abre en Excel).

**76 oraciones** repartidas en tres niveles de complejidad:

| Nivel | Descripción | Gramaticales | Agramaticales | Total |
|---|---|---|---|---|
| 1 | Oraciones simples (SVO, copulativas, un solo tiempo) | 16 | 6 | 22 |
| 2 | Modificadores y variaciones (adjetivos, adverbios, SP, negación, sujeto omitido) | 23 | 6 | 29 |
| 3 | Fenómenos que exceden la gramática (coordinación, relativas, clíticos, pasiva, preguntas...) | 20 | 5 | 25 |
| **Total** | | **59** | **17** | **76** |

Por diseño, las 20 oraciones gramaticales del nivel 3 son **gramaticales en español, pero están fuera de nuestra CFG**. Son los falsos negativos esperados del parser y el lugar donde se espera que spaCy y el LLM lo superen.

## Campos de cada oración

| Campo | Significado |
|---|---|
| `id` | Identificador `N<nivel>-<número>` |
| `nivel` | 1, 2 o 3 |
| `oracion` | Las palabras van separadas por espacios, incluso el punto y los signos (`¿ Come Juan ?`), para que todas las herramientas tokenicen igual |
| `gramatical` | **Etiqueta de referencia (gold):** ¿es una oración correcta del español? La decide el grupo, no el parser |
| `resultado_esperado` | Lo que **debe** devolver nuestro analizador según su especificación: `ok`, `sintactico` (fuera de la gramática) o `semantico` (falla la concordancia C1–C5) |
| `fenomeno` | El fenómeno lingüístico que se prueba |
| `upos` | Etiqueta gramatical de referencia de cada palabra, en el estándar **Universal Dependencies (UPOS)**, el mismo que usan spaCy y Stanza |
| `adjunciones` | Para las frases preposicionales con una lectura clara: la preposición y la palabra que modifica (el núcleo). Se usa para medir el problema de la adjunción |

`gramatical` y `resultado_esperado` son dos cosas distintas:
- `gramatical` es la **verdad lingüística** y es contra la que se calculan precisión y recall de todos los sistemas;
- `resultado_esperado` es la **especificación** de nuestro parser y sirve para comprobar que el código hace lo que la gramática dice (todas coinciden con la salida actual del parser).

## Equivalencia de categorías con UPOS

| Nuestra categoría | UPOS | | Nuestra categoría | UPOS |
|---|---|---|---|---|
| DET | DET | | VCOP (ser/estar) | AUX |
| N | NOUN | | PREP, CONTR (al/del) | ADP |
| NPROP | PROPN | | PUNTO, SIGNO | PUNCT |
| PRON, CLIT | PRON | | CONJ (y, o, pero) | CCONJ |
| ADJ | ADJ | | SUB (porque, cuando) | SCONJ |
| ADV, INT, NEG, COMP | ADV | | AUX (haber) | AUX |
| V, PART | VERB | | | |

Correcciones manuales sobre esa tabla (la categoría depende del uso en la oración):
- *que* relativo → PRON (N3-53, 64, 72, 75); *que* comparativo → SCONJ (N3-65);
- *la* clítica → PRON (N3-55, 71); *rápido* usado como adverbio → ADV (N3-70); *dónde* → ADV.

## Adjunciones de referencia

Hay 20 frases preposicionales con núcleo de referencia. Algunas se unen a un **sustantivo** (*"la ventana **de la casa**"*) y otras al **verbo** (*"come el pan **con la cuchara**"*). Nuestro parser une siempre la frase al sustantivo más cercano (regla codiciosa), así que se espera que falle en las que van con el verbo después de un objeto: N2-29, N2-30, N2-36 y N2-40.

N2-25 (*"Juan mira al hombre con el telescopio"*) es genuinamente ambigua: tiene dos lecturas válidas y por eso **no** tiene adjunción de referencia.

## Métricas que se calcularán

La clase positiva es "oración gramatical" (`gramatical = si`). Un sistema predice positivo cuando acepta la oración.

| Métrica | Fórmula |
|---|---|
| Precisión | VP / (VP + FP): de las oraciones que aceptó, cuántas eran correctas |
| Cobertura (recall) | VP / (VP + FN): de las oraciones correctas, cuántas aceptó |
| Tasa de rechazo correcto | VN / (VN + FP): de las agramaticales, cuántas rechazó |
| Falsos positivos | Aceptó una oración agramatical |
| Falsos negativos | Rechazó una oración gramatical |
| Errores de etiquetado | Palabras cuya categoría UPOS no coincide con la de referencia |
| Precisión de adjunción | Frases preposicionales unidas al núcleo correcto |
