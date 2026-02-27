import os
import time
from mininet.net import Mininet
from mininet.node import OVSController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from topology import MininetTopology, TopologyType
from configure_settings import configure_settings
from generate_traffic import generate_traffic, TrafficPattern
from configure_settings import CongestionControlAlgo, QueueManagement, ReceiverFeedback

# TODO: check if we need to change this to a parameter for run_experiment
NUM_SENDERS = 4

def run_experiment(topology_type: TopologyType, sender_cca: CongestionControlAlgo, switch_qm: QueueManagement, receiver_ack: ReceiverFeedback, traffic_pattern: TrafficPattern):
    print(f"Running Experiment with topology={topology_type}, sender_cca={sender_cca}, switch_qm={switch_qm}, receiver_ack={receiver_ack}, traffic_pattern={traffic_pattern}")

    mininet_topology = MininetTopology()
    mininet_topology.create(num_senders=NUM_SENDERS, type=topology_type)
    
    print("Starting Mininet...")
    net = Mininet(topo=mininet_topology, switch=OVSSwitch, link=TCLink, controller=OVSController)
    
    net.start()
    # Avoid ARP request so we don't have extra delay on the first packet.
    net.staticArp()
    
    # Configure settings and generate traffic.
    print("Configuring settings...")
    configure_settings(net, sender_cca=sender_cca, switch_qm=switch_qm, receiver_ack=receiver_ack)
    print_config(net)

    log_directory = f"{topology_type.value}_{sender_cca.value}_{switch_qm.value}_{receiver_ack.value}_{traffic_pattern.value}"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    print("Generating traffic...")
    generate_traffic(net, traffic_pattern=traffic_pattern, num_senders=NUM_SENDERS, sender_cca=sender_cca, 
                     log_directory=log_directory)
    print_config(net)

    # Kill all iperf processes and clear any mininet configurations.
    os.system('sudo pkill iperf3')
    net.stop()
    # TODO: see if this is needed.
    os.system('sudo mn -c')
    info(f"Experiment {log_directory} Complete\n")

def print_config(net):
    print("\n------------ Mininet Network Configuration ------------")
    for host in net.hosts:
        # Execute the sysctl command on the host
        algo = host.cmd('sysctl -n net.ipv4.tcp_congestion_control').strip()
        print(f"Host {host.name}: {algo}")
    for switch in net.switches:
        qm = switch.cmd('sudo tc qdisc show').strip()
        print(f"Switch {switch.name}: {qm}")
    receiver = net.get('receiver')
    fb = receiver.cmd('sysctl -n net.ipv4.tcp_ecn').strip()
    print(f"Receiver {receiver.name}: {fb}")
    print("------------ End of Configuration ---------------\n")
    print("\n\n\n")

if __name__ == '__main__':
    setLogLevel('info')
    # TODO: write a script to run experiment for multiple scenarios
    # TODO: generate log directory names for different scenarios
    run_experiment(
        topology_type=TopologyType.DUMBBELL,
        sender_cca=CongestionControlAlgo.DCTCP, 
        switch_qm=QueueManagement.ECN, 
        receiver_ack=ReceiverFeedback.IMMEDIATE_ACK, 
        traffic_pattern=TrafficPattern.CONSTANT,
    )