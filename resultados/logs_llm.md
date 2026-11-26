# Logs LLM — TLP02-2026

Generado: 2026-11-25 21:45
Modelo: gemini-3.5-flash-lite | Modo: ambos | Oraciones: 3

## Caso 1: `El perro come .`

**Esperado:** `ok`

### Parser propio ✅
- Veredicto: `ok`
- Razón: oración válida

### Gemini zero-shot ❌
- Veredicto: `error`
- Razón: API key de Gemini no configurada. Ver GEMINI_API_KEY en api_llm.py

### Gemini few-shot ❌
- Veredicto: `error`
- Razón: API key de Gemini no configurada. Ver GEMINI_API_KEY en api_llm.py

---

## Caso 2: `María compra una manzana .`

**Esperado:** `ok`

### Parser propio ✅
- Veredicto: `ok`
- Razón: oración válida

### Gemini zero-shot ❌
- Veredicto: `error`
- Razón: API key de Gemini no configurada. Ver GEMINI_API_KEY en api_llm.py

### Gemini few-shot ❌
- Veredicto: `error`
- Razón: API key de Gemini no configurada. Ver GEMINI_API_KEY en api_llm.py

---

## Caso 3: `Los niños corren .`

**Esperado:** `ok`

### Parser propio ✅
- Veredicto: `ok`
- Razón: oración válida

### Gemini zero-shot ❌
- Veredicto: `error`
- Razón: API key de Gemini no configurada. Ver GEMINI_API_KEY en api_llm.py

### Gemini few-shot ❌
- Veredicto: `error`
- Razón: API key de Gemini no configurada. Ver GEMINI_API_KEY en api_llm.py

---
