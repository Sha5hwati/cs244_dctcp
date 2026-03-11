import matplotlib.pyplot as plt
from pathlib import Path
from parse_data import *
from parameters import *

def generate_graphs(json_directory):
    """This function takes in a Path to a directory of iperf3 json data and generates
    several graphs from the data. """
    path = Path(json_directory)
    if not path.exists():
        print(f"Error: Directory {json_directory} does not exist.")
        return

    # Get all json files in the given directory and label each flow by filename (without .json).
    json_files = list(path.glob("*.json"))
    raw_flows = {f.stem: parse_json(f) for f in json_files}
    summaries = {f.stem: parse_summary_stats(f) for f in json_files}
    
    # Find the global start time (the earliest 'abs_start' among all files)
    global_start = min(df['abs_start'].iloc[0] for df in raw_flows.values())
    
    # Align the time axis for every flow
    flow_data = {}
    for label, df in raw_flows.items():
        # Calculate the offset (e.g., if this started 5s after the elephant)
        offset = df['abs_start'].iloc[0] - global_start
        df['time'] = df['time'] + offset
        flow_data[label] = df

    # Metric Calculations
    bottleneck_bw = float(StarTopologyParameters.BANDWIDTH.value) if "star" in str(path) else float(DumbbellTopologyParameters.BANDWIDTH.value)
    
    summary_results = []
    for label, stats in summaries.items():
        if not stats: continue
        df = flow_data.get(label)
        tp_cov = df['throughput'].std() / df['throughput'].mean() if df is not None else 0
        p99_rtt = df['rtt'].quantile(0.99) if df is not None else 0

        summary_results.append({
            'Flow': label,
            'Avg_Throughput_Mbps': stats['avg_throughput'],
            'Throughput_CoV': tp_cov, # Variance/Stability
            'P99_RTT_ms': p99_rtt,    # Tail Latency
            'FCT_s': stats['fct'],    # Mouse Flow Success
            'Retransmissions': stats['retransmits']
        })

    # Save to CSV for easy comparison in the report
    pd.DataFrame(summary_results).to_csv(path / "summary_metrics.csv", index=False)

    # 3. Calculate Link Utilization
    aligned_tp = pd.concat([df.set_index('time')['throughput'] for df in flow_data.values()], axis=1).fillna(0)
    avg_util = aligned_tp.sum(axis=1).mean() / bottleneck_bw
    print(f"Scenario {path.name} | Utilization: {avg_util:.2%}")
    
    # Initialize plot.
    # TODO: adjust visualization parameters as needed
    figure, axes = plt.subplots(5, 1, figsize=(10, 16), sharex=True)
    plt.subplots_adjust(hspace=0.3)
    
    # Plot each flow-specific metric in individual subplots.
    for label, data in flow_data.items():
        i = 0
        for metric in Metrics:
            if metric == Metrics.FAIRNESS:
                # Fairness is aggregated across all flows, so plot separately.
                continue
            axes[i].plot(data['time'], data[metric.value[0]], label=label, alpha=1.0)
            axes[i].set_ylabel(metric.value[1])
            # TODO: play around with style
            axes[i].grid(True, linestyle='--',alpha=0.5)
            i += 1

    # Plot fainess.
    fairness_data = calculate_fairness(list(flow_data.values()))
    # TODO: play around with style
    # We use post because the fairness index is calculated at the end of an interval.
    axes[4].step(fairness_data['time'], fairness_data[Metrics.FAIRNESS.value[0]], where='post', color='black', lw=2)
    axes[4].set_ylabel(Metrics.FAIRNESS.value[1])
    axes[4].set_ylim(0, 1.1)
    axes[4].grid(True, linestyle='--', alpha=0.5)

    axes[0].set_title(f"Scenario Graphs: {path.name}")
    axes[4].set_xlabel("Time (s)")
    axes[0].legend(loc='upper right', bbox_to_anchor=(1.15, 1))

    save_path = path / "scenario_graphs.png"
    plt.savefig(save_path, bbox_inches='tight')
    print(f"Graphs saved to: {save_path}")

if __name__ == "__main__":
    for scenario in EXPERIMENT_TABLE:
        topology = scenario['topology']   
        sender_cca = scenario['cca']
        switch_qm = scenario['qm']
        receiver_feedback = scenario['feedback']
        traffic_pattern = scenario['traffic']
        g = DEFAULT_DCTCP_G
        min = DEFAULT_DCTCP_MIN
        max = DEFAULT_DCTCP_MAX
        if 'dctcp_g' in scenario:
            g = scenario['dctcp_g']
        if 'dctcp_min' in scenario:
            min = scenario['dctcp_min']
        if 'dctcp_max' in scenario:
            max = scenario['dctcp_max']
        # Find name of directory with results based on each scenario.
        directory_path = f"data/{topology.value}_{sender_cca.value}_{switch_qm.value}_{receiver_feedback.value}_{traffic_pattern.value}_g{g}_min{min}_max{max}"
        generate_graphs(directory_path)