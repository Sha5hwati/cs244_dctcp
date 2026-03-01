import subprocess
from pathlib import Path

from mininet.net import Mininet
from mininet.node import OVSController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

from initialize_topology import MininetTopology, TopologyType
from configure_network import configure_network
from generate_traffic import generate_traffic, TrafficPattern
from configure_network import (
    CongestionControlAlgo,
    QueueManagement,
    ReceiverFeedback,
)

# TODO: check if we need to change this to a parameter for run_experiment
NUM_SENDERS = 4

def run_experiment(
    topology_type: TopologyType,
    sender_cca: CongestionControlAlgo,
    switch_qm: QueueManagement,
    receiver_feedback: ReceiverFeedback,
    traffic_pattern: TrafficPattern,
) -> None:
    """Create a Mininet topology, apply settings, run traffic, and collect logs.

    The experiment writes logs to data/<topo>_<cca>_<qm>_<ack>_<pattern>.
    """

    print(
        f"Running experiment: topology={topology_type.value} "
        f"cca={sender_cca.value} qm={switch_qm.value} "
        f"feedback={receiver_feedback.value} pattern={traffic_pattern.value}"
    )

    topo = MininetTopology()
    topo.create(num_senders=NUM_SENDERS, type=topology_type)

    print("Starting Mininet...")
    net = Mininet(topo=topo, switch=OVSSwitch, link=TCLink, controller=OVSController)
    net.start()
    # Avoid ARP requests so we don't have extra delay on the first packet.
    net.staticArp()
    print("Mininet started successfully\n\n")

    # Configure devices in the topology.
    print("Configuring network...")
    configure_network(net, sender_cca=sender_cca, switch_qm=switch_qm, receiver_feedback=receiver_feedback)
    print_config(net)

    # Generate traffic.
    print("Generating traffic...")
    log_exp = Path(
        f"data/{topology_type.value}_{sender_cca.value}_{switch_qm.value}_{receiver_feedback.value}_{traffic_pattern.value}"
    )
    log_exp.mkdir(parents=True, exist_ok=True)
    generate_traffic(
        net,
        traffic_pattern=traffic_pattern,
        num_senders=NUM_SENDERS,
        sender_cca=sender_cca,
        log_directory=str(log_exp),
    )
    print_config(net)

    # Kill all iperf processes and clear any mininet configurations.
    subprocess.run(["sudo", "pkill", "iperf3"], check=False)
    net.stop()
    # Cleanup Mininet state.
    subprocess.run(["sudo", "mn", "-c"], check=False)
    info(f"Experiment {log_exp} Complete\n")

def print_config(net):
    print("\n\n------------ Mininet Network Configuration ------------")
    for host in net.hosts:
        algo = host.cmd("sysctl -n net.ipv4.tcp_congestion_control").strip()
        print(f"Host {host.name}: {algo}")

    for switch in net.switches:
        qm = switch.cmd("sudo tc qdisc show").strip()
        print(f"Switch {switch.name}: {qm}")

    receiver = net.get("receiver")
    fb = receiver.cmd("sysctl -n net.ipv4.tcp_ecn").strip()
    print(f"Receiver {receiver.name}: tcp_ecn={fb}")
    print("------------ End of Configuration ---------------\n\n")

# TODO: remove this once we finish run_multiple_scenarios.py
# if __name__ == '__main__':
#     setLogLevel('info')
#     # TODO: write a script to run experiment for multiple scenarios
#     run_experiment(
#         topology_type=TopologyType.DUMBBELL,
#         sender_cca=CongestionControlAlgo.DCTCP, 
#         switch_qm=QueueManagement.ECN, 
#         receiver_feedback=ReceiverFeedback.IMMEDIATE_ACK, 
#         traffic_pattern=TrafficPattern.CONSTANT,
#     )