import os
import subprocess

@staticmethod
# This method configures sender, switch, and receiver settings in the Mininet topology.
# Possible sender CCAs: 'cubic', 'reno', 'dctcp', 'bbr'
# Possible switch AQMs: 'red', 'taildrop', 'ecn'
# Possible receiver ack: 'normal_ack', 'delayed_ack'
def configure_settings(net, sender_cca, switch_aqm, receiver_ack):
    switch1 = net.get('switch1')
    receiver = net.get('receiver')
    default_ccas = ['cubic', 'reno']

    # If the CCA is not loaded by default, we need to explicitly load the Kernel module in.
    if sender_cca not in default_ccas:
        subprocess.call(['sudo', 'modprobe', f'tcp_{sender_cca}'])
        # The OS also needs to allow the senders to use this CCA.
        os.system(f'sudo sysctl -w net.ipv4.tcp_allowed_congestion_control="cubic reno {sender_cca}"')

    # Configure same CCA for senders and receiver.
    # TODO: figure out if we need to configure here as well or if OS level is sufficient
    for host in net.hosts:
        host.cmd(f'sudo sysctl -w net.ipv4.tcp_allowed_congestion_control="cubic reno {sender_cca}"')
        host.cmd(f'sudo sysctl -w net.ipv4.tcp_congestion_control={sender_cca}')
        # TODO: change this to a parameter, since we want to be able to disable ECN as well.
        host.cmd('sudo sysctl -w net.ipv4.tcp_ecn=1')
        # TODO: This prevents DCTCP from falling back to Reno, but we may not need it.
        host.cmd('sudo sysctl -w net.ipv4.tcp_ecn_fallback=0')
        if sender_cca == 'bbr':
            # BBR requires fair queuing scheduling so we replace the default queue scheduler with a
            # fair queuing one.
            host.cmd(f'sudo tc qdisc replace dev {host.name}-eth0 root fq')
    
    # Configure switch AQM by first deleting the current default buffer manager, then replacing it 
    # with a different one.
    # TODO: tune the parameters to make sure we get the results we're looking for
    switch1.cmd('sudo tc qdisc del dev s1-eth1 root')
    if switch_aqm == 'taildrop':
        # Limit the queue length to 100 packets.
        switch1.cmd('sudo tc qdisc add dev s1-eth1 root pfifo limit 100')
    elif switch_aqm == 'red':
        # Start dropping packets at 15kb with 10% chance, drop all packets after 20kb. We keep the range small
        # for now to ensure we get bottlenecked, but might make it larger later.
        switch1.cmd('sudo tc qdisc add dev s1-eth1 root red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 probability 0.1')
    elif switch_aqm == 'ecn':
        # ECN will mark all packets over the min threshold of 15kb and doesn't actually drop them, so we can set
        # probability to 100%.
        switch1.cmd('sudo tc qdisc add dev s1-eth1 root red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 probability 1 ecn')

    # Configure receiver to either send acks immediately or delay them.
    receiver.cmd('sudo sysctl -w net.ipv4.tcp_ecn=1')
    receiver.cmd('sudo sysctl -w net.ipv4.tcp_sack=1')
    quickack_val = '0' if receiver_ack == 'delayed_ack' else '1'
    receiver.cmd(f'sudo ip route change 10.0.0.0/8 dev dst-eth0 proto kernel scope link src {receiver.IP()} quickack {quickack_val}')

