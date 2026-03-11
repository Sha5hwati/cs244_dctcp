import pandas as pd
import os
from pathlib import Path

def get_closeness_analysis(baseline_df, experiment_df):
    all_metrics = [
        'Avg_Throughput_Mbps', 'Throughput_CoV', 'P50_RTT_ms', 'P99_RTT_ms', 
        'Min_RTT', 'Max_RTT', 'RTT_CoV', 'Mean_Cwnd', 'Min_Cwnd', 
        'Max_Cwnd', 'Cwnd_CoV', 'FCT_s', 'Retransmissions'
    ]
    
    merged = pd.merge(baseline_df, experiment_df, on='Flow', suffixes=('_base', '_exp'))
    metric_deviations = {m: [] for m in all_metrics}

    for _, row in merged.iterrows():
        for metric in all_metrics:
            base_val, exp_val = row[f"{metric}_base"], row[f"{metric}_exp"]
            if base_val == 0:
                dev = 0 if exp_val == 0 else 1.0
            else:
                dev = abs(exp_val - base_val) / base_val
            metric_deviations[metric].append(dev)

    # Average deviation across flows
    final_devs = {m: (sum(v)/len(v)*100 if v else 999) for m, v in metric_deviations.items()}
    final_devs['overall'] = sum(final_devs.values()) / len(final_devs)
    return final_devs

def run_closeness_report(data_root, baseline_csv):
    baseline_df = pd.read_csv(baseline_csv)
    all_data = []

    for subdir in Path(data_root).iterdir():
        metrics_file = subdir / "summary_metrics.csv"
        if subdir.is_dir() and metrics_file.exists():
            res = get_closeness_analysis(baseline_df, pd.read_csv(metrics_file))
            res['directory'] = subdir.name
            all_data.append(res)

    df = pd.DataFrame(all_data)
    targets = {
        'overall': 'CLOSEST OVERALL MATCH',
        'Throughput_CoV': 'CLOSEST THROUGHPUT CoV',
        'RTT_CoV': 'CLOSEST RTT CoV',
        'Cwnd_CoV': 'CLOSEST CWND CoV'
    }

    for key, title in targets.items():
        winner_row = df.loc[df[key].idxmin()] # Minimum deviation wins
        print(f"\n{'='*30} {title} {'='*30}")
        print(f"Directory: {winner_row['directory']}")
        print(f"{'-'*75}")
        print(f"{'Metric':<25} | {'% Deviation':>15}")
        print(f"{'-'*75}")
        for m in sorted([c for c in df.columns if c not in ['directory', 'overall']]):
            print(f"{m:<25} | {winner_row[m]:>14.2f}%")
        print(f"{'-'*75}")
        print(f"{'OVERALL DEVIATION':<25} | {winner_row['overall']:>14.2f}%")

if __name__ == "__main__":
    run_closeness_report('data/all_noise_star', 'data/baseline_star/star_dctcp_ecn_immediate_ack_elephant_vs_mice/summary_metrics.csv')