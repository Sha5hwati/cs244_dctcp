# Linux commands

## traffic control (TC)

Linux traffic control `tc` is used to configure packet scheduling and queuing disciplines (`qdiscs`) in the kernel which controls queuing, policing, and packet marking. 

We use `tc qdisc` commands to:
- remove any existing root qdisc on a bottleneck interface
- add a queue management algorithms to emulate different queuing behaviors on switches.
- replace qdiscs on sender when a particular TCP algorithm.

## What are the defaults

- Root qdisc: `pfifo_fast` / kernel default FIFO behavior (no advanced AQM or per-flow fairness).
- qdisc parameters: `pfifo` has a small default limit by packets, while advanced qdiscs like `red` or `fq_codel` have tunable thresholds and internal defaults that vary by kernel version.

Because Mininet runs virtualized namespaces, Mininet may call `tc` inside those namespaces; if you don't explicitly set a qdisc, the default applies there too.

### Mininet setup

The following `tc` commands are used in the mininet setup:

- `sudo tc qdisc replace dev <interface> root <qdisc_kind> [parameters]`: Replace the qdisc config.

- `sudo tc qdisc del dev <interface> root`. This resets the interface to the default values.

- `sudo tc qdisc add dev <interface> root <qdisc_kind> [parameters]`. Adds a new qdisc config. If one already exists, it throws an error.

See `man tc-<qdisc_kind` for the `qdisc_kind` and their corresponding parameters. (or https://man7.org/linux/man-pages/man8/tc.8.html)


These are some examples of queue management at `switches`:
- Taildrop (pfifo): `tc qdisc add dev <interface> root pfifo limit 100` — simple drop-tail FIFO queue limited to ~100 packets.
- Random Early Detaction (RED) : `tc qdisc add dev <interface> root red limit 1mb min 15kb max 20kb avpkt 1500 burst 20 probability 0.1` — configures RED with low thresholds appropriate for low-bandwidth bottlenecks.
- RED + ECN: same RED parameters but with `probability 1 ecn` or `ecn` flag to enable ECN marking so ECN-capable TCPs (like DCTCP) react to marks instead of drops. This is set in the IP layer.
- For BBR senders we replace the sender host qdisc with `fq` to enable pacing and fair queuing: `tc qdisc replace dev <interface> root fq`.

## sysctl

`sysctl` is used for more general kernel configuration changes. We use it to configure the `net.ipv4` TPC config at the endpoint (mainly the `sender`):

- `net.ipv4.tcp_ecn=1` to enable ECN support in the sender. This means that the ECN are not ignored in the packet.
- `net.ipv4.tcp_allowed_congestion_control="cubic reno dctcp bbr"` so the desired algorithms are selectable.
- `net.ipv4.tcp_ecn_fallback=0` to prevent fallback to loss-based behavior when ECN negotiation fails (important when testing DCTCP)

### Defaults

- ECN: disabled by default (kernel sysctl `net.ipv4.tcp_ecn = 0`).
- Allowed congestion-control algorithms: the kernel exposes a set of compiled algorithms in `/proc/sys/net/ipv4/tcp_allowed_congestion_control` — often just `cubic`/`reno` unless others were loaded (`dctcp`, `bbr`).
