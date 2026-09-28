from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ..analysis.drawdown import drawdown
from ..analysis.metrics import metrics
from ..analysis.risk import risk
from ..analysis.regimes import classify, by_regime
from ..features.indicators import features, distribution
from ..experiments.parameter_sensitivity import split, experiment
from ..strategies.mean_reversion import MeanReversion
from ..backtest.engine import run

COLORS=["#167d9a","#d47732","#6157a3"]

def markdown(frame):
    d=frame.copy()
    if isinstance(d,pd.Series): d=d.to_frame("value")
    d=d.reset_index()
    def fmt(x):
        if isinstance(x,(float,np.floating)): return "N/A" if not np.isfinite(x) else f"{x:.5g}"
        return str(x)
    return "| "+" | ".join(map(str,d.columns))+" |\n| "+" | ".join(["---"]*len(d.columns))+" |\n"+"\n".join("| "+" | ".join(fmt(x) for x in row)+" |" for row in d.itertuples(index=False,name=None))

def generate(data, quality, metadata, config, output):
    out=Path(output); figures=out/"figures"; figures.mkdir(parents=True,exist_ok=True)
    parts=split(data)
    sensitivity,selected=experiment(parts["train"],parts["validation"],config)
    # Freeze selection before any test metrics or full-history feature exploration.
    selection={"strategy":"momentum", "parameters":selected.get_parameters(),
        "selection":"highest validation net Sharpe, ties lower fast then slow", "candidates":9,
        "train_end":str(parts["train"].index[-1]),"validation_end":str(parts["validation"].index[-1]),
        "test_start":str(parts["test"].index[0]),"dataset_sha256":quality["sha256"]}
    (out/"selection.json").write_text(json.dumps(selection,indent=2))
    strategies={"momentum":selected,"mean_reversion":MeanReversion(),"buy_hold":None}
    signals={name:s.generate_signals(data) if s else pd.Series(1,index=data.index) for name,s in strategies.items()}
    results={}; rows=[]; risks=[]; regime_rows=[]
    labels=classify(data)
    for phase,part in parts.items():
        for name,s in strategies.items():
            for scenario,fee,slip in [("net",config.fee,config.slippage),("frictionless",0.,0.)]:
                result=run(part,signals[name].loc[part.index],config.initial_capital,fee,slip,benchmark=s is None)
                results[(phase,name,scenario)]=result
                rows.append({"split":phase,"strategy":name,"scenario":scenario,
                    **metrics(result,config.periods_per_year).to_dict()})
                if scenario=="net":
                    risks.append({"split":phase,"strategy":name,**risk(result)})
                    reg=by_regime(result,labels.loc[part.index]).reset_index()
                    reg["split"]=phase; reg["strategy"]=name; regime_rows.append(reg)
                    result.bars.to_csv(out/f"{phase}_{name}_ledger.csv")
                    result.trades.to_csv(out/f"{phase}_{name}_trades.csv",index=False)
                    result.orders.to_csv(out/f"{phase}_{name}_orders.csv",index=False)
    metrics_table=pd.DataFrame(rows); risk_table=pd.DataFrame(risks); regime_table=pd.concat(regime_rows,ignore_index=True)
    metrics_table.to_csv(out/"metrics.csv",index=False); risk_table.to_csv(out/"risk.csv",index=False)
    regime_table.to_csv(out/"regimes.csv",index=False); sensitivity.to_csv(out/"parameter_sensitivity.csv",index=False)
    f=features(data,config.periods_per_year); stats=distribution(f.simple_return)
    stats.to_csv(out/"return_statistics.csv")
    f.to_csv(out.parent/"data"/"processed"/"features.csv") if (out.parent/"data"/"processed").is_dir() else None
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,
        "axes.grid":True,"grid.alpha":.18,"figure.facecolor":"white","savefig.dpi":150})
    fig,ax=plt.subplots(3,2,figsize=(13,10),layout="constrained")
    f.close.plot(ax=ax[0,0],color=COLORS[0],title="BTC/USDT · close",ylabel="USDT")
    f.simple_return.plot(ax=ax[0,1],color=COLORS[0],title="4-hour simple returns",linewidth=.5)
    ax[1,0].hist(f.simple_return.dropna(),bins=100,color=COLORS[0]); ax[1,0].set(title="Return distribution",xlabel="Simple return",ylabel="Bars")
    f.rolling_volatility.plot(ax=ax[1,1],color=COLORS[1],title="42-bar volatility · annualized")
    f.volume.plot(ax=ax[2,0],color=COLORS[0],title="Volume",ylabel="BTC",linewidth=.6)
    f[["close","rolling_mean"]].plot(ax=ax[2,1],title="Close and 42-bar mean",color=COLORS[:2])
    fig.suptitle(f"QuantLab | {metadata['kind']} | exploratory data analysis",fontsize=16)
    fig.savefig(figures/"exploration.png"); plt.close(fig)
    fig,ax=plt.subplots(2,3,figsize=(15,8),layout="constrained")
    for col,phase in enumerate(parts):
        for color,name in zip(COLORS,strategies):
            result=results[(phase,name,"net")]
            # Include initial capital to show entry costs and first-bar drawdowns.
            start=result.bars.index[0]-pd.Timedelta(config.frequency)
            eq=pd.concat([pd.Series([config.initial_capital],index=[start]),result.bars.equity])
            ax[0,col].plot(eq.index,eq,label=name,color=color)
            dd=drawdown(eq,config.initial_capital)
            ax[1,col].plot(dd.index,dd*100,label=name,color=color)
        ax[0,col].set_title(phase.upper()); ax[0,col].set_ylabel("Equity · USDT")
        ax[1,col].set_ylabel("Drawdown · %")
        for a in ax[:,col]: a.tick_params(axis="x",labelrotation=25)
    ax[0,0].legend(fontsize=8)
    fig.suptitle("Net strategy results | separate cash portfolios per split",fontsize=16)
    fig.savefig(figures/"equity_drawdown.png"); plt.close(fig)
    validation=sensitivity[sensitivity.split=="validation"].pivot(index="fast",columns="slow",values="sharpe")
    fig,ax=plt.subplots(figsize=(7,4),layout="constrained")
    im=ax.imshow(validation.to_numpy(),cmap="RdYlGn",aspect="auto")
    ax.set_xticks(range(3),validation.columns); ax.set_yticks(range(3),validation.index)
    ax.set(xlabel="Slow MA bars",ylabel="Fast MA bars",title="Validation net Sharpe | 9 fixed candidates")
    for i in range(3):
        for j in range(3): ax.text(j,i,f"{validation.iloc[i,j]:.2f}",ha="center",va="center")
    fig.colorbar(im,ax=ax); fig.savefig(figures/"sensitivity.png"); plt.close(fig)
    boundaries=pd.DataFrame([{"split":k,"start_open_utc":str(v.index[0]),"last_open_utc":str(v.index[-1]),
        "end_exclusive_utc":str(v.index[-1]+pd.Timedelta(config.frequency)),"bars":len(v)} for k,v in parts.items()])
    boundaries.to_csv(out/"splits.csv",index=False)
    net=metrics_table[metrics_table.scenario=="net"]
    test=net[net.split=="test"].set_index("strategy")
    conclusions=[]
    benchmark=test.loc["buy_hold","total_return"]
    for name in ("momentum","mean_reversion"):
        row=test.loc[name]
        conclusions.append(f"- {name}: test return {row.total_return:.2%}, versus buy-and-hold {benchmark:.2%}; "
            f"difference {(row.total_return-benchmark)*100:.2f} percentage points. Maximum drawdown {row.max_drawdown:.2%}; "
            f"exposure {row.exposure:.1%}; {int(row.trades)} round trips. These are descriptive observations, not significance tests.")
    report=f"""# QuantLab — Research report

## 1. Dataset and provenance

**{metadata['kind']}**. Source: {metadata.get('source')}. BTC/USDT (USDT is not USD). Frequency: {config.frequency}.
Coverage: {data.index[0]} through {data.index[-1]+pd.Timedelta(config.frequency)} (exclusive).
Timestamp denotes candle OPEN. Data SHA-256: `{quality['sha256']}`.
Public archive schema: https://github.com/binance/binance-public-data .
Checksums and exact archive URLs are recorded in the dataset JSON sidecar.
If the dataset is synthetic, every observation below is a software demonstration, not a BTC finding.

## 2. Data quality

{markdown(pd.Series(quality))}

Missing prices are not forward filled; incomplete data aborts analysis.

## 3. Return and volume statistics

Simple return: close[t]/close[t-1] - 1. Log return: log(close[t]/close[t-1]).
First undefined observation is excluded from descriptive statistics. Excess kurtosis uses the normal=0 convention.
Rolling mean/std/volatility use 42 bars (7 days), std uses ddof=1.

{markdown(stats)}

{markdown(data.volume.describe())}

![Exploration](figures/exploration.png)

## 4. Strategies and hypotheses

Momentum: MA({selected.fast}) > MA({selected.slow}) means long, otherwise cash. Hypothesis: trends may persist.
Mean reversion: 42-bar rolling z-score below -2 enters long, z-score >=0 exits. Hypothesis: deviations may partially revert.
Zero variance/insufficient history yields cash. Both strategies use completed candles only.
Buy-and-hold is the mandatory benchmark and buys at each split's first open.

## 5. Backtest methodology and execution

Signals at close t execute at open t+1. The engine tracks cash and asset units; no leverage, shorting or rebalancing while holding.
Existing units receive overnight/open gaps; newly bought units receive only subsequent moves.
Each split starts with {config.initial_capital:,.2f} USDT cash; strategy first bar is cash because the local signal is shifted.
Past data warms indicators and signal state, but holdings are not carried across splits. No future prices warm indicators.
All open positions liquidate at the final candle close, a predetermined endpoint convention; this includes exit costs.
The final signal is ignored. Trades include these terminal exits, flagged in the ledger. Marks use candle close.
Ledger/order timestamps identify candle OPEN even for a terminal_close execution; that fill occurs at that candle end.
Exposure is the fraction of bars held from open through close, before terminal liquidation, not a capital-weighted risk measure.

## 6. Transaction costs and benchmark

Fee: {config.fee:.3%} of executed notional on EACH side. Slippage: {config.slippage:.3%} adverse price adjustment on EACH side.
A buy uses units = cash / (open × (1+slippage) × (1+fee)); a sell receives units × open × (1-slippage) × (1-fee).
Frictionless means both fee and slippage are zero. Benchmark bears entry and terminal exit costs too.

## 7. Chronological train / validation / held-out test

{markdown(boundaries.set_index('split'))}

Nine momentum configurations: fast ∈ {{10,20,30}}, slow ∈ {{50,100,150}}. Train and validation results are recorded.
Select the highest validation NET Sharpe, ties use lower fast then slow. No test input enters the selection function.
Selected configuration and data hash are frozen in selection.json before test evaluation.
Mean-reversion parameters are fixed in advance. Test runs once per declared cost scenario, without subsequent selection.
Training results for the selected model are retrospective in-sample descriptions, not unbiased estimates.
Full-period exploration is descriptive after selection. Reusing this test to redesign a strategy would invalidate its held-out status.

## 8. Performance metrics (net)

Ratios/returns are decimals; 0.10 means 10%. Annualization: {config.periods_per_year:g} four-hour bars/year (365.25-day crypto calendar).
Annualized return and Calmar are omitted when a split is shorter than one year. Volatility and Sharpe are annualized descriptive estimates;
Sharpe assumes zero risk-free return and square-root time scaling, which can mislead with autocorrelation or changing variance.
Drawdown includes initial capital as a possible peak. Profit factor uses closed-trade cash P&L; absent losses yields N/A.

{markdown(net.set_index(['split','strategy'])[['total_return','annualized_return','annualized_volatility','sharpe','max_drawdown','calmar','win_rate','trades','average_trade','best_trade','worst_trade','exposure','profit_factor']])}

![Equity and drawdown](figures/equity_drawdown.png)

## 9. Cost sensitivity

{markdown(metrics_table.set_index(['split','strategy','scenario'])[['total_return','trades','fees_paid','turnover']])}

Trading frequency creates additional entry/exit costs. Fees_paid excludes implicit slippage, which is incorporated in execution prices.

## 10. Held-out observations

{chr(10).join(conclusions)}

## 11. Market regimes

Four combinations: above/below trailing 180-bar price mean, and high/low 42-bar volatility relative to its expanding median
(minimum 180 valid volatility observations). Labels shift one bar so they are known at the current open. Warmup is explicit.
Rows are conditional bar statistics; disconnected regimes are NOT independent tradable equity curves or causal effects.
Market gaps occur after the label's last known close; this is an ex-ante classification, not hindsight labeling.

{markdown(regime_table.set_index(['split','strategy','regime']))}

## 12. Risk

Historical 95% VaR is minus the 5th percentile of bar returns. Expected shortfall is minus the average return at/below that cutoff.
These are empirical 4-hour loss measures, can be negative, and are NOT maximum possible losses or forecasts.
Sparse exposure creates zero-heavy distributions and can produce zero VaR despite meaningful tail losses.
Worst 6-bar return is a rolling 24-hour compounded observation, not a calendar-day grouping.
Downside RMS averages squared negative returns over ALL bars (zero for nonnegative bars), without annualization.

{markdown(risk_table.set_index(['split','strategy']))}

## 13. Parameter sensitivity

{markdown(sensitivity.set_index(['split','fast','slow'])[['total_return','sharpe','max_drawdown','trades']])}

![Sensitivity](figures/sensitivity.png)

## 14. Limitations and bias review

- Look-ahead: shifted close signals, causal rolling features and lagged regimes; tested with hand-calculated gap examples and prefix invariance.
- Execution: exact next-open fills, fixed fees/slippage, no spread/order book, latency, partial fills, minimum lots or market impact.
- Selection bias: BTC is one surviving, successful asset selected in hindsight; no delisted-asset universe. One venue and USDT quote risks remain.
- Overfitting: nine validation comparisons introduce selection bias; no multiple-testing correction, walk-forward study or statistical significance claim.
- One held-out market path cannot establish generalization or profitability; dependent returns weaken standard annualized ratios.
- No financing, tax, yield on cash, live monitoring or execution. Fixed fee is an assumption, not an asserted current exchange tariff.
- Aggregate candle data cannot reconstruct intrabar paths; maximum drawdown is measured at closes, potentially understating intrabar loss.
- No Monte Carlo: intentionally deferred to keep the core verifiable.

## 15. Conclusions

{chr(10).join(conclusions)}

Inspect cost sensitivity and regime tables before interpreting aggregate returns. Even positive results here do not establish statistical evidence of an edge.
For educational and research purposes. Historical performance does not imply future results.
"""
    (out/"quant_report.md").write_text(report, encoding="utf-8")
    return {"metrics":metrics_table,"risk":risk_table,"regimes":regime_table,"selection":selection,"results":results}
