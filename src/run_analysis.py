"""Run the complete offline research pipeline."""
import argparse
from pathlib import Path
from .config import Config
from .data.loader import load, synthetic
from .reporting.report import generate

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data",default="data/raw/btcusdt_4h.csv")
    p.add_argument("--output",default="reports")
    p.add_argument("--cost",type=float,default=.001)
    p.add_argument("--slippage",type=float,default=0.)
    p.add_argument("--synthetic",action="store_true",help="Explicit engineering fixture; never historical BTC")
    a=p.parse_args()
    path=synthetic("data/raw/synthetic_4h.csv") if a.synthetic else Path(a.data)
    if not path.exists(): p.error("Dataset missing. Run python -m src.data.download or explicitly use --synthetic")
    data,quality,metadata=load(path)
    result=generate(data,quality,metadata,Config(fee=a.cost,slippage=a.slippage),a.output)
    print(f"Dataset: {metadata['kind']}; {len(data)} bars")
    print(f"Selected: {result['selection']['parameters']}")
    print(f"Report: {Path(a.output)/'quant_report.md'}")

if __name__=="__main__": main()
