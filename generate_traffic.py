import time
import os
from mininet.log import info
from enum import Enum

class TrafficPattern(Enum):
    ELEPHANT_VS_MICE = 'elephant_vs_mice'
    CONSTANT = 'constant'
    BURSTY = 'bursty'


# Traffic pattern must be one of 'elephant_vs_mice', 'constant', or 'bursty'
def generate_traffic(net, traffic_pattern, num_senders, sender_cca, log_directory):
    receiver = net.get('receiver')
    receiver_ip = receiver.IP()
    senders = []
    for i in range(num_senders):
        senders.append(net.get(f'sender{i+1}'))
    
    # iperf3 only supports flow from a single client to a single server port. To
    # support flows from multiple senders, we have to open an iperf3 server on 
    # a different port for each sender.
    for port in range(5001, 5001 + num_senders):
        receiver.cmd(f'sudo iperf3 -s -p {port} -D')
    time.sleep(1)

    info(f"Generating Traffic: {traffic_pattern}\n")

    if traffic_pattern == TrafficPattern.ELEPHANT_VS_MICE:
        # We generate one long-lived (elephant) flow that will run for 15 seconds.
        senders[0].cmd(f'sudo iperf3 -c {receiver_ip} -p 5001 -t 15 -C {sender_cca.value} -J --logfile {log_directory}/elephant.json &')
        time.sleep(2)
        # For each of the other senders, send 500KB of data on a short-lived (mouse) flow.
        for i, s in enumerate(senders[1:]):
            s.cmd(f'sudo iperf3 -c {receiver_ip} -p {5002+i} -n 500K -C {sender_cca.value} -J --logfile {log_directory}/mouse_{i}.json &')

    elif traffic_pattern == TrafficPattern.CONSTANT:
        # Each sender just sends a constant stream of 5 Mbps from each sender for 15 seconds. 
        # TODO: adjust bitrate as needed if this creates too much congestion.
        for i, s in enumerate(senders):
            s.cmd(f'sudo iperf3 -c {receiver_ip} -p {5001+i} -t 15 -b 5M -C {sender_cca.value} -J --logfile {log_directory}/sender{i+1}.json &')

    elif traffic_pattern == TrafficPattern.BURSTY:
        # Each sender has a target bitrate of 2 Mbps, sending in bursts of 20 packets for 15 seconds.
        # TODO: adjust bitrate as needed if this creates too much congestion.
        for i, s in enumerate(senders):
            s.cmd(f'sudo iperf3 -c {receiver_ip} -p {5001+i} -t 15 -b 2M/20 -C {sender_cca.value} -J --logfile {log_directory}/sender{i+1}.json &')

    # Sleep 20 seconds to allow all flows to complete.
    time.sleep(20)