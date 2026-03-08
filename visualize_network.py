from parameters import RECEIVER_NAME
from mininet.net import Mininet
from mininet.node import Host, Switch
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt

def host_tcp_config(host: Host) -> str:
    """TCP config for a host"""
    info = []
    # Get Congestion Control Algorithm
    cca = host.cmd('sysctl net.ipv4.tcp_congestion_control').split('=')[-1].strip()
    if cca: info.append(f"CC: {cca}")

     # Get ECN setting (0: off, 1: on, 2: enabled when requested)
    ecn = host.cmd('sysctl net.ipv4.tcp_ecn').split('=')[-1].strip()
    if ecn: info.append(f"ECN: {ecn}")
    return f"CCA: {cca}, ECN: {ecn}"

def switch_config(switch: Switch) -> str:
    """HTCP config for a switch"""
    raw_tc = switch.cmd('sudo tc -s -d qdisc show')
    # interface_name -> config map
    iface_configs = {}
    # interesting switch parameters
    interesting_red_params = ['min', 'max', 'limit', 'probability']
    interesting_pfifo_params = ['limit']
    
    raw_tc_class = switch.cmd('sudo ovs-vsctl list qos')
    print(f"Raw tc class output for {switch.name}:\n{raw_tc_class}\n")

    # 1. Parse Bandwidth from HTB Classes
    for line in raw_tc_class.split('\n'):
        print(f"Parsing class line: {line}")
        if 'htb' in line and 'rate' in line:
            parts = line.split()
            dev_idx = parts.index('dev')
            iface = parts[dev_idx + 1]
            rate_idx = parts.index('rate')
            rate = parts[rate_idx + 1]
            
            # Store the bandwidth for this interface
            iface_configs[iface] = f"BW: {rate}"

    # Standardize the output into blocks per interface
    for line in raw_tc.split('\n'):
        if 'dev' not in line or 'qdisc noqueue' in line or not line.strip():
            continue
            
        parts = line.split()
        # Find the interface name which is after 'dev' keyword
        try:
            dev_idx = parts.index('dev')
            iface_name = parts[dev_idx + 1]
        except (ValueError, IndexError):
            continue

        config_str = ""
        if 'red' in line:
            params = {p: parts[i+1] for i, p in enumerate(parts) if p in interesting_red_params}
            config_str = f"RED(min:{params.get('min','?')}, max:{params.get('max','?')}, prob:{params.get('probability','?')})"
            if 'ecn' in params:
                config_str += " ecn: 1"
            else:
                config_str += " ecn: 0"

        elif 'pfifo' in line:
            params = {p: parts[i+1] for i, p in enumerate(parts) if p in interesting_pfifo_params}
            config_str = f"TailDrop(lim:{params.get('limit','?')})"

        if config_str:
            iface_configs[iface_name] = iface_configs.get(iface_name, "") + " " + config_str

    # Format into a multi-line string for the node label
    formatted_output = "\n".join([f"{iface}: {cfg.strip()}" for iface, cfg in iface_configs.items()])
    return formatted_output if formatted_output else "No active QDiscs"

def visualize_mininet(net: Mininet, log_dir: Path) -> None:
    G = nx.Graph()
    edge_labels = {}
    node_sizes = []

    for node in net.hosts + net.switches:
        # Base config: Name and IP
        config_label = f"{node.name}\nIP: {node.IP() if hasattr(node, 'IP') else 'N/A'}"
        
        # Add TCP-specific Kernel info for Hosts
        if node in net.hosts:
            tcp_info = host_tcp_config(node)
            config_label += f"\n---\n{tcp_info}"
            if node.name == RECEIVER_NAME:
                color = 'lightcoral' 
            else:
                color = 'lightgreen'
            node_sizes.append(3000)
        else:
            # For switches, you might want to show if ECN is enabled on interfaces
            # This is a placeholder; switch config depends on your OVS/Linux Bridge setup
            q_info = switch_config(node)
            config_label += f"\n---\nQueue:\n{q_info}"
            color = 'skyblue'
            node_sizes.append(8000)
        
        G.add_node(node.name, label=config_label, color=color)

    # Add Edges
    for link in net.links:
        u, v = link.intf1.node.name, link.intf2.node.name
        G.add_edge(u, v)
        edge_labels[(u, v)] = f"{link.intf1.name} <-> {link.intf2.name}"

    # Setup Layout
    plt.figure(figsize=(14, 10))
    # Add more room between nodes with a larger k value. Seed for reproducibility.
    pos = nx.spring_layout(G, k=2, seed=42) 
    
    node_colors = [data['color'] for n, data in G.nodes(data=True)]
    labels = nx.get_node_attributes(G, 'label')

    # Draw nodes and main labels
    nx.draw(G, pos, with_labels=False, node_color=node_colors, node_size=node_sizes, edge_color='silver')
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7, font_weight='bold')
    
    # Draw interface names on the edges
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6, font_color='darkred')
    
    plt.title("Mininet Topology Visualization")
    plt.show()
    plt.savefig(str(log_dir / "mininet_topology.png"))