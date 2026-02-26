from mininet.topo import Topo
from enum import Enum

##### Topology parameters #####
BANDWIDTH_DUMBBELL = 10  # Mbps
QUEUE_SIZE_DUMBBELL = 100
DELAY_DUMBBELL = '20ms'

BANDWIDTH_STAR = 10  # Mbps
QUEUE_SIZE_STAR = 64
DELAY_STAR = '1ms'

class TopologyType(Enum):
    DUMBBELL = 'dumbbell'
    STAR = 'star'

class MininetTopology(Topo):
    def create(self, num_senders: int, type: TopologyType):
        '''
         Creates a topology with the specified number of senders and single receiver for the given topology type.
         num_senders: The number of sender hosts to include in the topology.
         type: The type of topology to create (e.g., 'dumbbell' or 'star').
        '''
        if type == TopologyType.DUMBBELL:
            self._dumbbell(num_senders)
        elif type == TopologyType.STAR:
            self._star(num_senders)
        else:
            raise ValueError(f"Unsupported topology type: {type}")
            
    def _dumbbell(self, num_senders: int):
        # First add a single switch and a receiver.
        switch1 = self.addSwitch('switch1')
        receiver = self.addHost('receiver')
        # For dumbbell, we need a second switch on the path.
        switch2 = self.addSwitch('switch2')
        # The bottleneck link should be between switches 1 and 2.
        # We choose a small bandwidth value to make sure this link is the 
        # bottleneck.
        self.addLink(switch1, switch2, bw=BANDWIDTH_DUMBBELL, delay=DELAY_DUMBBELL, max_queue_size=QUEUE_SIZE_DUMBBELL)
        self.addLink(switch2, receiver)
        # Add the senders to the topology.
        for i in range(num_senders):
            sender = self.addHost(f'sender{i+1}')
            # All senders route traffic to switch1.
            self.addLink(sender, switch1)
            
    # TODO: expand star topology to include multiple layers.
    def _star(self, num_senders: int):
        # First add a single switch and a receiver.
        switch1 = self.addSwitch('switch1')
        receiver = self.addHost('receiver')
        # The bottleneck link should be between switch1 and the receiver.
        # We choose a smaller delay since switch and receiver should be located 
        # near each other.
        self.addLink(switch1, receiver, bw=BANDWIDTH_STAR, delay=DELAY_STAR, max_queue_size=QUEUE_SIZE_STAR)
        # Add the senders to the topology.
        for i in range(num_senders):
            sender = self.addHost(f'sender{i+1}')
            # All senders route traffic to switch1.
            self.addLink(sender, switch1, bw=100)
        