import subprocess
from pathlib import Path

from mininet.net import Mininet
from mininet.node import OVSController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

from initialize_topology import MininetTopology, TopologyType
from configure_network import configure_network
from configure_network_dumbbell import configure_network_dumbbell
from generate_traffic import generate_traffic, TrafficPattern
from visualize_network import visualize_mininet
from configure_network import (
    CongestionControlAlgo,
    QueueManagement,
    ReceiverFeedback,
)
from parameters import NUM_SENDERS

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
    if topology_type == TopologyType.DUMBBELL:
        # if traffic_pattern == TrafficPattern.ELEPHANT_VS_MICE:
        #     sender_cca = { "sender1": sender_cca.value}
        #     sender_cca.update({f"sender{i+1}": CongestionControlAlgo.CUBIC.value for i in range(1, NUM_SENDERS)})
        # else:
        #     sender_cca = {f"sender{i+1}": sender_cca.value for i in range(NUM_SENDERS)}
        sender_cca = {f"sender{i+1}": sender_cca.value for i in range(NUM_SENDERS)}
        configure_network_dumbbell(net, sender_cca=sender_cca, switch_qm=switch_qm, receiver_feedback=receiver_feedback)
    else:
        configure_network(net, sender_cca=sender_cca, switch_qm=switch_qm, receiver_feedback=receiver_feedback)
    print_config(net)

    # Save experiment data
    distinct_ccas = sorted(list(set(sender_cca.values())))
    log_dir = Path(
        f"data/{topology_type.value}_{'_'.join(distinct_ccas)}_{switch_qm.value}_{receiver_feedback.value}_{traffic_pattern.value}_noise"
    )
    log_dir.mkdir(parents=True, exist_ok=True)

    print("Visualizing topology...")
    visualize_mininet(net, log_dir)
    
    print("Generating traffic...")
    generate_traffic(
        net,
        traffic_pattern=traffic_pattern,
        num_senders=NUM_SENDERS,
        sender_cca=sender_cca[f"sender1"],  # Assuming all senders use the same CCA for simplicity
        log_directory=str(log_dir),
    )
    print_config(net)

    # Kill all iperf processes and clear any mininet configurations.
    subprocess.run(["sudo", "pkill", "iperf3"], check=False)
    net.stop()
    # Cleanup Mininet state.
    subprocess.run(["sudo", "mn", "-c"], check=False)
    subprocess.run(["sudo", "pkill", "-9", "ovs-testcontrol"])
    info(f"\nExperiment {log_dir} Complete\n")

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