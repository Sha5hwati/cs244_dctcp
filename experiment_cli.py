import argparse
import os
import matplotlib.pyplot as plt
from pathlib import Path

from run_experiment import run_experiment
from generate_graphs import generate_graphs
from parameters import *

def run_cli():
    parser = argparse.ArgumentParser(description='Runs a single experiment scenario and generates graphs for the scenario.')
    
    # Map command line strings to your Enum types
    parser.add_argument('--topology', type=str, default='dumbbell', choices=[topology.value for topology in TopologyType], help='Topology Type')
    parser.add_argument('--traffic', type=str, default='constant', choices=[traffic_pattern.value for traffic_pattern in TrafficPattern], help='Traffic Pattern')
    parser.add_argument('--cca', type=str, default='cubic', choices=[cca.value for cca in CongestionControlAlgo], help='Congestion Control Algorithm')
    parser.add_argument('--qm', type=str, default='taildrop', choices=[qm.value for qm in QueueManagement], help='Queue Management')
    parser.add_argument('--feedback', type=str, default='immediate_ack', choices=[feedback.value for feedback in ReceiverFeedback], help='Receiver Feedback')
    parser.add_argument('--directory_path', type=str, default='', help='Optional directory path. If provided, the data in directory path will be analyzed')
    parser.add_argument('--dctcp_g', type=int, default=DEFAULT_DCTCP_G, help='Optional g value for DCTCP.')
    parser.add_argument('--dctcp_min', type=int, default=DEFAULT_DCTCP_MIN, help='Optional min value for DCTCP.')
    parser.add_argument('--dctcp_max', type=int, default=DEFAULT_DCTCP_MAX, help='Optional max value for DCTCP.')
    args = parser.parse_args()

    if args.directory_path:
        print(f"Analyzing data for directory path {args.directory_path}...")
        generate_graphs(args.directory_path)
        return

    try:
        topology = TopologyType(args.topology)
        traffic_pattern = TrafficPattern(args.traffic)
        sender_cca = CongestionControlAlgo(args.cca)
        switch_qm = QueueManagement(args.qm)
        receiver_feedback = ReceiverFeedback(args.feedback)
    except:
        print("Invalid arguments. Terminating early.")
        return
    

    # Start in clean slate.
    print("Cleaning up Mininet...")
    os.system('sudo mn -c')
    os.system('sudo pkill -9 ovs-testcontrol')


    run_experiment(
        topology_type=topology,
        sender_cca=sender_cca,
        switch_qm=switch_qm,
        receiver_feedback=receiver_feedback,
        traffic_pattern=traffic_pattern,
        dctcp_g=args.dctcp_g,
        dctcp_min=args.dctcp_min,
        dctcp_max=args.dctcp_max,
    )
    # Find name of directory with results based on each scenario and generate graphs from results.
    directory_path = f"data/{topology.value}_{sender_cca.value}_{switch_qm.value}_{receiver_feedback.value}_{traffic_pattern.value}_g{args.dctcp_g}_min{args.dctcp_min}_max{args.dctcp_max}"
    print(f"\nExperiment finished. Generating graphs in {directory_path}...")
    generate_graphs(directory_path)

if __name__ == "__main__":
    run_cli()