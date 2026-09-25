# QuantLab MVP 0.1 — Entrega final

## 1. Implementado

Sistema offline de investigación: ingesta verificable, validación estricta, indicadores y distribución, dos estrategias, benchmark, motor con efectivo/unidades, costos y deslizamiento configurables, métricas, riesgo, regímenes, selección temporal, notebook, CLI, reportes y pruebas matemáticas. No incluye ejecución real.

## 2. Arquitectura final

`src/data`, `src/features`, `src/strategies`, `src/backtest`, `src/analysis`, `src/experiments`, `src/reporting`, `src/config.py`, `src/run_analysis.py`; más `data/raw`, `data/processed`, `tests`, `notebooks`, `scripts`, `reports` y `docs`. README explica el mapa por responsabilidades.

## 3–4. Dataset y período real

6.576 velas BTC/USDT de 4 horas. Archivos públicos spot de Binance, 36 meses descargados y verificados con sus checksums. Período: 01/01/2022 00:00 UTC a 01/01/2025 00:00 UTC exclusivo; última apertura: 31/12/2024 20:00 UTC. CSV incluido; no se necesita red para repetir el análisis. USDT no equivale conceptualmente a USD.

## 5. Estrategias

Momentum por medias 10/50 seleccionadas entre nueve candidatos. Reversión a la media por z-score de 42 velas: entra bajo −2 y sale al llegar a 0. Benchmark comprar/mantener. Solo largo o efectivo.

## 6–7. Ejecución y costos

Señal al cierre t, compra/venta en apertura t+1. Quien ya posee unidades recibe el gap hasta la siguiente apertura. Capital inicial 10.000 USDT por cartera; comisión 0,10% por lado y deslizamiento base 0%. Comparación con un escenario sin fricciones. Liquidación predefinida en cierre final, con costo de salida. Timestamps identifican velas por apertura, incluso en registros marcados como terminal_close.

## 8. División temporal

| split | start_open_utc | last_open_utc | end_exclusive_utc | bars |
| --- | --- | --- | --- | --- |
| train | 2022-01-01 00:00:00+00:00 | 2023-10-20 08:00:00+00:00 | 2023-10-20 12:00:00+00:00 | 3945 |
| validation | 2023-10-20 12:00:00+00:00 | 2024-05-26 12:00:00+00:00 | 2024-05-26 16:00:00+00:00 | 1315 |
| test | 2024-05-26 16:00:00+00:00 | 2024-12-31 20:00:00+00:00 | 2025-01-01 00:00:00+00:00 | 1316 |

Entrenamiento 3.945 velas, validación 1.315 y test 1.316. La función de selección no recibe test; maximiza Sharpe neto de validación. Los indicadores pueden calentarse con historia pasada, pero cada cartera empieza en efectivo y no arrastra posiciones. Test se evalúa en los escenarios predefinidos; otra ejecución idéntica solo comprobó reproducibilidad, sin retocar la selección.

## 9. Resultados históricos por división

Retornos en decimales: 0,10 representa 10%.

| split | strategy | total_return | max_drawdown | sharpe | trades | exposure |
| --- | --- | --- | --- | --- | --- | --- |
| train | momentum | -0.29669 | -0.56711 | -0.42231 | 60 | 0.44436 |
| train | mean_reversion | -0.42061 | -0.57689 | -0.79652 | 37 | 0.25272 |
| train | buy_hold | -0.35564 | -0.67214 | -0.1863 | 1 | 1 |
| validation | momentum | 0.92576 | -0.13744 | 2.9475 | 17 | 0.65779 |
| validation | mean_reversion | 0.14172 | -0.12083 | 1.0288 | 10 | 0.14677 |
| validation | buy_hold | 1.3026 | -0.22445 | 3.0231 | 1 | 1 |
| test | momentum | 0.18953 | -0.19903 | 1.0003 | 16 | 0.54863 |
| test | mean_reversion | 0.014277 | -0.26428 | 0.22877 | 12 | 0.24772 |
| test | buy_hold | 0.35645 | -0.28396 | 1.2585 | 1 | 1 |

## 10. Fuera de muestra

Momentum: **18,95%** neto; reversión: **1,43%**; benchmark: **35,65%**. Ambos modelos quedan por debajo de comprar y mantener. No se afirma significancia estadística ni rentabilidad futura.

## 11. Riesgo observado

Drawdown de test: momentum **−19,90%**, reversión **−26,43%**, benchmark **−28,40%**. Peor intervalo móvil de 24 horas: aproximadamente −6,84%, −15,69% y −15,69%, respectivamente. Momentum redujo exposición y drawdown; reversión mantuvo una pérdida máxima importante pese al escaso retorno.

El VaR histórico 95% por vela de momentum fue aproximadamente 1,14%; no es un límite de pérdida ni una predicción. Las métricas usan cierres y pueden ignorar caídas intravela.

## 12. Regímenes

En test, momentum tuvo media por vela de aproximadamente +0,111% en régimen alcista de alta volatilidad, frente a +0,092% del benchmark en esas mismas 290 velas. En alcista de baja volatilidad, momentum promedió −0,017%, contra +0,014% del benchmark. Reversión promedió −0,026% en alcista de alta volatilidad, donde su exposición fue solo 2,41%. Son comparaciones descriptivas condicionadas, no efectos causales.

## 13. Pruebas ejecutadas

33 casos pytest aprobados, con ejemplos manuales para retornos, ejecución, gaps, costos, equity, drawdown, métricas y señales; además controles de causalidad, validación y splits. Instalación por requirements y editable correctas. Pipeline histórico ejecutado y reproducido; seis salidas estructuradas idénticas byte a byte. Fallback sintético completo ejecutado aparte. Notebook: seis celdas ejecutadas dentro de IPython, con outputs enriquecidos; kernel Jupyter externo no validado porque el entorno bloquea sockets.

## 14. Reproducción

Desde la carpeta quantlab:

```bash
python -m pip install -r requirements.txt
python -m src.run_analysis
python -m pytest -q
python scripts/execute_notebook.py --in-process
```

Descarga opcional: `python -m src.data.download`. Muestra explícita: `python -m src.run_analysis --synthetic --output reports_synthetic`.

## 15. Límites conocidos

Un activo y una fuente, sesgo de selección de superviviente, nueve comparaciones de validación, un único test, sin pruebas de significancia ni corrección por múltiples comparaciones. Sin spread variable, profundidad, impacto, latencia, lotes mínimos, impuestos ni rendimiento del efectivo. Sharpe anualizado presupone escalado temporal; CAGR/Calmar se omiten en períodos de menos de un año. Sin Monte Carlo, ML ni dashboard. Windows no fue probado.

## 16. Git

Rama main. Commits separados para implementación/pruebas, datos verificados y documentación/resultados. El paquete incluye `quantlab-history.bundle` para recuperar el historial completo. No se publicó en GitHub ni se configuró un remoto. Para recuperar el repositorio después de extraer el ZIP:

```bash
git clone quantlab-history.bundle quantlab-restored
cd quantlab-restored
git log --oneline
git status --short
```

## 17. ¿Presentable como portfolio cuantitativo?

**Sí, como MVP de investigación educativa**, con resultados auditables y límites explícitos. Su valor reside en metodología y corrección verificable; no en haber encontrado una estrategia ganadora. Está listo para revisión y publicación manual en GitHub.

## FILES I MUST UNDERSTAND BEFORE AN INTERVIEW

La guía siguiente cubre los 15 archivos centrales, en orden, con función, concepto cuantitativo, concepto Python y pregunta probable.

 Primero reconstruí un trade a mano; después compará los resultados por período. No hace falta memorizar el código: sí explicar decisiones y límites.

| Orden y archivo | Qué hace | Concepto cuantitativo | Concepto Python | Pregunta probable |
| --- | --- | --- | --- | --- |
| 1. `src/config.py` | Centraliza frecuencia, capital y costos | 2.191,5 velas por año; anualización | dataclass inmutable y property | ¿Por qué no usás 252 días de bolsa? |
| 2. `src/data/validation.py` | Ordena y rechaza datos ambiguos | Huecos y precios inválidos distorsionan retornos | DataFrame, máscaras y excepciones | ¿Por qué no rellenar los huecos con el último cierre? |
| 3. `src/data/download.py` | Descarga archivos públicos y verifica hashes | Procedencia de datos y unidades temporales | HTTP, ZIP en memoria, hilos, SHA-256 | ¿Cómo reproducís exactamente el dataset? |
| 4. `src/features/indicators.py` | Retornos, medias, volatilidad y distribución | Retorno simple/logarítmico, ddof y colas | pct_change, rolling, reducción vectorizada | ¿Por qué sumás retornos logarítmicos y componés los simples? |
| 5. `src/strategies/base.py` | Define la interfaz compartida | Separa señal de ejecución | ABC y método abstracto | ¿Cómo agregás una estrategia sin modificar el motor? |
| 6. `src/strategies/momentum.py` | Compara medias móviles | Persistencia de tendencia y warmup | Herencia, dataclass y operaciones vectorizadas | ¿Qué mercado perjudica a una estrategia tendencial? |
| 7. `src/strategies/mean_reversion.py` | Implementa entrada y salida por z-score | Reversión y estado de posición | Bucle con estado y Series indexada | ¿Por qué no alcanza con una condición independiente por fila? |
| 8. `src/backtest/engine.py` | Lleva efectivo, unidades, órdenes y operaciones | Causalidad, gaps, mark-to-market y liquidación | Dataclass, registros y alineación de índices | ¿Quién recibe el salto entre cierre y apertura? |
| 9. `src/backtest/costs.py` | Calcula cantidades y cobros | Costos por lado y deslizamiento adverso | Funciones puras y validación | ¿Por qué las unidades se dividen por 1 + comisión? |
| 10. `src/analysis/metrics.py` | Resume retorno, riesgo y trades | CAGR, Sharpe, Calmar y profit factor | Series, filtros y NaN | ¿Por qué Sharpe puede engañar con retornos dependientes? |
| 11. `src/analysis/drawdown.py` | Calcula caída desde el máximo | Capital inicial como primer máximo posible | cummax y clip | ¿Qué pasa si perdés dinero en la primera operación? |
| 12. `src/experiments/parameter_sensitivity.py` | Divide y selecciona nueve candidatos | Validación temporal y sobreajuste | Funciones sin acceso al test y orden estable | ¿Por qué el mejor Sharpe de validación puede caer en test? |
| 13. `src/analysis/regimes.py` | Clasifica condiciones usando información pasada | Umbral expansivo y clasificación ex ante | rolling, expanding, shift y groupby | ¿Qué fuga provocaría usar la mediana de volatilidad de toda la serie? |
| 14. `src/analysis/risk.py` | VaR, cola y peores intervalos | VaR no es máximo de pérdida; cola histórica | quantile, máscaras y rolling.apply | ¿Cómo puede una estrategia tener VaR cero y sufrir pérdidas? |
| 15. `tests/test_quantitative.py` | Verifica casos conocidos y causalidad | Validación matemática independiente | pytest, parametrización y approximate equality | ¿Qué prueba detectaría una ejecución imposible al cierre anterior? |

Después leé `reports/quant_report.md`: defendé por qué ambas estrategias quedaron debajo del benchmark en test y qué evidencia adicional necesitarías antes de afirmar una ventaja. `src/reporting/report.py` muestra en qué orden se ejecuta el protocolo completo.
