# oc-meter

Instrumento de medición para sesiones de OpenCode. Mide recursos y tiempo, y emite
un registro JSON canónico. No ejecuta prompts, no modifica proyectos, no juzga si el
trabajo es correcto, no calcula dinero. El conductor del experimento es otro paquete.

## Qué mide

Unidad interna: tokens enteros. La presentación en K es responsabilidad de `report`.

| Cantidad | Definición operacional | Frontera |
|---|---|---|
| inputTokens | entrada NO cacheada (`tokens.input`) | mensajes assistant del árbol completo |
| outputTokens | generación visible (`tokens.output`) | idem; excluye reasoning si el proveedor lo reporta aparte |
| reasoningTokens | fase de razonamiento (`tokens.reasoning`) | idem; guarda de doble conteo |
| cacheReadTokens | tokens servidos desde caché por coincidencia de prefijo | idem |
| cacheWriteTokens | tokens escritos a caché | idem; 0 o ausente según proveedor → flag |
| wallMs | t0 → t1 con debounce | árbol completo, reloj monotónico del observador |
| overlapFactor | busySumMs / wallMs | >1 indica trabajo concurrente |

Derivadas: promptTokens = input + cacheRead · generation = output + reasoning ·
cacheHitRatio = cacheRead / (cacheRead + input).

Bucket separado `maintenance` para title/summary/compaction. Se reporta work,
maintenance y all. No se descarta nada en silencio.

## Unidad de medición

Corrida = sesión raíz + todas las descendientes.
t0 = envío del primer prompt. t1 = quietud de todo el árbol sostenida δ ms.
δ declarado (default 5000). Se guardan t1Raw y t1Debounced.

## Requisitos

- Versión de OpenCode pineada (schema de export y flags derivan entre versiones).
- Contenedor desechable, sin credenciales. `--auto` convierte los `ask` por defecto
  (incluida lectura de `.env`) en permitidos: no debe haber secretos en el entorno.
- La caché del proveedor NO se desactiva; se observa. Alternar el orden de los
  brazos entre réplicas para no acumular el efecto a favor del mismo.

## Uso

oc-meter doctor                      # certificado de limpieza del entorno
oc-meter zero [--live]               # medición cero (offline por defecto)
oc-meter measure --root <ses_id> --out record.json
oc-meter report record.json --format markdown|txt
oc-meter compare records/ --group-by arm

`report` renderiza registros existentes; nunca vuelve a medir.
`compare` rechaza registros con distinto modelo/variante, versión de instrumento,
mappingHash o workId.

## Calibración

Ocho checks (cero, mapeo congelado, doble conteo, atribución del árbol,
conservación vs stats, reloj, determinismo, sonda conocida).
`uv run pytest` — los siete primeros sobre fixtures, sin cuota.

## Limitaciones conocidas

- Caché del proveedor: no desactivable; efecto de orden entre brazos.
- Tokenizador: los tokens no son comparables entre modelos; modelo pineado por lote.
- Paralelismo de subagentes: una ganancia de tiempo puede venir de concurrencia,
  no de eficiencia; interpretar siempre junto a overlapFactor.
- Agentes de mantenimiento: consumen tokens; bucket separado, nunca ocultos.
- Drift del schema de export: versión pineada + mappingHash; revalidar al actualizar.
- Ruido temporal: carga del proveedor y red afectan wallMs; requiere más réplicas
  que las métricas de tokens.
- Variante de razonamiento: si solo es configurable y no observable, se marca flag.

## Formato de salida

El formato de salida es un JSON estructurado.

```json
{
  "instrument": { "name": "oc-meter", "version": "0.1.0", "mappingHash": "sha256:…" },
  "run": { "id": "r-0007", "labels": { "arm": "layered" }, "workId": "sha256:…" },
  "conditions": {
    "opencodeVersion": "2.x.y",
    "model": "deepseek/deepseek-v4-flash",
    "reasoningEffort": "low",
    "reasoningEffortSource": "observed",
    "modelHomogeneous": true,
    "cleanlinessCertificateHash": "sha256:…"
  },
  "tree": { "root": "ses_…", "sessions": 9, "maxDepth": 1, "requests": 74 },
  "time": {
    "t0": "…", "t1Raw": "…", "t1Debounced": "…", "debounceMs": 5000,
    "wallMs": 412000, "busySumMs": 690000, "overlapFactor": 1.67,
    "clockSource": "observer-monotonic"
  },
  "requests": [
    {
      "sessionId": "ses_…", "agent": "backend", "segmentId": "003", "class": "work",
      "model": "deepseek/deepseek-v4-flash", "reasoningEffort": "low",
      "inputTokens": 1820, "outputTokens": 640, "reasoningTokens": 310,
      "cacheReadTokens": 14200, "cacheWriteTokens": 0
    }
  ],
  "segments": [
    { "id": "003", "wallMs": 91000, "inputTokens": 0, "outputTokens": 0,
      "reasoningTokens": 0, "cacheReadTokens": 0, "cacheWriteTokens": 0 }
  ],
  "totals": {
    "work":        { "inputTokens": 0, "outputTokens": 0, "reasoningTokens": 0, "cacheReadTokens": 0, "cacheWriteTokens": 0 },
    "maintenance": { "inputTokens": 0, "outputTokens": 0, "reasoningTokens": 0, "cacheReadTokens": 0, "cacheWriteTokens": 0 },
    "all":         { "inputTokens": 0, "outputTokens": 0, "reasoningTokens": 0, "cacheReadTokens": 0, "cacheWriteTokens": 0 }
  },
  "derived": { "promptTokens": 0, "generationTokens": 0, "cacheHitRatio": 0.0 },
  "flags": []
}
```

## Versionado

Semántico. Cambiar una definición operacional = major. Todo registro lleva
versión del instrumento y mappingHash; el comparador rechaza mezclas.