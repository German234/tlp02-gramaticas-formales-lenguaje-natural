# Logs LLM — TLP02-2026

Generado: 2026-11-25 17:32
Modelo: gemini-2.0-flash | Modo: ambos | Oraciones: 3

## Caso 1: `El perro come .`

**Esperado:** `ok`

### Parser propio ✅
- Veredicto: `ok`
- Razón: oración válida

### Gemini zero-shot ❌
- Veredicto: `error`
- Razón: HTTP 404: Not Found

### Gemini few-shot ❌
- Veredicto: `error`
- Razón: HTTP 404: Not Found

---

## Caso 2: `María compra una manzana .`

**Esperado:** `ok`

### Parser propio ✅
- Veredicto: `ok`
- Razón: oración válida

### Gemini zero-shot ❌
- Veredicto: `error`
- Razón: HTTP 404: Not Found

### Gemini few-shot ❌
- Veredicto: `error`
- Razón: HTTP 404: Not Found

---

## Caso 3: `Los niños corren .`

**Esperado:** `ok`

### Parser propio ✅
- Veredicto: `ok`
- Razón: oración válida

### Gemini zero-shot ❌
- Veredicto: `error`
- Razón: HTTP 404: Not Found

### Gemini few-shot ❌
- Veredicto: `error`
- Razón: HTTP 404: Not Found

---
