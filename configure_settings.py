import os
import subprocess
from enum import Enum
from mininet.net import Mininet

# Congestion control algorithm used by the sender.
class CongestionControlAlgo(Enum):
    CUBIC = 'cubic'
    RENO = 'reno'
    DCTCP = 'dctcp'
    BBR = 'bbr'

# Queue management scheme used at the bottleneck switch.
class QueueManagement(Enum):
    TAILDROP = 'taildrop'
    RED = 'red'
    ECN = 'ecn'

# Feedback strategy used by the receiver for ACKs.
class ReceiverFeedback(Enum):
    DELAYED_ACK = 'delayed_ack'
    IMMEDIATE_ACK = 'immediate_ack'


# This method configures sender, switch, and receiver settings in the Mininet topology.
# Possible sender CCAs: 'cubic', 'reno', 'dctcp', 'bbr'
# Possible switch AQMs: 'red', 'taildrop', 'ecn'
# Possible receiver ack: 'normal_ack', 'delayed_ack'
def configure_settings(net: Mininet, sender_cca: CongestionControlAlgo, switch_qm: QueueManagement, receiver_ack: ReceiverFeedback):
    receiver = net.get('receiver')
    
    # Load supported congestion control algorithms in Mininet OS.
    load_congestion_control_algo(sender_cca)

    # Configure same CCA for senders and receiver.
    # TODO: figure out if we need to configure here as well or if OS level is sufficient
    # Allow a set of algorithms so switching is possible inside namespaces.
    allowed_cc = "cubic reno dctcp bbr"
    for host in net.hosts:
        host.cmd(f'sudo sysctl -w net.ipv4.tcp_allowed_congestion_control="{allowed_cc}"')
        host.cmd(f'sudo sysctl -w net.ipv4.tcp_congestion_control={sender_cca.value}')
        print(f"Configured {host.name} with congestion control algorithm {sender_cca.value}")

        if sender_cca == CongestionControlAlgo.DCTCP:
            # TODO: change this to a parameter, since we want to be able to disable ECN as well.
            host.cmd('sudo sysctl -w net.ipv4.tcp_ecn=1')
            # TODO: This prevents DCTCP from falling back to Reno, but we may not need it.
            host.cmd('sudo sysctl -w net.ipv4.tcp_ecn_fallback=0')
        if sender_cca == CongestionControlAlgo.BBR:
            # BBR requires fair queuing scheduling so we replace the default queue scheduler with a
            # fair queuing one.
            host.cmd(f'sudo tc qdisc replace dev {host.name}-eth0 root fq')
    
    
    # Configure switch AQM by first deleting the current default buffer manager, then replacing it 
    # with a different one.
    # TODO: tune the parameters to make sure we get the results we're looking for
    for switch in net.switches:
        # Use f-strings so the switch name is interpolated correctly.
        for intf in switch.intfList():
            switch.cmd(f"tc qdisc del dev {intf.name} root 2>/dev/null")
            if switch_qm == QueueManagement.TAILDROP:
                # Limit the queue length to 100 packets.
                switch.cmd(f'sudo tc qdisc add dev {intf.name} root pfifo limit 100')
            elif switch_qm == QueueManagement.RED:
                # Start dropping packets at 15kb with 10% chance, drop all packets after 20kb. We keep the range small
                # for now to ensure we get bottlenecked, but might make it larger later.
                switch.cmd(f'sudo tc qdisc add dev {intf.name} root red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 probability 0.1')
            elif switch_qm == QueueManagement.ECN:
                # ECN will mark packets over the min threshold instead of dropping them.
                switch.cmd(f'sudo tc qdisc add dev {intf.name} root red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 ecn')
        print(f"Configured switch {switch.name} with queue management scheme {switch_qm.value}")

    if sender_cca == CongestionControlAlgo.DCTCP:
        receiver.cmd('sudo sysctl -w net.ipv4.tcp_ecn=1')
    
    # Configure receiver to either send acks immediately or delay them.
    # receiver.cmd('sudo sysctl -w net.ipv4.tcp_sack=1')
    quickack_val = 1 # default
    if receiver_ack == ReceiverFeedback.DELAYED_ACK:
        # Delayed ACKs: send an ACK for every 2 packets received.
        quickack_val = 0
        receiver.cmd('sudo sysctl -w net.ipv4.tcp_delack_min=200')
        receiver.cmd('sudo sysctl -w net.ipv4.tcp_delack_max=200')
    else:
        # Immediate ACKs: send an ACK for every packet received.
        receiver.cmd('sudo sysctl -w net.ipv4.tcp_delack_min=0')
        receiver.cmd('sudo sysctl -w net.ipv4.tcp_delack_max=0')

    receiver.cmd(f'sudo ip route change 10.0.0.0/8 dev {receiver.name}-eth0 proto kernel scope link src {receiver.IP()} quickack {quickack_val}')


def load_congestion_control_algo(algo: CongestionControlAlgo):
    '''
    Loads the kernel module for the specified congestion control algorithm if it's not already loaded.
    '''
    if not isinstance(algo, CongestionControlAlgo):
        print(f"Unsupported congestion control algorithm: {algo}")
        return

    try:
        subprocess.check_call(['sudo', 'modprobe', f'tcp_{algo.value}'])
    except subprocess.CalledProcessError as e:
        print(f"Error loading congestion control algorithm {algo.value}: {e}")
        return

    # Ensure a sensible allowed list is present inside the root namespace. Mininet hosts set this per-namespace
    # in configure_settings, but setting it here helps when the script is run outside Mininet.
    allowed_cc = "cubic reno dctcp bbr"
    try:
        subprocess.check_call(['sudo', 'sysctl', '-w', f'net.ipv4.tcp_allowed_congestion_control="{allowed_cc}"'])
    except subprocess.CalledProcessError:
        # Not fatal — per-namespace settings will still be applied to Mininet hosts.
        pass
