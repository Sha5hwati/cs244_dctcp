from enum import Enum

# TODO: add some description of each parameter.

# Common constants used by the experiment scripts.
# TODO: check if we need to change this to a parameter for run_experiment
NUM_SENDERS = 4
SWITCH_NAME = "switch1"
RECEIVER_NAME = "receiver"
# K must be greater than 17 KB for star BDP value; we might change this.
DEFAULT_DCTCP_MIN = 30
DEFAULT_DCTCP_MAX = 31
DEFAULT_DCTCP_G = 4

# Possible topology types.
class TopologyType(Enum):
    DUMBBELL = "dumbbell"
    STAR = "star"

# Dumbbell-specific topology parameters.
class DumbbellTopologyParameters(Enum):
    BANDWIDTH = 950  # Mbps (bottleneck link)
    QUEUE_SIZE = 500
    DELAY = "10ms" # For 20ms RTT
    LOSS = 0
    JITTER = "0ms"

# Star-specific topology parameters.
class StarTopologyParameters(Enum):
    BANDWIDTH = 950  # Mbps
    QUEUE_SIZE = 100
    DELAY = "500us" # For 1ms RTT
    LOSS = 0.1
    JITTER = "200us"

# Possible traffic patterns.
class TrafficPattern(Enum):
    ELEPHANT_VS_MICE = 'elephant_vs_mice'
    INCAST = 'incast'
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
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.DELAYED_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": DEFAULT_DCTCP_G,
        "dctcp_min": DEFAULT_DCTCP_MIN,
        "dctcp_max": DEFAULT_DCTCP_MAX,
    },
    {
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.DELAYED_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": 6,
        "dctcp_min": DEFAULT_DCTCP_MIN,
        "dctcp_max": DEFAULT_DCTCP_MAX,
    },
    {
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.DELAYED_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": 7,
        "dctcp_min": DEFAULT_DCTCP_MIN,
        "dctcp_max": DEFAULT_DCTCP_MAX,
    },
    {
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.IMMEDIATE_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": 5,
        "dctcp_min": DEFAULT_DCTCP_MIN,
        "dctcp_max": DEFAULT_DCTCP_MAX,
    },
    {
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.DELAYED_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": DEFAULT_DCTCP_G,
        "dctcp_min": 40,
        "dctcp_max": 41,
    },
    {
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.DELAYED_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": 6,
        "dctcp_min": 40,
        "dctcp_max": 41,
    },
    {
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.DELAYED_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": 5,
        "dctcp_min": 30,
        "dctcp_max": 60,
    },
    {
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.DELAYED_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": DEFAULT_DCTCP_G,
        "dctcp_min": 30,
        "dctcp_max": 150,
    },
    {
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.DELAYED_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": 5,
        "dctcp_min": 120,
        "dctcp_max": 121,
    },
    {
        "topology": TopologyType.STAR,
        "cca": CongestionControlAlgo.DCTCP,
        "qm": QueueManagement.ECN,
        "feedback": ReceiverFeedback.DELAYED_ACK,
        "traffic": TrafficPattern.ELEPHANT_VS_MICE,
        "dctcp_g": DEFAULT_DCTCP_G,
        "dctcp_min": 60,
        "dctcp_max": 120,
    },
]