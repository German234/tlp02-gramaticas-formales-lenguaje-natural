# Resultados de la comparación

Set de prueba: 76 oraciones (59 gramaticales, 17 agramaticales).

## Aceptación de oraciones

| Sistema | VP | FP | VN | FN | Precisión | Cobertura | Rechazo correcto | Exactitud |
|---|---|---|---|---|---|---|---|---|
| Parser propio (CFG) | 39 | 0 | 17 | 20 | 100.0% | 66.1% | 100.0% | 73.7% |
| spaCy | 51 | 8 | 9 | 8 | 86.4% | 86.4% | 52.9% | 78.9% |
| HuggingFace | 46 | 7 | 10 | 13 | 86.8% | 78.0% | 58.8% | 73.7% |

## Por nivel

| Sistema | N1 cobertura | N1 rechazo | N2 cobertura | N2 rechazo | N3 cobertura | N3 rechazo |
|---|---|---|---|---|---|---|
| Parser propio (CFG) | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% |
| spaCy | 87.5% | 33.3% | 87.0% | 33.3% | 85.0% | 100.0% |
| HuggingFace | 81.2% | 66.7% | 91.3% | 66.7% | 60.0% | 40.0% |

## Etiquetado gramatical (UPOS)

| Sistema | Palabras | Aciertos | Errores | Exactitud | Confusiones más frecuentes |
|---|---|---|---|---|---|
| Parser propio (CFG) | 480 | 472 | 8 | 98.3% | que: PRON→SCONJ, la: PRON→DET, dónde: ADV→PRON, rápido: ADV→ADJ |
| spaCy | 480 | 461 | 19 | 96.0% | perro: NOUN→PROPN, la: PRON→DET, come: VERB→NOUN, está: AUX→VERB |
| HuggingFace | 480 | 457 | 23 | 95.2% | es: AUX→VERB, que: PRON→SCONJ, está: AUX→VERB, al: ADP→DET |

> El etiquetado del parser propio sale de su propio léxico, que es la misma fuente de la que se derivó la referencia (salvo unas pocas correcciones manuales). Su exactitud es alta por construcción y no es comparable con la de spaCy o HuggingFace.

## Adjunción de frases preposicionales

| Sistema | Correctas | Total | Exactitud | SP → sustantivo | SP → verbo |
|---|---|---|---|---|---|
| Parser propio (CFG) | 12 | 20 | 60.0% | 83.3% | 50.0% |
| spaCy | 20 | 20 | 100.0% | 100.0% | 100.0% |

## Costo computacional

| Sistema | Tiempo total | ms por oración |
|---|---|---|
| Parser propio (CFG) | 0.01 s | 0.1 |
| spaCy | 4.63 s | 60.9 |
| HuggingFace | 16.7 s | 219.7 |

Conformidad del parser con su especificación (`resultado_esperado`): 76/76.
