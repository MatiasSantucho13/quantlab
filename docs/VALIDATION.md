# Validación ejecutada — MVP 0.1

Entorno: Linux, Python 3.12. Fecha: 25/09/2026.

| Verificación | Resultado observado |
| --- | --- |
| `python -m pip install -r requirements.txt` | Correcto |
| `python -m pip install -e . --no-build-isolation` | Paquete editable construido e instalado |
| `python -m src.data.download` | Descarga real de 36 meses y SHA-256 de cada ZIP verificado contra CHECKSUM público |
| Validación del CSV | 6.576 barras, UTC, sin huecos, duplicados ni valores ausentes |
| `python -m pytest -q` | 33 pruebas aprobadas |
| `python -m src.run_analysis` | Informe, métricas, órdenes, operaciones, ledgers y figuras generados |
| Segunda ejecución en directorio independiente | metrics, risk, regimes, parameter_sensitivity, splits y selection idénticos byte por byte |
| `python scripts/execute_notebook.py --in-process` | 6 celdas de código ejecutadas; outputs enriquecidos y tres imágenes embebidas; esquema nbformat válido |
| Jupyter con kernel externo, TCP/IPC | No disponible: el entorno impide abrir sockets. No se afirma haber validado ese transporte |
| CLI con `--synthetic` y directorio separado | Pipeline completo ejecutado, salida identificada SYNTHETIC; datos históricos preservados |
| Inspección visual | Figuras de exploración y curvas/drawdowns revisadas: títulos, ejes y leyendas legibles |

La segunda ejecución histórica fue un control determinista de reproducción: no se cambiaron parámetros a partir de sus resultados. Los escenarios neto/frictionless estaban definidos antes de observar test.

Las pruebas validan ejemplos pequeños conocidos y controles de causalidad, no prueban ausencia de todo error posible ni garantizan realismo de las ejecuciones. La instalación no se verificó en Windows ni en un entorno completamente vacío.
