import subprocess
from parameters import CongestionControlAlgo, ReceiverFeedback, QueueManagement, SWITCH_NAME, RECEIVER_NAME
from mininet.net import Mininet

def configure_network_dumbbell(
    net: Mininet,
    sender_cca: dict[str, CongestionControlAlgo],
    switch_qm: QueueManagement,
    receiver_feedback: ReceiverFeedback,
) -> None:
    """Configure CC algorithm, switch QM and receiver ACK strategies inside Mininet.

    This function applies per-namespace sysctls and `tc` qdisc settings for all hosts and
    switches in Mininet.
    """

    receiver = net.get(RECEIVER_NAME)
    sender_cca = {name: cca for name, cca in sender_cca.items()}
    
    sender_cca_str = ", ".join(f"{name}: {cca}" for name, cca in sender_cca.items())
    print(f"Setup: CCA={sender_cca_str}, switch QM={switch_qm.value}, receiver FEEDBACK={receiver_feedback.value}")

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
        
        cca = sender_cca.get(host.name, "NA")  # default to cubic if not specified
        if cca == "NA":
            print(f"Warning: No CCA specified for {host.name}, defaulting to cubic")
            cca = "cubic"
        host.cmd(f"sudo sysctl -w net.ipv4.tcp_congestion_control={cca}")
        print(f"Configured {host.name} with congestion control algorithm {cca}")

        # Disable GRO/LRO so the kernel sees every individual ACK
        host.cmd(f"ethtool -K {host.name}-eth0 gro off lro off")

        # Additional settings for specific CCAs.
        # Cubic and Reno should work well with default settings.
        if cca == CongestionControlAlgo.DCTCP:
            # Enable ECN and disable fallback to loss-based behavior for DCTCP experiments.
            host.cmd("sudo sysctl -w net.ipv4.tcp_ecn=1")
            host.cmd("sudo sysctl -w net.ipv4.tcp_ecn_fallback=0")

        if cca == CongestionControlAlgo.BBR:
            # BBR benefits from fair queuing / pacing on the sender interface.
            host.cmd(f"sudo tc qdisc replace dev {host.name}-eth0 root fq")
            
        if cca == CongestionControlAlgo.CUBIC:
            # Cubic can be bursty, so we enable pacing to smooth out bursts.
            host.cmd(f"sudo tc qdisc replace dev {host.name}-eth0 root fq pacing")
            # Ensure ECN is in 'selective' mode (1) or off (0) for pure loss-based CUBIC
            # Usually, CUBIC experiments use ECN=0 to test tail-drop behavior.
            host.cmd("sudo sysctl -w net.ipv4.tcp_ecn=0")


    # Configure switch QM on all switch interfaces. We iterate interfaces explicitly
    # to avoid assumptions about eth indexes (e.g., avoid hardcoding "-eth1").
    for switch in net.switches:
        print(f"Configuring switch {switch.name} with queue management scheme {switch_qm.value}...")
        for intf in switch.intfList():
            if intf.name == 'lo':
                continue

            # ECN will mark packets over the min threshold instead of dropping them.
            print(f"--- Attempting to configure {intf.name} with QM {switch_qm.value}")
        
            # Clear everything for the interface.
            cmd = switch.cmd(f"sudo tc qdisc del dev {intf.name} root")
            # Add HTB structure with 1000Mbit bandwidth to ensure we can fully utilize the link
            cmd1 = switch.cmd(f"sudo tc qdisc add dev {intf.name} root handle 5: htb default 1")
            cmd2 = switch.cmd(f"sudo tc class add dev {intf.name} parent 5: classid 5:1 htb rate 1000Mbit")
            
            cmd3 = ""
            if intf.name == 'switch1-eth1' or intf.name == 'switch2-eth1':
                print(f"--- Configuring bottleneck interface {intf.name} with bandwidth 1000Mbit and delay 10ms")
                cmd3 = switch.cmd(f"sudo tc qdisc add dev {intf.name} parent 5:1 handle 10: netem delay 10ms")
            # elif 'switch1' in intf.name:
            #     print(f"--- Configuring non-bottleneck interface {intf.name} with bandwidth 1000Mbit and delay 2ms")
            #     cmd3 = switch.cmd(f"sudo tc qdisc add dev {intf.name} parent 5:1 handle 10: netem delay 2ms")
            
            for cmd in [cmd, cmd1, cmd2, cmd3]:
                if cmd.strip():
                    print(f"--- Error: could not configure root qdisc on {intf.name}: {cmd.strip()}")

            if switch_qm == QueueManagement.TAILDROP:
                # Limit the queue length to 100 packets.
                cmd = switch.cmd(f"sudo tc qdisc add dev {intf.name} parent 10: handle 20: pfifo limit 200")
                
                if cmd.strip():
                    print(f"--- Error: could not configure TAILDROP on {intf.name}: {cmd.strip()}")
            
            elif switch_qm == QueueManagement.RED:
                
                # Start dropping packets at 15kb with 10% chance, drop all packets after 20kb. We keep the range small
                # for now to ensure we get bottlenecked, but might make it larger later.
                cmd = switch.cmd(f'sudo tc qdisc replace dev {intf.name} parent 10: handle 20: red limit 1mb min 15kb '
                           'max 20kb avpkt 1500 burst 20 probability 0.1 bandwidth 1000Mbit")')
                
                # Check if command succeeded and print any errors to console. 
                if cmd.strip():
                    print(f"--- Error: could not configure RED on {intf.name}: {cmd.strip()}")

            elif switch_qm == QueueManagement.ECN:
                
                 
                # Setup ECN marking with RED parameters. 
                # We use a small range for min and max thresholds to ensure we get bottlenecked and see ECN in action.
                cmd = switch.cmd(f"sudo tc qdisc add dev {intf.name} parent 5:1 handle 10: red "
                                f"limit 1mb min 30kb max 90kb avpkt 1500 burst 25 probability 1.0 ecn bandwidth 1000Mbit")
                
                # Check if command succeeded and print any errors to console. 
                if cmd.strip():
                    print(f"--- Error: could not configure ECN on {intf.name}: {cmd.strip()}")

        print(f"Configured switch {switch.name} with queue management scheme {switch_qm.value}")

    if switch_qm == QueueManagement.ECN:
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
