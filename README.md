# cs244_dctcp

Implementation of "Beyond the Sender: A Modular Framework for End-to-End Network Optimization" to experiment with different congestion control, queue management, and receiver feedback to measure network performance in dumbbell and star topologies.

## Run

In the vm with mininet, run in interactive mode with:

```
sudo python3 experiment_cli.py -h [To get the available options]

sudo python3 experiment_cli.py --topology star --traffic elephant_vs_mice --cca dctcp --qm ecn --feedback immediate_ack [Example scenario]
```

This will run the given experiment scenario and generate relevant graphs.

To run multiple scenarios:

(1) Update EXPERIMENT_TABLE in `parameters.py` with the desired list of scenarios.

(2) Run `sudo python3 run_multiple_scenarios.py` to get results for all scenarios.

(3) Run `sudo python3 generate_graphs.py` to generate graphs for each scenario.

## Use a modified DCTCP kernel module

To run with a custom DCTCP congestion control algorithm (one of the dctcp_v* CCAs):

(1) Make sure the module is not already installed in the kernel by running `sudo rmmod -f dctcp_v1`.

(2) Build the .ko module by running `make`.

(3) Install the module with `sudo insmod dctcp_v1.ko`.

(4) Run `sudo sysctl net.ipv4.tcp_available_congestion_control`; `dctcp_v1` should appear in the list if successfully installed.