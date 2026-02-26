import os
import time
from mininet.net import Mininet
from mininet.node import Controller
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from generate_topology import MininetTopology
from configure_settings import configure_settings
from generate_traffic import generate_traffic

# TODO: check if we need to change this to a parameter for run_experiment
NUM_SENDERS = 4

def run_experiment(topology_type, sender_cca, switch_aqm, receiver_ack, traffic_pattern, log_directory):
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    mininet_topology = MininetTopology(num_senders=NUM_SENDERS, topology_type=topology_type)
    net = Mininet(topo=mininet_topology, link=TCLink, controller=Controller)
    net.start()
    # Avoid ARP request so we don't have extra delay on the first packet.
    net.staticArp()
    
    # Configure settings and generate traffic.
    configure_settings(net, sender_cca=sender_cca, switch_aqm=switch_aqm, receiver_ack=receiver_ack)
    generate_traffic(net, traffic_pattern=traffic_pattern, num_senders=NUM_SENDERS, sender_cca=sender_cca, 
                     log_directory=log_directory)

    # Kill all iperf processes and clear any mininet configurations.
    os.system('sudo pkill iperf3')
    net.stop()
    # TODO: see if this is needed.
    os.system('sudo mn -c')
    info(f"Experiment {log_directory} Complete\n")

if __name__ == '__main__':
    setLogLevel('info')
    # TODO: write a script to run experiment for multiple scenarios
    # TODO: generate log directory names for different scenarios
    run_experiment(
        topology_type='incast',
        sender_cca='dctcp', 
        switch_aqm='ecn', 
        receiver_ack='normal_ack', 
        traffic_pattern='bursty', 
        log_dir='incast_dctcp_ecn_normal_ack_bursty'
    )