import time
from pathlib import Path
from typing import List, Union

from mininet.net import Mininet
from mininet.log import info
from parameters import CongestionControlAlgo, TrafficPattern, RECEIVER_NAME

def generate_traffic(
    net: Mininet, 
    traffic_pattern: TrafficPattern,
    num_senders: int, 
    sender_ccas: Union[CongestionControlAlgo, List[CongestionControlAlgo]], 
    log_directory: str,
) -> None:
    """Generate traffic with support for host-specific CCAs."""
    receiver = net.get(RECEIVER_NAME)
    receiver_ip = receiver.IP()
    senders = [net.get(f"sender{i+1}") for i in range(num_senders)]

    # Handle CCA mapping: Single value vs List of values
    if isinstance(sender_ccas, list):
        if len(sender_ccas) != num_senders:
            raise ValueError(f"Expected {num_senders} CCAs, got {len(sender_ccas)}")
        cc_list = [cca.value for cca in sender_ccas]
    else:
        cc_list = [sender_ccas.value] * num_senders

    # Start iperf3 servers
    for port in range(5001, 5001 + num_senders):
        receiver.cmd(f"sudo iperf3 -s -p {port} -D")

    time.sleep(1)
    info(f"Traffic pattern: {traffic_pattern.value} with CCAs: {cc_list}\n")

    log_dir = Path(log_directory)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Common logic for running iperf3 flows
    for idx, s in enumerate(senders):
        port = 5001 + idx
        cca = cc_list[idx]
        
        # Scenario: The Politeness Penalty (usually a long-lived flow test)
        # We'll use the CONSTANT pattern logic but remove the bandwidth limit (-b) 
        # to see the true throughput battle.
        if traffic_pattern == TrafficPattern.CONSTANT:
            # Note: Removed -b 5M to allow protocols to compete for full bandwidth
            s.cmd(
                f"sudo iperf3 -c {receiver_ip} -p {port} -t 20 -C {cca} "
                f"-i 0.1 -J --logfile {log_dir}/sender{idx+1}_{cca}.json &"
            )

    # Allow flows to finish and clean up servers
    time.sleep(30)
    receiver.cmd("sudo pkill iperf3")
