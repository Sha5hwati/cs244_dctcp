import argparse
import os
import matplotlib.pyplot as plt
from pathlib import Path

# Importing existing logic from your files
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
    args = parser.parse_args()

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
        traffic_pattern=traffic_pattern
    )
    # Find name of directory with results based on each scenario and generate graphs from results.
    # directory_path = f"data/{topology.value}_{sender_cca.value}_{switch_qm.value}_{receiver_feedback.value}_{traffic_pattern.value}"
    directory_path = "/home/shashwatishradha/cs244_dctcp/data/dumbbell_cubic_dctcp_ecn_immediate_ack_elephant_vs_mice"
    print(f"\nExperiment finished. Generating graphs in {directory_path}...")
    generate_graphs(directory_path)

if __name__ == "__main__":
    run_cli()