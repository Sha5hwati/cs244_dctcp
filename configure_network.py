import os
import subprocess
from parameters import CongestionControlAlgo, ReceiverFeedback, QueueManagement, SWITCH_NAME, RECEIVER_NAME
from mininet.net import Mininet

def configure_network(
    net: Mininet,
    sender_cca: CongestionControlAlgo,
    switch_qm: QueueManagement,
    receiver_feedback: ReceiverFeedback,
) -> None:
    """Configure CC algorithm, switch QM and receiver ACK strategies inside Mininet.

    This function applies per-namespace sysctls and `tc` qdisc settings for all hosts and
    switches in Mininet.
    """

    receiver = net.get(RECEIVER_NAME)
    print(f"Setup: CCA={sender_cca.value}, switch QM={switch_qm.value}, receiver FEEDBACK={receiver_feedback.value}")

    # Configure same CCA for senders and receiver.
    # TODO: figure out if we need to configure here as well or if OS level is sufficient
    # Allow a set of algorithms so switching is possible inside namespaces.
    allowed_cc = "cubic reno dctcp bbr"

    for host in net.hosts:
        # Enable the allowed set and select the desired algorithm.
        try:
            host.cmd(f"sudo sysctl -w net.ipv4.tcp_available_congestion_control=\"{allowed_cc}\"")
        except subprocess.CalledProcessError as e:
            print(f"Error loading congestion control algorithm {allowed_cc}: {e}")
            return
        host.cmd(f"sudo sysctl -w net.ipv4.tcp_allowed_congestion_control=\"{allowed_cc}\"")
        host.cmd(f"sudo sysctl -w net.ipv4.tcp_congestion_control={sender_cca.value}")
        print(f"Configured {host.name} with congestion control algorithm {sender_cca.value}")

        if sender_cca == CongestionControlAlgo.DCTCP:
            # Enable ECN and disable fallback to loss-based behavior for DCTCP experiments.
            host.cmd("sudo sysctl -w net.ipv4.tcp_ecn=1")
            host.cmd("sudo sysctl -w net.ipv4.tcp_ecn_fallback=0")

        if sender_cca == CongestionControlAlgo.BBR:
            # BBR benefits from fair queuing / pacing on the sender interface.
            host.cmd(f"sudo tc qdisc replace dev {host.name}-eth0 root fq")

    # Configure switch QM on all switch interfaces. We iterate interfaces explicitly
    # to avoid assumptions about eth indexes (e.g., avoid hardcoding "-eth1").
    for switch in net.switches:
        for intf in switch.intfList():
            # Remove any existing root qdisc (ignore errors)
            switch.cmd(f"sudo tc qdisc del dev {intf.name} root 2>/dev/null || true")

            if switch_qm == QueueManagement.TAILDROP:
                # Limit the queue length to 100 packets.
                switch.cmd(f"sudo tc qdisc add dev {intf.name} root pfifo limit 100")
            elif switch_qm == QueueManagement.RED:
                # Start dropping packets at 15kb with 10% chance, drop all packets after 20kb. We keep the range small
                # for now to ensure we get bottlenecked, but might make it larger later.
                switch.cmd(f'sudo tc qdisc add dev {intf.name} root red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 probability 0.1')
            elif switch_qm == QueueManagement.ECN:
                # ECN will mark packets over the min threshold instead of dropping them.
                switch.cmd(f'sudo tc qdisc add dev {intf.name} root 1:10 handle 20: red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 probability 1.0 ecn')
        print(f"Configured switch {switch.name} with queue management scheme {switch_qm.value}")

    if sender_cca == CongestionControlAlgo.DCTCP:
        receiver.cmd('sudo sysctl -w net.ipv4.tcp_ecn=1')
    
    # Configure receiver to either send acks immediately or delay them.
    # receiver.cmd('sudo sysctl -w net.ipv4.tcp_sack=1')
    quickack_val = 1 # default
    if receiver_feedback == ReceiverFeedback.DELAYED_ACK:
        quickack_val = 0
        receiver.cmd("sudo sysctl -w net.ipv4.tcp_delack_min=200")
        receiver.cmd("sudo sysctl -w net.ipv4.tcp_delack_max=200")
    else:
        receiver.cmd("sudo sysctl -w net.ipv4.tcp_delack_min=0")
        receiver.cmd("sudo sysctl -w net.ipv4.tcp_delack_max=0")

    receiver.cmd(
        f"sudo ip route change 10.0.0.0/8 dev {receiver.name}-eth0 proto kernel scope link src {receiver.IP()} quickack {quickack_val}"
    )
