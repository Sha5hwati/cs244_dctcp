import matplotlib.pyplot as plt
from pathlib import Path
from parse_data import *
from parameters import Metrics, EXPERIMENT_TABLE

def generate_graphs(json_directory):
    """This function takes in a Path to a directory of iperf3 json data and generates
    several graphs from the data. """
    path = Path(json_directory)
    if not path.exists():
        print(f"Error: Directory {json_directory} does not exist.")
        return

    # Get all json files in the given directory and label each flow by filename (without .json).
    json_files = list(path.glob("*.json"))
    flow_data = {f.stem: parse_json(f) for f in json_files}
    
    # Initialize plot.
    # TODO: adjust visualization parameters as needed
    figure, axes = plt.subplots(4, 1, figsize=(10, 16), sharex=True)
    plt.subplots_adjust(hspace=0.3)
    
    # Plot each flow-specific metric in individual subplots.
    for label, data in flow_data.items():
        i = 0
        for metric in Metrics:
            if metric == Metrics.FAIRNESS:
                # Fairness is aggregated across all flows, so plot separately.
                continue
            axes[i].plot(data['time'], data[metric.value[1]], label=label, alpha=1.0)
            axes[i].set_ylabel(metric.value[2])
            # TODO: play around with style
            axes[i].grid(True, linestyle='--',alpha=0.5)
            i += 1

    # Plot fainess.
    fairness_data = calculate_fairness(list(flow_data.values()))
    # TODO: play around with style
    # We use post because the fairness index is calculated at the end of an interval.
    axes[3].step(fairness_data['time'], fairness_data[Metrics.FAIRNESS.value[1]], where='post', color='black', lw=2)
    axes[3].set_ylabel(Metrics.FAIRNESS.value[2])
    axes[3].set_ylim(0, 1.1)
    axes[3].grid(True, linestyle='--', alpha=0.5)

    axes[0].set_title(f"Scenario Graphs: {path.name}")
    axes[3].set_xlabel("Time (s)")
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
        # Find name of directory with results based on each scenario.
        directory_path = f"data/{topology.value}_{sender_cca.value}_{switch_qm.value}_{receiver_feedback.value}_{traffic_pattern.value}"
        generate_graphs(directory_path)