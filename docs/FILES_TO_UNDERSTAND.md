# FILES I MUST UNDERSTAND BEFORE AN INTERVIEW

Orden sugerido de lectura. Primero reconstruí un trade a mano; después compará los resultados por período. No hace falta memorizar el código: sí explicar decisiones y límites.

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
