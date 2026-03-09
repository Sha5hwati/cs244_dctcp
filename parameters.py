from enum import Enum

# TODO: add some description of each parameter.

# Common constants used by the experiment scripts.
# TODO: check if we need to change this to a parameter for run_experiment
NUM_SENDERS = 4
SWITCH_NAME = "switch1"
RECEIVER_NAME = "receiver"

# Possible topology types.
class TopologyType(Enum):
    DUMBBELL = "dumbbell"
    STAR = "star"

# Dumbbell-specific topology parameters.
class DumbbellTopologyParameters(Enum):
    BANDWIDTH = 10  # Mbps (bottleneck link)
    QUEUE_SIZE = 100
    DELAY = "100ms"
    LOSS = 0
    JITTER = "0ms"

# Star-specific topology parameters.
class StarTopologyParameters(Enum):
    BANDWIDTH = 10  # Mbps
    QUEUE_SIZE = 100
    DELAY = "1ms"
    LOSS = 0
    JITTER = "0ms"

# Possible traffic patterns.
class TrafficPattern(Enum):
    ELEPHANT_VS_MICE = 'elephant_vs_mice'
    CONSTANT = 'constant'
    BURSTY = 'bursty'

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

# Metrics that will be graphed for each experiment.
# The defined tuple of values is {key in dataframe, title in subplot}.
class Metrics(Enum):
    THROUGHPUT = ('throughput', 'Throughput (Mbps)')
    RTT = ('rtt', 'Round Trip Time (ms)')
    CONGESTION_WINDOW = ('congestion_window', 'Congestion Window (KB)')
    FAIRNESS = ('fairness_index', 'Fairness (Jain\'s Fairness Index)')
    RETRANSMITS = ('retransmits', 'Retransmissions (count)')

# List of experiments that we want to run and graph.
# Each row of the experiment table defines a scenario to run.
# TODO: update the list of scenarios
EXPERIMENT_TABLE = [
    {
        "topology": TopologyType.DUMBBELL,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.IMMEDIATE_ACK,
        "traffic": TrafficPattern.CONSTANT
    },
]