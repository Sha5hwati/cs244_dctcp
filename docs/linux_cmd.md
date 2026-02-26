# Linux commands

## traffic control (TC)

Linux traffic control `tc` is used to configure packet scheduling and queuing disciplines (`qdiscs`) in the kernel which controls queuing, policing, and packet marking. 

We use `tc qdisc` commands to:
- remove any existing root qdisc on a bottleneck interface
- add a queue management algorithms to emulate different queuing behaviors on switches.
- replace qdiscs on sender when a particular TCP algorithm.

### Defaults

- Root qdisc: `pfifo_fast` / kernel default FIFO behavior (no advanced AQM or per-flow fairness).
- qdisc parameters: `pfifo` has a small default limit by packets, while advanced qdiscs like `red` or `fq_codel` have tunable thresholds and internal defaults that vary by kernel version.

Because Mininet runs virtualized namespaces, Mininet may call `tc` inside those namespaces; if you don't explicitly set a qdisc, the default applies there too.

### Setup

The following `tc` commands are used in the mininet `queue` setup:

- `sudo tc qdisc replace dev <interface> root <qdisc_kind> [parameters]`: Replace the qdisc config.

- `sudo tc qdisc del dev <interface> root`. This resets the interface to the default values.

- `sudo tc qdisc add dev <interface> root <qdisc_kind> [parameters]`. Adds a new qdisc config. If one already exists, it throws an error.

See `man tc-<qdisc_kind>` for the `qdisc_kind` and their corresponding parameters. (or https://man7.org/linux/man-pages/man8/tc.8.html)


These are some examples of queue management at `switches`:
- Taildrop (pfifo): `tc qdisc add dev <interface> root pfifo limit 100` — simple drop-tail FIFO queue limited to ~100 packets.
- Random Early Detaction (RED) : `tc qdisc add dev <interface> root red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 probability 0.1` — configures RED with low thresholds appropriate for low-bandwidth bottlenecks.
- RED + ECN: same RED parameters but with `probability 1 ecn` or `ecn` flag to enable ECN marking so ECN-capable TCPs (like DCTCP) react to marks instead of drops. This is set in the IP layer.
- For BBR senders we replace the sender host qdisc with `fq` to enable pacing and fair queuing: `tc qdisc replace dev <interface> root fq`.

## sysctl

`sysctl` is used for more general kernel configuration changes. We use it to configure the `net.ipv4` TPC config at the endpoint (mainly the `sender`):

### Defaults

- ECN: disabled by default (kernel sysctl `net.ipv4.tcp_ecn = 0`).
- Allowed congestion-control algorithms: the kernel exposes a set of compiled algorithms in `/proc/sys/net/ipv4/tcp_allowed_congestion_control` — often just `cubic`/`reno` unless others were loaded (`dctcp`, `bbr`) using `modprobe`.

### Setup

- `net.ipv4.tcp_ecn=1` to enable ECN support in the sender. This means that the ECN are not ignored in the packet.
- `net.ipv4.tcp_allowed_congestion_control="cubic reno dctcp bbr"` so the desired algorithms are selectable.
- `net.ipv4.tcp_ecn_fallback=0` to prevent fallback to loss-based behavior when ECN negotiation fails (important when testing DCTCP)

## iperf3

`iperf` is used to measure network performance such as throughput, rtt, loss, etc.

When we generate differnt types of traffic patterns, we start collecting data about to the performance by running the iperf3 server in the background.

After the simulation ends, we kill it using `pkill iperf3`.

We use:
- `sudo iperf3 -c {receiver_ip} -p 5001 -t 15 -C {sender_cca} -J --logfile` is runs from the sender to the reciever for 15s with `sender_cca` congestion control algorithm and collects data in the logfile in json format.
- Other traffic patterns using the following iperf parameters:
  - `-n`: Number of bytes to transmit
  - `-b`: bandwidth for TCP (only UDP for IPERF 2): Set target bandwidth to n bits/sec (default 1 Mbit/sec for UDP, unlimited for TCP)
  See https://iperf.fr/iperf-doc.php for more info. 
