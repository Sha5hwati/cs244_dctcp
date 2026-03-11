import pandas as pd
import sys
import os

def compare_and_print(file_old, file_new):
    if not (os.path.exists(file_old) and os.path.exists(file_new)):
        print("Error: One or both files not found.")
        return

    # Load and align
    old = pd.read_csv(file_old).set_index('Flow')
    new = pd.read_csv(file_new).set_index('Flow')
    
    # Calculate Percent Change
    pct_change = ((new - old) / old) * 100
    
    # Logic categorization
    higher_is_better = ['Avg_Throughput_Mbps', 'Mean_Cwnd', 'Min_Cwnd', 'Max_Cwnd']
    lower_is_better = [
        'Throughput_CoV', 'P50_RTT_ms', 'P99_RTT_ms', 'Min_RTT', 
        'Max_RTT', 'RTT_CoV', 'Cwnd_CoV', 'FCT_s', 'Retransmissions'
    ]
    
    improvements = []
    regressions = []
    
    for flow in pct_change.index:
        for metric in pct_change.columns:
            val = pct_change.loc[flow, metric]
            
            # Skip if there's no change or data is missing
            if pd.isna(val) or val == 0:
                continue
            
            is_improvement = False
            if metric in higher_is_better:
                is_improvement = (val > 0)
            elif metric in lower_is_better:
                is_improvement = (val < 0)
            
            row = {'Flow': flow, 'Metric': metric, 'Change (%)': round(val, 2)}
            if is_improvement:
                improvements.append(row)
            else:
                regressions.append(row)

    # Print Results
    print("\n" + "="*45)
    print(f"{'IMPROVEMENTS':^45}")
    print("="*45)
    if improvements:
        print(pd.DataFrame(improvements).to_string(index=False))
    else:
        print("No improvements detected.")

    print("\n" + "="*45)
    print(f"{'REGRESSIONS':^45}")
    print("="*45)
    if regressions:
        print(pd.DataFrame(regressions).to_string(index=False))
    else:
        print("No regressions detected.")

if __name__ == "__main__":
    old_path = 'data/packet_loss_star/star_dctcp_ecn_immediate_ack_elephant_vs_mice_baseline/summary_metrics.csv'
    new_path = 'data/packet_loss_star/star_dctcp_ecn_immediate_ack_elephant_vs_mice/summary_metrics.csv'
    print('Path A: ', old_path)
    print('Path B: ', new_path)
    compare_and_print(old_path, new_path)