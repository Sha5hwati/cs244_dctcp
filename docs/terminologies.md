# Terminologies

This document defines the key terminologies to study the Network Optimization problem which includes network topologies, traffic patterns, performance metrics, and TCP congestion control algorithms.

## Network Topologies

### Dumbbell
Multiple senders connect to one router, multiple receivers connect to another router, and the two routers are connected by a single bottleneck link.

Eg. TCP congestion control experiments

![dumbbell](https://www.researchgate.net/profile/Nooshin-Bigdeli/publication/228954007/figure/fig1/AS:393654268121103@1470865899241/Dumbbell-network-topology.png)

### Clos (aka Fat Tree)

A Clos topology (often implemented as a fat-tree) is a multi-stage hierarchical network with multiple equal-cost paths between nodes. The hierarchy includes leaves, aggregater, core, and edge routers.

Eg. Datacenter RPC, MapReduce-style shuffle

![clos](https://www.researchgate.net/publication/304068722/figure/fig6/AS:391340278992964@1470314201946/Fat-tree-data-center-network-topology.png)

### Leaf-spine

A leaf-spine topology consists of multiple leaves and all the leaves connect to spine servers.

Eg. Data centers

![leaf_spine](https://www.juniper.net/documentation/us/en/software/nce/sg-005-data-center-fabric/images/g301248.png)

### Star

A star topology is a network design where all nodes connect to a single central device (hub or switch). All communication between nodes passes through this central point.

Eg. Small LANs, Home network

![star](https://www.conceptdraw.com/How-To-Guide/picture/star-network-topology-diagram.png)

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

### Throughput
Rate of successfully delivered useful data (bits/sec).

### Latency
One-way delay from sender to receiver. This includes Propagation delay, serialization delay, queuing delay and processing delay. Queuing delays are usually the bottleneck.

### RTT (Round Trip Time)
Time for a packet to travel from sender to receiver, and back.

Approximation:
RTT ≈ 2 × one-way latency (in symmetric paths)

### Fairness
Degree to which competing flows share bandwidth equally.

## Congestion Control Algorithms

### CUBIC
Loss based congestion control. Sender uses AIMD with cubic growth function. Leads to higher queue build up since it waits for actual packet losses.

### BBR (Bottleneck Bandwidth and RTT)
Model based congestion control to minimize packet loss. Sender tries to estimate the bottleneck badwidth and keep track of min RTT to estimate the window size ~ Bandwidth x min RTT. Leads to low loss and small queue size.

### DCTCP (Data center TCP)
Receiver marks packets with ECN bit before the switch experiences buffer overflow. Sender reduces window proportionally to ECN-marked fraction. Leads to fast feedback loop before any packets are lost.


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