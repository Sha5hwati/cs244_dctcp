import time
from pathlib import Path

from mininet.net import Mininet
from mininet.log import info
from parameters import CongestionControlAlgo, TrafficPattern, RECEIVER_NAME


def generate_traffic(
    net: Mininet, 
    traffic_pattern: TrafficPattern,
    num_senders: int, 
    sender_cca: CongestionControlAlgo, 
    log_directory: str,
) -> None:
    """Generate traffic in the Mininet topology according to the specified pattern.
    """
    receiver = net.get(RECEIVER_NAME)
    receiver_ip = receiver.IP()

    # Collect sender host objects
    senders = [net.get(f"sender{i+1}") for i in range(num_senders)]

    # Start one iperf3 server per sender on consecutive ports
    for port in range(5001, 5001 + num_senders):
        receiver.cmd(f"sudo iperf3 -s -p {port} -D")

    # Allow servers to spin up
    time.sleep(1)

    info(f"Traffic pattern: {traffic_pattern.value}\n")

    log_dir = Path(log_directory)
    log_dir.mkdir(parents=True, exist_ok=True)

    if traffic_pattern == TrafficPattern.ELEPHANT_VS_MICE:
        # One long-lived elephant flow
        senders[0].cmd(
            f"sudo iperf3 -c {receiver_ip} -p 5001 -t 15 -C {sender_cca.value} -i 0.1 -J --logfile {log_dir}/elephant.json &"
        )
        time.sleep(2)

        # Other senders produce short 'mouse' transfers (5M)
        for idx, s in enumerate(senders[1:], start=1):
            port = 5001 + idx
            s.cmd(
                f"sudo iperf3 -c {receiver_ip} -p {port} -n 20M -C {sender_cca.value} -i 0.1 -J --logfile {log_dir}/mouse_{idx-1}.json &"
            )
            time.sleep(2)

    elif traffic_pattern == TrafficPattern.CONSTANT:
        # Each sender streams at 5 Mbps for 15s
        for idx, s in enumerate(senders):
            port = 5001 + idx
            s.cmd(
                f"sudo iperf3 -c {receiver_ip} -p {port} -t 15 -b 5M -C {sender_cca.value} -i 0.1 -J --logfile {log_dir}/sender{idx+1}.json &"
            )

    elif traffic_pattern == TrafficPattern.BURSTY:
        # Bursty pattern: 2 Mbps in bursts (tunable)
        for idx, s in enumerate(senders):
            port = 5001 + idx
            s.cmd(
                f"sudo iperf3 -c {receiver_ip} -p {port} -t 15 -b 2M/20 -C {sender_cca.value} -i 0.1 -J --logfile {log_dir}/sender{idx+1}.json &"
            )

    # Allow flows to finish
    time.sleep(25)