# Beyond the Sender: A Modular Framework for End-to-End Network Optimization

We will be developing a modular Mininet framework to analyze the end-to-end interactions between senders, routers, and receivers. Instead of just changing congestion control algorithm at the sender, this setup allows for "plug-and-play" testing of network behaviors, such as the active queue management (AQM) of the switches, and feedback mechansim of the receiver.

The goal is to move replicate heterogenous internet and use Linux kernel tuning to identify how cross-layer dependencies actually affect real-world performance. We will be testing these behaviors on dumbbell and star topologies, as well as with different traffic patterns, such as short bursts, constant, or elephant and mice flows. We plan to measure throughput, latency, and fairness to reach some conclusions on which parameters matter most for different configurations. This idea is an extension of the DCTCP paper, which makes certain choices for each of these points.

https://people.csail.mit.edu/alizadeh/papers/dctcp-sigcomm10.pdf
