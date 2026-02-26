# Terminologies

This document defines the key terminologies to study the Network Optimization problem which includes network topologies, traffic patterns, performance metrics, and TCP congestion control algorithms.

## Network Topologies

### Dumbbell
Multiple senders connect to one router, multiple receivers connect to another router, and the two routers are connected by a single bottleneck link.

Eg. TCP congestion control experiments

![dumbbell](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTu4QcCyR4BI9PLRJYbKWUqvPyFWiXRn-o0nw&s)

### Clos (aka Fat Tree)

A Clos topology (often implemented as a fat-tree) is a multi-stage hierarchical network with multiple equal-cost paths between nodes. The hierarchy includes leaves, aggregater, core, and edge routers.

Eg. Datacenter RPC, MapReduce-style shuffle

![clos](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRJzAfQkAd0BeY_lq1BM2B7aB4ryIeMZBjr-g&s)

### Leaf-spine

A leaf-spine topology consists of multiple leaves and all the leaves connect to spine servers.

Eg. Data centers

![leaf_spine](https://www.juniper.net/documentation/us/en/software/nce/sg-005-data-center-fabric/images/g301248.png)

### Star

A star topology is a network design where all nodes connect to a single central device (hub or switch). All communication between nodes passes through this central point.

Eg. Small LANs, Home network

![star](https://www.conceptdraw.com/How-To-Guide/picture/star-network-topology-diagram.png)

### Torus (3D Mesh)
A 3D mesh network where edges wrap around, forming a torus in each dimension.

Eg. Parallel computer, supercomputers

![torus](https://clusterdesign.org/wp-content/uploads/2012/09/fujitsu-3d-torus.jpg)


## Traffic patterns

| Pattern | Description | Example |
|---|---|---|
| Unicast | One sender → One receiver. | RPC |
| Multicast | One sender → Multiple receivers. | Video streaming, data replication |
| Incast | Multiple senders → One receiver. | Leaf-spine topologies, distributed databases |
| Elephant flows | Large, long-lived, throughput-sensitive flows. | Backups |
| Mice flows | Short, latency-sensitive flows. | RPCs |
| Short bursts | Short, sudden spikes of traffic (micro-bursts). | Bursts of RPCs or small transfers |


## Measurements

| Metric | Definition | Notes / Units |
|---|---|---|
| Throughput | Rate of successfully delivered useful data. | Typically measured in bits/sec (bps, Kbps, Mbps, Gbps). |
| Latency | One-way delay from sender to receiver. | Includes propagation, serialization, queuing, and processing delays. Queuing delay is usually dominant; measured in ms. |
| RTT (Round-Trip Time) | Time for a packet to travel from sender to receiver and back. | Approximation: RTT ≈ 2 × one-way latency for symmetric paths. Measured in ms. |
| Fairness | Degree to which competing flows share bandwidth equally. | Often quantified with metrics like Jain's fairness index; important for multi-flow scenarios. |

## Congestion Control Algorithms

| Algorithm | Type | Description & Notes |
|---|---|---|
| CUBIC | Loss-based (AIMD with cubic growth) | Uses a cubic window-growth function after loss events. Tends to push for high throughput but can cause larger queue build-up because it relies on packet loss as a congestion signal. |
| BBR (Bottleneck Bandwidth and RTT) | Model-based | Estimates bottleneck bandwidth and minimum RTT to set sending rate (approx. BtlBw × minRTT). Aims to operate at the bottleneck without filling queues, resulting in low loss and smaller queues. |
| DCTCP (Data Center TCP) | ECN-based | Uses ECN marks from switches to measure congestion; sender reduces its window proportionally to the fraction of ECN-marked packets. Provides fast, fine-grained feedback and keeps queues shallow in datacenter environments. |


## Active Queue Management (AQM)

Active Queue Management (AQM) algorithms proactively manage packet queues at routers/switches by marking or dropping packets before buffers overflow, preventing bufferbloat and improving latency and fairness.

| Algorithm | Description | Mechanism / Notes |
|---|---|---|
| RED (Random Early Detection) | Randomly drops packets when the average *queue length* exceeds a minimum threshold to signal congestion early. | Uses average queue length; probabilistic drops between min and max thresholds. WRED is an extension that drops based on traffic class. |
| CoDel (Controlled Delay) | Drops packets based on packet *queue delay* rather than queue length. | Targets maintaining low queueing delay; self-tuning to varying link rates. |
| ECN-based AQM | Marks packets with ECN instead of dropping them. | Requires ECN-capable endpoints; reduces packet loss by signalling congestion. |
| FQ-CoDel (FlowQueue-CoDel) | Combines per-flow fair queuing with CoDel delay control to provide low latency and fairness. | Per-flow queues prevent head-of-line blocking and flow domination of buffers. |
| Tail drop | Packets are accepted until the buffer is full. | Not proactive, reactive queue management and does not provide early signaling|


## Receiver feedback mechanisms

Receiver feedback is the information sent by the receiver (not switches/routers) to the sender. The receiver observes arrivals and reports signals the sender uses to adjust its congestion window, pacing, or retransmissions.

| Mechanism | Purpose / Signals | How it works / Notes |
|---|---|---|
| ACK | Confirms receipt; provides timing and delivery signals (RTT, packet arrival) | Receiver sends ACKs; sender measures ACK arrival rate, RTT, and spacing. Duplicate ACKs often indicate loss. |
| Delayed ACK | Reduce ACK traffic and moderate cwnd growth | Receiver delays ACKs (common policies: ACK every 2 packets or after a short timeout, e.g., 40 ms). Lowers reverse-path load but may interact with sender algorithms. |
| SACK (Selective ACK) | Precise loss/receipt information to speed recovery | Receiver lists received byte ranges so the sender retransmits only missing segments; improves recovery on multiple losses. |
| Receiver window (rwnd) | Flow-control signal indicating available receive buffer | Advertised in TCP header; limits sender's send window to avoid overflowing receiver buffers. |
| Explicit rate / feedback (non-TCP) | Direct congestion/rate advice from receiver or network | Some protocols or networks include explicit rate recommendations or marks (e.g., XCP-like signals, or ECN-marking interpreted as rate); requires endpoint support. |