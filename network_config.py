from mininet.net import Mininet
from mininet.node import Host
import subprocess
import os
from enum import Enum
import topology

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


class ConfigurationManager:
    @staticmethod
    def apply(
        network_topo: Mininet, 
        switch_qm_algo: QueueManagement, 
        sender_algo: CongestionControlAlgo, 
        receiver_feedback: ReceiverFeedback):
        """
        This function applies the specified network settings to the Mininet topology.
        network_topo: The Mininet topology object containing senders, switches, and receiver.
        switch_qm_algo: The queue management scheme to apply at the bottleneck switch.
        sender_algo: The congestion control algorithm to use at the sender.
        receiver_feedback: The ACK strategy to use at the receiver.
        """
        src = network_topo.get(topology.SRC_NAME)
        dst = network_topo.get(topology.DST_NAME)

        # Apply the selected congestion control algorithm
        ConfigurationManager._apply_sender_algo(sender_algo)

        # Apply the selected queue management algorithm at the bottleneck switch.
        ConfigurationManager._apply_bottleneck_qm_algo(switch_qm_algo, src)

        # 2. Receiver Settings
        ConfigurationManager._apply_receiver_feedback(receiver_feedback, dst)

    def _apply_sender_algo(algo):
        '''
        Applies the specified congestion control algorithm at the sender.
        '''
        if not isinstance(algo, CongestionControlAlgo):
            print(f"Unsupported sender algorithm: {algo}")
            return

        # Load the kernel module for the specified congestion control algorithm.
        try:
            subprocess.check_call(['sudo', 'modprobe', f'tcp_{algo.value}'])
        except subprocess.CalledProcessError as e:
            print(f"Error applying sender algorithm {algo.value}: {e}")
            return
        
        # Set the congestion control algorithm for the sender host.
        os.system(f'sudo sysctl -w net.ipv4.tcp_congestion_control={algo.value}')


    def _apply_bottleneck_qm_algo(qm: QueueManagement, src: Host):
        '''
        Applies the specified queue management algorithm at the bottleneck switch.
        '''
        if not isinstance(qm, QueueManagement):
            print(f"Unsupported queue management algorithm: {qm}")
            return
        
        bottleneck_interface = f"{src.name}-eth1"
        # 1. Bottleneck AQM (src-eth1 is the outbound bottleneck in both topos)
        src.cmd(f'sudo tc qdisc del dev {bottleneck_interface} root')
        if qm == QueueManagement.TAILDROP:
            src.cmd(f'sudo tc qdisc add dev {bottleneck_interface} root pfifo limit 100')
        elif qm == QueueManagement.RED:
            src.cmd(f'sudo tc qdisc add dev {bottleneck_interface} root red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 probability 0.1')
        elif qm == QueueManagement.ECN:
            # RED with ECN marking enabled
            # DCTCP needs very low thresholds (e.g., min 15kb max 16kb for 10Mbps)
            src.cmd(f'sudo tc qdisc add dev {bottleneck_interface} root red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 probability 1 ecn')
            
    def _apply_receiver_feedback(receiver_feedback: ReceiverFeedback, dst: Host):
        '''
        Applies the specified ACK strategy at the receiver.
        '''
        if not isinstance(receiver_feedback, ReceiverFeedback):
            print(f"Unsupported receiver feedback strategy: {receiver_feedback}")
            return
        
        # Configure delayed ACKs or immediate ACKs based on the receiver feedback strategy.
        dst.cmd('sudo sysctl -w net.ipv4.tcp_ecn=1')
        dst.cmd('sudo sysctl -w net.ipv4.tcp_sack=1')
        quickack_val = '0' if receiver_feedback == ReceiverFeedback.DELAYED_ACK else '1'
        dst.cmd(f'sudo ip route change 10.0.0.0/8 dev dst-eth0 proto kernel scope link src {dst.IP()} quickack {quickack_val}')

