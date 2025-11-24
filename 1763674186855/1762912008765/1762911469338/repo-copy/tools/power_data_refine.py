import argparse
import pathlib

import pandas as pd
import numpy as np
from statsmodels.api import OLS, add_constant


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='input', required=True)
    parser.add_argument('--x', required=True)
    parser.add_argument('--y', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    x, y = df[args.x], df[args.y]

    # keep only positive x,y for log-log fitting
    mask_pos = (x > 0) & (y > 0)
    df = df[mask_pos].copy()
    if df.empty:
        print(f"[adaptive_refine] input=0 kept=0 removed=0")
        df.to_csv(args.out, index=False)
        return

    # Prototype model on log-log
    X = add_constant(np.log(df[args.x].values))
    model = OLS(np.log(df[args.y].values), X).fit()

    # Cook's Distance
    influence = model.get_influence()
    cooks = influence.cooks_distance[0]

    # threshold: common heuristic 4/n
    threshold = 4.0 / len(df)
    mask = cooks < threshold
    df_filtered = df[mask]

    print(f"[adaptive_refine] input={len(df)} kept={mask.sum()} removed={(~mask).sum()}")
    print(f"[adaptive_refine] mean Cook's D={cooks.mean():.4f}  threshold={threshold:.4f}")

    # re-estimate after refine
    if len(df_filtered) >= 2:
        X_refit = add_constant(np.log(df_filtered[args.x].values))
        model_refit = OLS(np.log(df_filtered[args.y].values), X_refit).fit()
        a = np.exp(model_refit.params[0])
        b = model_refit.params[1]
        print(f"[adaptive_refine] log-fit: log(y)= {model_refit.params[0]:.4f} + {b:.4f}*log(x) => y≈ {a:.4f} * x^{b:.4f}")

    df_filtered.to_csv(args.out, index=False)


if __name__ == '__main__':
    main()
