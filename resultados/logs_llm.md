# Experimento LLM — TLP02-2026

Generado: 2026-11-26 15:35  
Modelo: `gemini-3.5-flash-lite`  
Modos: zero-shot, few-shot  
Prompts completos: `llm_logs/prompt_<modo>.txt`  
Respuestas textuales: `llm_logs/respuestas_<modo>.jsonl`

## N1-01 (nivel 1): `El perro come .`

Fenómeno: SV intransitivo/transitivo sin objeto  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y las reglas de concordancia.
- **few-shot** ✅ `ok`: DET(m,s) N(m,s) V(3s). Deriva <sujeto> <predicado> PUNTO y concuerda perfectamente.

## N1-02 (nivel 1): `María compra una manzana .`

Fenómeno: SVO  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple estrictamente con la gramática, el vocabulario y las reglas de concordancia.
- **few-shot** ✅ `ok`: María es NPROP(3s), compra es V(3s), una manzana es objeto directo femenino singular. Todo concuerda.

## N1-03 (nivel 1): `Los niños corren .`

Fenómeno: SV plural  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `semantico` (C5): El verbo 'corren' es intransitivo y no debe llevar objeto directo, aunque aquí no lleva ninguno, es correcto, pero la regla C5 no se viola. Espera, el análisis es correcto: 'corren' no lleva objeto. Revisemos: sujeto 'Los niños' (3ª plural), verbo 'corren' (3ª plural). Todo concuerda. Veredicto: ok.
- **few-shot** ✅ `ok`: DET(m,p) N(m,p) V(3p). Deriva <sujeto> <predicado> PUNTO y concuerda perfectamente.

## N1-04 (nivel 1): `Yo escribiré una carta .`

Fenómeno: SVO, pronombre, futuro  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: PRON(1s) V(1s) DET(f,s) N(f,s) PUNTO. Sujeto y verbo concuerdan en 1.ª persona singular y cumple todas las reglas.

## N1-05 (nivel 1): `La casa es grande .`

Fenómeno: Copulativa con adjetivo  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `sintactico`: La palabra 'La' no está en el vocabulario (debe ser minúscula 'la').
- **few-shot** ✅ `ok`: DET(f,s) N(f,s) VCOP ADJ. Concuerdan en género y número (C1, C3) y sujeto y verbo (C2).

## N1-06 (nivel 1): `Ana canta .`

Fenómeno: SV con nombre propio  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y las reglas de concordancia.
- **few-shot** ✅ `ok`: NPROP(3s) V(3s). Deriva <sujeto> <predicado> PUNTO y cumple la concordancia de persona y número.

## N1-07 (nivel 1): `Nosotros estudiamos .`

Fenómeno: Pronombre plural, tiempo ambiguo  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y las reglas de concordancia.
- **few-shot** ✅ `ok`: PRON(1p) V(1p) PUNTO. Deriva <sujeto> <predicado> PUNTO y concuerda en persona y número.

## N1-08 (nivel 1): `El gato mira el árbol .`

Fenómeno: SVO  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y las reglas de concordancia.
- **few-shot** ✅ `ok`: DET(m,s) N(m,s) V(3s) DET(m,s) N(m,s). Deriva correctamente y cumple C1 y C2.

## N1-09 (nivel 1): `Tú vives aquí .`

Fenómeno: 2.ª persona, adverbio  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: PRON(2s) V(2s) ADV PUNTO; cumple con la derivación y la concordancia C2.

## N1-10 (nivel 1): `Las niñas bailaron .`

Fenómeno: Pretérito plural  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `semantico` (C5): El verbo 'bailaron' es intransitivo y no lleva objeto directo, aunque en este caso tampoco lo tiene, la regla se evalúa. Espera, el análisis es correcto, la oración no tiene objeto. Ah, pero la oración es 'Las niñas bailaron .' Sujeto (Las niñas) y verbo intransitivo (bailaron). No hay objeto directo. Por tanto, cumple C5. Revisemos el sujeto 'Las niñas' (3ra plural) y verbo 'bailaron' (3ra plural) -> C2 ok. DET 'Las' y N 'niñas' (femenino plural) -> C1 ok.
- **few-shot** ❌ `semantico` (C5): 'bailar' es un verbo intransitivo y no puede llevar objeto directo, pero la estructura no lo lleva; sin embargo, cumple con C1 y C2.

## N1-11 (nivel 1): `Pedro es inteligente .`

Fenómeno: Copulativa, adjetivo de género común  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: NPROP(3s) VCOP(3s) ADJ. C3 se cumple pues el sujeto singular y el atributo coinciden.

## N1-12 (nivel 1): `Mi profesora trabaja .`

Fenómeno: Determinante posesivo  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `semantico` (C5): El verbo trabaja es intransitivo y no debe llevar objeto directo, pero aquí no hay objeto directo, cumple correctamente con la transitividad ya que el sujeto y verbo concuerdan y no hay objeto.
- **few-shot** ✅ `ok`: DET N V; 'profesora' y 'trabaja' concuerdan en 3.ª persona singular (C2).

## N1-13 (nivel 1): `Ellos abrirán la ventana .`

Fenómeno: SVO, futuro  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración es gramaticalmente correcta, cumple con la concordancia de sujeto y verbo, así como dentro del sintagma nominal.
- **few-shot** ✅ `ok`: PRON(3p) V(3p) DET(f,s) N(f,s). El sujeto y el verbo concuerdan en persona y número (C2), y el DET y N en género y número (C1).

## N1-14 (nivel 1): `Luis está cansado .`

Fenómeno: Copulativa con estar  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia (C1-C5).
- **few-shot** ✅ `ok`: NPROP con VCOP y atributo adjetival; C3 se cumple en género y número.

## N1-15 (nivel 1): `Un hombre caminó .`

Fenómeno: Pretérito singular  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: DET(m,s) N(m,s) V(3s). Deriva <sujeto> <predicado> PUNTO y concuerda perfectamente.

## N1-16 (nivel 1): `Usted cocina el pan .`

Fenómeno: Pronombre usted, SVO  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la sintaxis, el vocabulario y las reglas de concordancia (C1-C5).
- **few-shot** ❌ `semantico` (C2): 'usted' es de 2.ª persona (o requiere tratamiento especial) y el verbo 'cocina' concuerda en 3.ª persona, fallando la concordancia estricta.

## N1-17 (nivel 1): `Los perro come .`

Fenómeno: C1: DET-N en número  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C1): El determinante 'Los' (masculino plural) no concuerda en número con el sustantivo 'perro' (masculino singular).
- **few-shot** ✅ `semantico` (C1): 'Los' es plural y 'perro' es singular.

## N1-18 (nivel 1): `El niños corre .`

Fenómeno: C1: DET-N en número  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C1): El determinante (El) y el sustantivo (niños) no concuerdan en número (singular vs plural).
- **few-shot** ✅ `semantico` (C1): 'El' es singular y 'niños' es plural.

## N1-19 (nivel 1): `María es alto .`

Fenómeno: C3: atributo en género  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C3): El atributo 'alto' no concuerda en género femenino con el sujeto 'María'.
- **few-shot** ✅ `semantico` (C3): Sujeto femenino (María) con atributo masculino (alto).

## N1-20 (nivel 1): `Yo come una manzana .`

Fenómeno: C2: persona  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C2): El sujeto 'Yo' (1.ª persona singular) no concuerda con el verbo 'come' (3.ª persona singular).
- **few-shot** ✅ `semantico` (C2): 'Yo' es 1.ª persona singular y 'come' es 3.ª persona singular.

## N1-21 (nivel 1): `Perro el come .`

Fenómeno: Orden de palabras  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La secuencia DET N no se genera correctamente por la estructura esperada del sujeto o la gramática no valida 'Perro el' como <sn>.
- **few-shot** ✅ `sintactico`: Ninguna regla permite comenzar con un sustantivo sin determinante seguido de un determinante.

## N1-22 (nivel 1): `Las flores es bonitas .`

Fenómeno: C2: número  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C3): El sujeto 'Las flores' (fem. pl.) y el atributo 'bonitas' (fem. pl.) concuerdan, pero el verbo 'es' es de 3ª sing. y el sujeto es plural.
- **few-shot** ✅ `semantico` (C2): 'Las flores' es plural (3p) y el verbo 'es' es singular (3s); además falla C3 con el atributo.

## N2-23 (nivel 2): `La pequeña niña come una manzana roja .`

Fenómeno: Adjetivos antes y después  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `sintactico`: La palabra 'La' no está en el vocabulario (debe ser minúscula 'la').
- **few-shot** ✅ `ok`: DET ADJ N V DET N ADJ PUNTO. Todos los componentes derivan correctamente y cumplen C1, C2 y C5.

## N2-24 (nivel 2): `Mis profesores no trabajaron ayer .`

Fenómeno: Negación y adverbio  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: DET N NEG V ADV PUNTO. Cumple C1, C2 y C5 (trabajar es intransitivo y no lleva OD).

## N2-25 (nivel 2): `Juan mira al hombre con el telescopio .`

Fenómeno: Adjunción ambigua (dos lecturas válidas)  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `sintactico`: El uso de la contracción 'al' con un nombre propio en el sintagma nominal no genera la estructura esperada por la gramática en este contexto.
- **few-shot** ✅ `ok`: NPROP(3s) V(3s) CONTR N con SP válido; C1, C2, C4 se cumplen correctamente.

## N2-26 (nivel 2): `Ana estará muy cansada hoy .`

Fenómeno: Intensificador, futuro de estar  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración es gramaticalmente correcta y cumple con todas las reglas de concordancia.
- **few-shot** ✅ `ok`: Ana(NPROP:3s) VCOP(estará:3s) INT(muy) ADJ(cansada:f,s) ADV(hoy). C3 se cumple (sujeto y atributo femenino singular).

## N2-27 (nivel 2): `Comimos el pan de Ana muy rápidamente .`

Fenómeno: Sujeto omitido, SP nominal, adverbio intensificado  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `semantico` (C5): El verbo 'comimos' es transitivo y requiere un objeto directo, pero aquí no se detecta la violación de intransitividad o bien se usa correctamente.
- **few-shot** ✅ `ok`: Sujeto tácito (nosotros), verbo transitivo 'comimos', SN objeto directo 'el pan', SP posesivo y adverbio circunstancial.

## N2-28 (nivel 2): `El perro muy grande corre muy lentamente .`

Fenómeno: Conflicto INT (LL(2))  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: DET(m,s) N(m,s) INT ADJ(m,s) V(3s) INT ADV. La estructura y concordancias se cumplen.

## N2-29 (nivel 2): `Ana come el pan con la cuchara .`

Fenómeno: SP instrumental (adjunción al verbo)  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: NPROP come DET N PREP DET N PUNTO. Deriva correctamente y cumple todas las concordancias.

## N2-30 (nivel 2): `Pedro escribió una carta en la mesa .`

Fenómeno: SP de lugar (adjunción al verbo)  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: Pedro(NPROP, 3s) escribió(V, 3s) una carta(SN, f,s) en la mesa(SP); sujeto y verbo concuerdan.

## N2-31 (nivel 2): `Los niños del parque cantaron bien .`

Fenómeno: Contracción en el sujeto  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `sintactico`: La gramática no permite CONTR (<nominal>) dentro de <sn> ni <sp> según la regla <sp>, generando un error sintáctico.
- **few-shot** ✅ `ok`: DET N CONTR N V ADV PUNTO. Todas las palabras derivan correctamente y cumplen la concordancia.

## N2-32 (nivel 2): `La niña abrió la ventana de la casa .`

Fenómeno: SP nominal en el objeto  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `sintactico`: La palabra 'La' empieza con mayúscula en el texto pero en el vocabulario está registrada como minúscula 'la'.
- **few-shot** ✅ `ok`: DET N V DET N SP (DET N) cumple todas las reglas sintácticas y semánticas.

## N2-33 (nivel 2): `Mi gato blanco corre en el jardín .`

Fenómeno: SP circunstancial sin objeto  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: DET(ms) N(ms) ADJ(ms) V(3s) PREP DET N PUNTO. Deriva correctamente, hay concordancia y 'correr' es intransitivo sin objeto directo.

## N2-34 (nivel 2): `Las estudiantes inteligentes estudiaron en la escuela .`

Fenómeno: Género común, SP circunstancial  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: DET(f,p) N(f,p) ADJ(f,p) V(3p) SP(DET(f,s) N(f,s)). Cumple C1, C2 y la gramática.

## N2-35 (nivel 2): `El viejo profesor no es feliz .`

Fenómeno: Adjetivo antepuesto, negación con copulativo  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: DET N ADJ NEG VCOP ADJ PUNTO. Sujeto, negación, VCOP y atributo concuerdan (C1, C2, C3).

## N2-36 (nivel 2): `Sofía cocinó el pan para Luis .`

Fenómeno: SP beneficiario (adjunción al verbo)  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: NPROP V SN SP; sujeto (3s) y verbo (3s) concuerdan, 'cocinar' admite objeto directo y el SP es circunstancial.

## N2-37 (nivel 2): `Ellas vivirán en una ciudad muy grande .`

Fenómeno: SP con adjetivo intensificado  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `semantico` (C5): El verbo 'vivirán' es intransitivo y no puede llevar un objeto directo o sintagma nominal como complemento directo (aunque aquí funciona como circunstancial de lugar, lo cual es sintácticamente correcto, revisemos la transitividad: 'vivir' es intransitivo, no lleva OD, pero 'en una ciudad muy grande' es un SP de lugar, no un objeto directo. Espera, el análisis gramatical requiere C5 si lleva OD. Aquí no hay OD, es un SP. ¿Por qué fallaría C5? No falla por C5. Veamos la concordancia de sujeto-verbo: 'Ellas' (3ª persona plural) y 'vivirán' (3ª persona plural). ¿Género? Los pronombres no tienen género explícito en la regla C1, pero 'Ellas' es femenino plural. 'vivirán' no tiene género. ¿Falla C1, C2, C3, C4, C5? Ninguna falla. Vamos a revisar si 'vivirán' es intransitivo. Sí. ¿Hay OD? No. Entonces la oración es 'ok'.
- **few-shot** ✅ `ok`: PRON(3p) V(3p) SP con DET, N, INT y ADJ; todas las concordancias y reglas se cumplen.

## N2-38 (nivel 2): `La casa del profesor está en el parque .`

Fenómeno: Contracción, atributo SP  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `semantico` (C4): La contracción del se usa con un sustantivo masculino singular, pero profesor es correcto y cumple; sin embargo, no hay fallo en C4, sino que profesor es masculino singular.
- **few-shot** ✅ `ok`: DET N CONTR N VCOP SP; concuerdan DET, N y CONTR ('del' con masculino singular), y el sujeto con VCOP.

## N2-39 (nivel 2): `Siempre caminamos al parque temprano .`

Fenómeno: Adverbio inicial, sujeto omitido  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `semantico` (C4): "al" solo debe ir seguido de un sustantivo masculino singular, pero "parque" es correcto.
- **few-shot** ✅ `ok`: ADV V CONTR N ADV. Deriva correctamente con sujeto omitido y se cumplen todas las reglas de concordancia y restricciones.

## N2-40 (nivel 2): `El hombre alto miró la flor roja con el telescopio .`

Fenómeno: SP instrumental tras objeto modificado  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: DET N ADJ V DET N ADJ SP DET N PUNTO. C1, C2 y las demás reglas se cumplen perfectamente.

## N2-41 (nivel 2): `Juan es un profesor bastante inteligente .`

Fenómeno: Atributo SN con intensificador  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: Sujeto NPROP(3s) VCOP(3s) con atributo nominal modificado por un adjetivo con intensificador; cumple C2 y C3.

## N2-42 (nivel 2): `Los gatos pequeños no beben rápidamente .`

Fenómeno: Negación, adverbio de modo  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración cumple con la gramática, el vocabulario y todas las reglas de concordancia.
- **few-shot** ✅ `ok`: DET N ADJ NEG V ADV PUNTO; cumple con C1, C2 y la estructura gramatical.

## N2-43 (nivel 2): `Yo cantaré en la casa de María .`

Fenómeno: Dos SP encadenados  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `semantico` (C2): El sujeto 'Yo' (1.ª persona singular) no concuerda en persona con el verbo 'cantaré' (1.ª persona singular... espera, 'cantaré' es 1.ª persona singular, sí concuerda). Revisemos: 'Yo' es 1.ª persona singular, 'cantaré' es 1.ª persona singular. La concordancia C2 es correcta. El verbo 'cantaré' es intransitivo sintácticamente aquí, pero no lleva objeto directo, por lo que C5 se cumple. Reevaluando: Yo (PRON, 1s) cantaré (V, 1s) en (PREP) la (DET) casa (N) de (PREP) María (NPROP). Todo es correcto.
- **few-shot** ✅ `ok`: PRON(1s) V(1s) ADV SP con SP nominal; C2 se cumple entre sujeto y verbo.

## N2-44 (nivel 2): `Nosotras estuvimos en el jardín ayer .`

Fenómeno: Pretérito de estar, atributo SP  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ✅ `ok`: La oración es gramaticalmente correcta, cumple con la concordancia y el uso del verbo estuve.
- **few-shot** ✅ `ok`: PRON(1p) VCOP(1p) SP ADV PUNTO; cumple con todas las reglas y concordancias.

## N2-45 (nivel 2): `Tú escribiste una carta muy bonita .`

Fenómeno: 2.ª persona, intensificador  
Esperado: `ok` · Parser: `ok`

- **zero-shot** ❌ `semantico` (C2): El sujeto 'Tú' es 2.ª persona del singular, pero el verbo 'escribiste' no concuerda adecuadamente en persona.
- **few-shot** ✅ `ok`: PRON(2s) V(2s) DET(f,s) N(f,s) INT ADJ(f,s). Cumple C1, C2 y la estructura sintáctica.

## N2-46 (nivel 2): `Ana camina al escuela .`

Fenómeno: C4: al + femenino  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ❌ `sintactico`: La contracción 'al' solo puede ir seguida de un sustantivo masculino singular, pero 'escuela' es femenino.
- **few-shot** ✅ `semantico` (C4): 'al' (CONTR) va con un sustantivo masculino singular, pero 'escuela' es femenino.

## N2-47 (nivel 2): `Pedro camina el parque .`

Fenómeno: C5: intransitivo con objeto  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C5): El verbo caminar es intransitivo y no puede llevar el objeto directo 'el parque'.
- **few-shot** ✅ `semantico` (C5): 'caminar' es un verbo intransitivo y no puede llevar un objeto directo.

## N2-48 (nivel 2): `Ana vive en las ciudad .`

Fenómeno: C1 dentro de un SP  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C1): El artículo 'las' (femenino plural) no concuerda con el sustantivo 'ciudad' (femenino singular).
- **few-shot** ✅ `semantico` (C1): 'las' es plural y 'ciudad' es singular.

## N2-49 (nivel 2): `El gato blanca corre rápidamente .`

Fenómeno: C1: ADJ-N en género  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C1): El determinante, el nombre y el adjetivo no concuerdan en género (el gato es masculino y blanca es femenino).
- **few-shot** ✅ `semantico` (C1): 'El' es masculino singular y 'blanca' es femenino singular.

## N2-50 (nivel 2): `La estudiante alto canta bien .`

Fenómeno: C1: género común definido por DET  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C1): El artículo 'La' (femenino singular) y el adjetivo 'alto' (masculino singular) no concuerdan con el sustantivo 'estudiante'.
- **few-shot** ✅ `semantico` (C1): 'estudiante' es singular pero 'alto' no concuerda en género femenino con el sustantivo.

## N2-51 (nivel 2): `Los niños de la profesora corre .`

Fenómeno: C2 a distancia con atractor singular  
Esperado: `semantico` · Parser: `semantico`

- **zero-shot** ✅ `semantico` (C2): El sujeto plural "Los niños de la profesora" no concuerda en número con el verbo singular "corre".
- **few-shot** ✅ `semantico` (C2): 'Los niños de la profesora' es sujeto plural (3p) y 'corre' está en singular (3s).

## N3-52 (nivel 3): `Juan y María comen manzanas .`

Fenómeno: Coordinación de sujetos, sustantivo sin determinante  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'y' pertenece a la categoría CONJ, la cual no es utilizada por ninguna regla gramatical.
- **few-shot** ✅ `sintactico`: 'y' es CONJ: está en el vocabulario, pero ninguna regla la usa.

## N3-53 (nivel 3): `El perro que miró Ana corre .`

Fenómeno: Cláusula relativa  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'que' pertenece a una categoría no utilizada por la gramática.
- **few-shot** ✅ `sintactico`: 'que' es SUB: está en el vocabulario, pero ninguna regla de la gramática la usa.

## N3-54 (nivel 3): `¿ Come Juan una manzana ?`

Fenómeno: Interrogativa, orden VSO  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: El signo de interrogación inicial '¿' pertenece a una categoría no utilizada por la gramática.
- **few-shot** ✅ `sintactico`: '¿' es un signo de interrogación que ninguna regla de la gramática utiliza.

## N3-55 (nivel 3): `Juan la mira .`

Fenómeno: Pronombre clítico  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ❌ `lexico`: La palabra 'la' es un CLIT (clítico), categoría no admitida por la gramática en el sintagma nominal o como objeto.
- **few-shot** ✅ `sintactico`: 'la' es CLIT, está en el vocabulario pero ninguna regla de la gramática la usa.

## N3-56 (nivel 3): `La carta fue escrita por Ana .`

Fenómeno: Voz pasiva  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ❌ `lexico`: La palabra 'escrita' pertenece a la categoría PART, la cual no está permitida por ninguna regla gramatical.
- **few-shot** ✅ `sintactico`: 'escrita' es PART: está en el vocabulario, pero ninguna regla de la gramática la usa.

## N3-57 (nivel 3): `Ana ha comido el pan .`

Fenómeno: Tiempo compuesto  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'ha' pertenece a la categoría AUX, la cual no es utilizada por ninguna regla de la gramática.
- **few-shot** ✅ `sintactico`: 'ha' es AUX: está en el vocabulario, pero ninguna regla de la gramática la usa.

## N3-58 (nivel 3): `Luis estudia porque el profesor es inteligente .`

Fenómeno: Subordinada causal  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ❌ `lexico`: La palabra 'porque' pertenece a la categoría SUB, la cual no está incluida en el vocabulario utilizable por la gramática.
- **few-shot** ✅ `sintactico`: 'porque' es SUB: está en el vocabulario, pero ninguna regla gramatical la utiliza.

## N3-59 (nivel 3): `Cuando Ana canta , los niños bailan .`

Fenómeno: Subordinada temporal antepuesta  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'Cuando' pertenece a la categoría SUB, la cual no es reconocida por ninguna regla de la gramática.
- **few-shot** ✅ `sintactico`: 'Cuando' es SUB y ',' es SIGNO: están en el vocabulario, pero ninguna regla los usa.

## N3-60 (nivel 3): `Los niños comen manzanas .`

Fenómeno: Objeto sin determinante  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ❌ `ok`: La oración es gramaticalmente correcta, cumple con la concordancia de sujeto-verbo (C2) y el verbo transitivo admite objeto directo.
- **few-shot** ❌ `ok`: DET(mp) N(mp) V(3p) SN(fp). Cumple C1, C2 y la transitividad del verbo comer.

## N3-61 (nivel 3): `Ana le escribió una carta a Pedro .`

Fenómeno: Doble objeto con clítico  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ❌ `lexico`: La palabra 'le' pertenece a una categoría (CLIT) que no es utilizada por la gramática ni está en el vocabulario válido de la oración.
- **few-shot** ✅ `sintactico`: 'le' es CLIT: está en el vocabulario, pero ninguna regla gramatical la utiliza.

## N3-62 (nivel 3): `Juan o Pedro cocinará el pan .`

Fenómeno: Disyunción de sujetos  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La conjunción 'o' pertenece a la categoría CONJ, la cual no está incluida en ninguna regla de la gramática.
- **few-shot** ✅ `sintactico`: 'o' es CONJ: está en el vocabulario, pero ninguna regla de la gramática la usa.

## N3-63 (nivel 3): `Ana mira al gato pero el gato no mira a Ana .`

Fenómeno: Coordinación de oraciones  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'pero' pertenece a la categoría CONJ, la cual no es utilizada por ninguna regla de la gramática.
- **few-shot** ✅ `sintactico`: 'pero' es CONJ: está en el vocabulario, pero ninguna regla de la gramática la usa.

## N3-64 (nivel 3): `Los perros que el niño miró corren .`

Fenómeno: Relativa de objeto: concordancia a través de la cláusula  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ❌ `lexico`: La palabra 'que' pertenece a una categoría (SUB) no utilizada por la gramática.
- **few-shot** ✅ `sintactico`: 'que' es SUB: está en el vocabulario, pero ninguna regla la usa.

## N3-65 (nivel 3): `María es más alta que Ana .`

Fenómeno: Comparativa  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'más' pertenece a una categoría (COMP) no utilizada por la gramática.
- **few-shot** ✅ `sintactico`: 'más' (COMP) y 'que' (SUB) están en el vocabulario, pero ninguna regla de la gramática los utiliza.

## N3-66 (nivel 3): `Se come bien en la casa de Ana .`

Fenómeno: Impersonal con se  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ❌ `lexico`: La palabra 'Se' no pertenece al vocabulario permitido por la gramática.
- **few-shot** ✅ `sintactico`: 'Se' es CLIT: está en el vocabulario, pero ninguna regla de la gramática la usa.

## N3-67 (nivel 3): `Comió Juan el pan .`

Fenómeno: Orden VSO declarativo  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La gramática exige que el sujeto preceda al predicado (<sujeto_opcional> <predicado>), por lo que la estructura VSO no se puede derivar.
- **few-shot** ✅ `sintactico`: La gramática no permite la estructura V OSV; el sujeto debe preceder al predicado o no estar.

## N3-68 (nivel 3): `¿ Dónde vive Ana ?`

Fenómeno: Interrogativa parcial  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ❌ `lexico`: Las palabras '¿' y 'dónde' no pertenecen al vocabulario admitido por la gramática.
- **few-shot** ✅ `sintactico`: '¿' y 'dónde' son signos e interrogativos del vocabulario no usados por la gramática.

## N3-69 (nivel 3): `La niña cansada y feliz canta .`

Fenómeno: Coordinación de adjetivos  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'y' pertenece a la categoría CONJ, la cual no es utilizada por ninguna regla de la gramática.
- **few-shot** ✅ `sintactico`: 'y' es CONJ: está en el vocabulario, pero ninguna regla gramatical la incluye.

## N3-70 (nivel 3): `Ana corre rápido .`

Fenómeno: Adjetivo usado como adverbio  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ❌ `ok`: La oración es sintácticamente correcta y cumple con todas las reglas de concordancia.
- **few-shot** ❌ `semantico` (C5): 'correr' es un verbo intransitivo y no lleva objeto directo.

## N3-71 (nivel 3): `A Ana la miran los niños .`

Fenómeno: Objeto antepuesto con clítico  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'la' es de categoría CLIT, la cual ninguna regla de la gramática utiliza.
- **few-shot** ✅ `sintactico`: La estructura 'A Ana' es un SP, y la gramática no contempla un SP como inicio de un SN o sujeto directo sin un mecanismo de topicalización.

## N3-72 (nivel 3): `Los perros que miró Ana corre .`

Fenómeno: Relativa + C2 a distancia  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'que' pertenece a la categoría SUB, la cual no es utilizada por ninguna regla de la gramática.
- **few-shot** ✅ `sintactico`: 'que' es SUB: está en el vocabulario, pero ninguna regla gramatical la usa.

## N3-73 (nivel 3): `Juan y María come manzanas .`

Fenómeno: Sujeto coordinado con verbo singular  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La conjunción 'y' pertenece a la categoría CONJ, la cual no está incluida en ninguna regla de la gramática.
- **few-shot** ✅ `sintactico`: 'y' es CONJ: está en el vocabulario, pero ninguna regla la usa.

## N3-74 (nivel 3): `La carta fueron escrita por Ana .`

Fenómeno: Pasiva con auxiliar mal conjugado  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'escrita' pertenece a PART (participio), una categoría no usada por la gramática.
- **few-shot** ✅ `sintactico`: 'escrita' es PART, la cual está en una categoría del vocabulario que ninguna regla usa.

## N3-75 (nivel 3): `El perro que corre rápidamente come la manzanas .`

Fenómeno: Relativa + C1 en el objeto  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'que' pertenece a la categoría SUB, la cual no es utilizada por ninguna regla de la gramática.
- **few-shot** ✅ `sintactico`: 'que' es SUB: está en el vocabulario, pero ninguna regla la usa.

## N3-76 (nivel 3): `Ana le escribió una carta a los niño .`

Fenómeno: Doble objeto + C1  
Esperado: `sintactico` · Parser: `sintactico`

- **zero-shot** ✅ `sintactico`: La palabra 'le' pertenece a la categoría CLIT, la cual no es utilizada por ninguna regla de la gramática.
- **few-shot** ✅ `sintactico`: 'le' pertenece a la categoría CLIT que ninguna regla de la gramática utiliza.
