import pandas as pd
import os
from pathlib import Path

def get_full_analysis(baseline_df, experiment_df):
    # Metric directions: True (Higher is Better), False (Lower is Better)
    metric_configs = {
        'Avg_Throughput_Mbps': True, 'Throughput_CoV': False,
        'P50_RTT_ms': False,         'P99_RTT_ms': False,
        'Min_RTT': False,            'Max_RTT': False,
        'RTT_CoV': False,            'Mean_Cwnd': True,
        'Min_Cwnd': True,            'Max_Cwnd': True,
        'Cwnd_CoV': False,           'FCT_s': False,
        'Retransmissions': False
    }
    
    merged = pd.merge(baseline_df, experiment_df, on='Flow', suffixes=('_base', '_exp'))
    
    # Store individual metric improvements to report them later
    metric_improvements = {m: [] for m in metric_configs.keys()}

    for _, row in merged.iterrows():
        for metric, higher_is_better in metric_configs.items():
            base_val = row[f"{metric}_base"]
            exp_val = row[f"{metric}_exp"]
            if base_val == 0 and exp_val == 0:
                change = 0
            elif base_val == 0:
                change = 1.0 if higher_is_better else -1.0
            else:
                change = (exp_val - base_val) / base_val if higher_is_better else (base_val - exp_val) / base_val
            metric_improvements[metric].append(change)

    # Average across flows for each metric
    final_metrics = {m: (sum(v)/len(v)*100 if v else 0) for m, v in metric_improvements.items()}
    
    # Overall score is the average of all metric improvements
    final_metrics['overall'] = sum(final_metrics.values()) / len(final_metrics)
    return final_metrics

def run_improvement_report(data_root, baseline_csv):
    baseline_df = pd.read_csv(baseline_csv)
    all_data = []

    for subdir in Path(data_root).iterdir():
        metrics_file = subdir / "summary_metrics.csv"
        if subdir.is_dir() and metrics_file.exists():
            res = get_full_analysis(baseline_df, pd.read_csv(metrics_file))
            res['directory'] = subdir.name
            all_data.append(res)

    df = pd.DataFrame(all_data)
    winners = {
        'overall': 'OVERALL IMPROVEMENT',
        'Throughput_CoV': 'THROUGHPUT STABILITY (CoV)',
        'RTT_CoV': 'RTT STABILITY (CoV)',
        'Cwnd_CoV': 'CWND STABILITY (CoV)'
    }

    for key, title in winners.items():
        winner_row = df.loc[df[key].idxmax()]
        print(f"\n{'='*30} {title} WINNER {'='*30}")
        print(f"Directory: {winner_row['directory']}")
        print(f"{'-'*75}")
        print(f"{'Metric':<25} | {'% Improvement':>15}")
        print(f"{'-'*75}")
        # Print all metrics for this winner
        for m in sorted([c for c in df.columns if c not in ['directory', 'overall']]):
            print(f"{m:<25} | {winner_row[m]:>14.2f}%")
        print(f"{'-'*75}")
        print(f"{'OVERALL SCORE':<25} | {winner_row['overall']:>14.2f}%")

if __name__ == "__main__":
    # Ensure 'data/' directory exists
    run_improvement_report('data/all_noise_star', 'data/star_dctcp_ecn_delayed_ack_elephant_vs_mice_baseline/summary_metrics.csv')