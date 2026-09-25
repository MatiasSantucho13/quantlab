from io import BytesIO
from zipfile import ZipFile
import numpy as np
import pandas as pd
import pytest
from src.data.validation import validate
from src.data.download import parse_archive
from src.data.loader import load, synthetic
from src.features.indicators import features
from src.strategies.momentum import Momentum
from src.strategies.mean_reversion import MeanReversion
from src.backtest.engine import run
from src.analysis.drawdown import drawdown
from src.analysis.metrics import metrics
from src.analysis.regimes import classify
from src.analysis.risk import risk
from src.experiments.parameter_sensitivity import split, experiment
from src.config import Config


def market(close, opening=None):
    close=np.array(close,dtype=float); opening=close if opening is None else np.array(opening,dtype=float)
    return pd.DataFrame({'open':opening,'high':np.maximum(opening,close),
        'low':np.minimum(opening,close),'close':close,'volume':1.},
        index=pd.date_range('2022-01-01',periods=len(close),freq='4h',tz='UTC',name='timestamp'))


def test_returns_hand_calculation():
    d=features(market([100,110,99]),2191.5,2)
    assert np.isnan(d.simple_return.iloc[0])
    np.testing.assert_allclose(d.simple_return.iloc[1:],[.1,-.1])
    np.testing.assert_allclose(d.log_return.iloc[1:],np.log([1.1,.9]))


def test_signal_delay_and_entry_gap():
    d=market([100,220,242],[100,200,220])
    r=run(d,pd.Series([1,1,0],index=d.index),100,0)
    # Buy at 200, not 100; closing information cannot capture the first gap.
    np.testing.assert_allclose(r.bars.equity,[100,110,121])
    assert r.orders.iloc[0].timestamp==d.index[1]
    assert r.orders.iloc[0].price==200


def test_old_position_receives_exit_gap():
    d=market([100,100,200],[100,100,150])
    r=run(d,pd.Series([1,0,0],index=d.index),100,0)
    np.testing.assert_allclose(r.bars.equity,[100,100,150])


def test_roundtrip_cost_and_slippage_exact():
    d=market([100,100,100]); fee=.01; slip=.02
    r=run(d,pd.Series([1,0,0],index=d.index),100,fee,slip)
    expected=100*(1-slip)*(1-fee)/((1+slip)*(1+fee))
    assert r.bars.equity.iloc[-1]==pytest.approx(expected)
    assert r.trades.iloc[0]['return']==pytest.approx(expected/100-1)
    assert r.bars.fees.sum()==pytest.approx(r.orders.fee.sum())


def test_terminal_liquidation_charges_exit():
    d=market([100,100]); r=run(d,pd.Series([1,1],index=d.index),100,.01)
    assert r.bars.equity.iloc[-1]==pytest.approx(100*.99/1.01)
    assert r.trades.terminal_exit.tolist()==[True]
    assert r.bars.units.iloc[-1]==0


def test_last_signal_has_no_effect():
    d=market([100,200,400]); a=pd.Series([0,0,0],index=d.index); b=a.copy(); b.iloc[-1]=1
    pd.testing.assert_frame_equal(run(d,a).bars,run(d,b).bars)


def test_buy_hold_exact():
    d=market([110,121],[100,110]); r=run(d,pd.Series(1,index=d.index),100,.01,benchmark=True)
    assert r.bars.equity.iloc[-1]==pytest.approx(121*.99/1.01)
    assert len(r.trades)==1


def test_drawdown_initial_peak():
    np.testing.assert_allclose(drawdown(pd.Series([90,120,80,100]),100),[-.1,0,-1/3,-1/6])


def test_known_metrics_and_equity_identity():
    d=market([110,99],[100,110]); r=run(d,pd.Series(1,index=d.index),100,0,benchmark=True)
    m=metrics(r,2)
    assert m.total_return==pytest.approx(-.01)
    assert m.annualized_return==pytest.approx(-.01)
    assert m.max_drawdown==pytest.approx(-.1)
    assert m.sharpe==pytest.approx(0,abs=1e-12)
    assert m.annualized_volatility==pytest.approx(.2)
    assert m.trades==1 and m.win_rate==0 and m.profit_factor==0
    assert (1+r.bars['return']).prod()==pytest.approx(r.bars.equity.iloc[-1]/100)
    np.testing.assert_allclose(r.bars.cash+r.bars.units*d.close,r.bars.equity)


def test_no_trade_metrics():
    d=market([100,100,100]); r=run(d,pd.Series(0,index=d.index))
    m=metrics(r,2191.5)
    assert m.total_return==0 and m.trades==0 and m.exposure==0
    assert np.isnan(m.sharpe) and np.isnan(m.win_rate) and np.isnan(m.annualized_return)


def test_momentum_signal_values():
    d=market([1,2,3,2,1]); s=Momentum(2,3).generate_signals(d)
    assert s.tolist()==[0,0,1,1,0]


def test_mean_reversion_state():
    d=market([10,10,10,5,6,10,10]); s=MeanReversion(3,1,0).generate_signals(d)
    assert s.tolist()==[0,0,0,1,1,0,0]


@pytest.mark.parametrize('strategy',[Momentum(10,50),MeanReversion()])
def test_strategy_prefix_invariance(strategy):
    d=market(100+np.sin(np.arange(400)/7)*10+np.arange(400)*.01)
    full=strategy.generate_signals(d)
    pd.testing.assert_series_equal(full.iloc[:300],strategy.generate_signals(d.iloc[:300]))
    altered=d.copy(); altered.iloc[300:,altered.columns.get_loc('close')]*=10
    pd.testing.assert_series_equal(full.iloc[:300],strategy.generate_signals(altered).iloc[:300])


def test_regime_causality():
    d=market(100+np.sin(np.arange(400)/7)*10+np.arange(400)*.01)
    labels=classify(d); other=d.copy(); other.loc[d.index[300]:,'close']*=10
    pd.testing.assert_series_equal(labels.iloc[:301],classify(other).iloc[:301])
    assert labels.iloc[:222].eq('warmup').all()
    assert not labels.iloc[250:].eq('warmup').any()


def test_split_contiguous_exhaustive():
    d=market(np.arange(500)+100); parts=split(d)
    assert [len(x) for x in parts.values()]==[300,100,100]
    pd.testing.assert_frame_equal(pd.concat(parts.values()),d)
    assert parts['train'].index.max()<parts['validation'].index.min()<parts['test'].index.min()


def test_selection_does_not_receive_test():
    d=market(100+np.arange(500)*.02+np.sin(np.arange(500)/7)*10)
    p=split(d); table,selected=experiment(p['train'],p['validation'],Config())
    assert len(table)==18 and set(table.split)=={'train','validation'}
    candidates=table[table.split=='validation'].sort_values(['sharpe','fast','slow'],ascending=[False,True,True])
    assert selected.fast==candidates.iloc[0].fast and selected.slow==candidates.iloc[0].slow


@pytest.mark.parametrize('fault',['duplicate','gap','nan','negative','bounds','infinite'])
def test_bad_data_rejected(fault):
    d=market([100,101,102]).reset_index()
    if fault=='duplicate': d.loc[1,'timestamp']=d.loc[0,'timestamp']
    elif fault=='gap': d=d.drop(1)
    elif fault=='nan': d.loc[1,'close']=np.nan
    elif fault=='negative': d.loc[1,'volume']=-1
    elif fault=='bounds': d.loc[1,'high']=1
    else: d.loc[1,'close']=np.inf
    with pytest.raises(ValueError): validate(d)


def test_sorting_and_schema():
    raw=market([100,101,102]).reset_index().iloc[::-1]
    d,q=validate(raw)
    assert d.index.is_monotonic_increasing and q['input_sorted'] is False
    with pytest.raises(ValueError): validate(raw.drop(columns='volume'))


@pytest.mark.parametrize('unit',['ms','us'])
def test_archive_timestamp_units(unit):
    stamp=pd.Timestamp('2024-01-01',tz='UTC').value//(10**6 if unit=='ms' else 10**3)
    raw=f'{stamp},100,110,90,105,10,0,0,0,0,0,0\n'.encode()
    stream=BytesIO()
    with ZipFile(stream,'w') as z: z.writestr('test.csv',raw)
    d=parse_archive(stream.getvalue())
    assert d.timestamp.iloc[0]==pd.Timestamp('2024-01-01',tz='UTC')


def test_fallback_labeled_and_reproducible(tmp_path):
    a=synthetic(tmp_path/'a.csv',n=500); b=synthetic(tmp_path/'b.csv',n=500)
    assert a.read_bytes()==b.read_bytes()
    d,q,m=load(a)
    assert 'SYNTHETIC' in m['kind'] and q['rows']==500


def test_risk_known_quantile():
    d=market([100,90,81],[100,100,90]); r=run(d,pd.Series(1,index=d.index),100,0,benchmark=True)
    v=risk(r)
    assert v['bar_var95_loss']==pytest.approx(.1)
    assert v['bar_expected_shortfall95_loss']==pytest.approx(.1)
    assert v['worst_bar']==pytest.approx(-.1)


@pytest.mark.parametrize('fee,slip',[(-.1,0),(1,0),(0,-1),(float('nan'),0),(0,float('inf'))])
def test_invalid_costs(fee,slip):
    d=market([100,100])
    with pytest.raises(ValueError): run(d,pd.Series(0,index=d.index),fee=fee,slippage=slip)
