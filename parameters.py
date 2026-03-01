from enum import Enum

# TODO: add some description of each parameter.

# Common node names used by the experiment scripts.
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
    DELAY = "20ms"

# Star-specific topology parameters.
class StarTopologyParameters(Enum):
    BANDWIDTH = 10  # Mbps
    QUEUE_SIZE = 64
    DELAY = "1ms"

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