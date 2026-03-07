from mininet.topo import Topo
from enum import Enum
from parameters import *

class MininetTopology(Topo):
    """Mininet Topology class that can be populated with different topologies based on the experiment configuration.
    """

    def create(self, num_senders: int, type: TopologyType) -> None:
        """Populate this Topo with `num_senders` and the given `type`.

        Note: parameter name `type` is maintained for backwards compatibility
        with existing call sites.
        """
        if type == TopologyType.DUMBBELL:
            self._dumbbell(num_senders)
        elif type == TopologyType.STAR:
            self._star(num_senders)
        else:
            raise ValueError(f"Unsupported topology type: {type}")

    def _dumbbell(self, num_senders: int):
        # First add a single switch and a receiver.
        switch1 = self.addSwitch(SWITCH_NAME)
        receiver = self.addHost(RECEIVER_NAME)
        # For dumbbell, we need a second switch on the path.
        switch2 = self.addSwitch('switch2')
        # The bottleneck link should be between switches 1 and 2.
        # We choose a small bandwidth value to make sure this link is the 
        # bottleneck.
        self.addLink(
            switch1,
            switch2,
            bw=DumbbellTopologyParameters.BANDWIDTH.value,
            delay=DumbbellTopologyParameters.DELAY.value,
            max_queue_size=DumbbellTopologyParameters.QUEUE_SIZE.value,
        )
        self.addLink(switch2, receiver)
        # Add the senders to the topology.
        for i in range(num_senders):
            sender = self.addHost(f'sender{i+1}')
            # All senders route traffic to switch1.
            # Make sure sender-switch links are not bottleneck.
            self.addLink(sender, switch1, bw=(DumbbellTopologyParameters.BANDWIDTH.value * 2))
            
    # TODO: expand star topology to include multiple layers.
    def _star(self, num_senders: int):
        # First add a single switch and a receiver.
        switch1 = self.addSwitch(SWITCH_NAME)
        receiver = self.addHost(RECEIVER_NAME)
        # The bottleneck link should be between switch1 and the receiver.
        # We choose a smaller delay since switch and receiver should be located 
        # near each other.
        self.addLink(
            switch1,
            receiver,
            bw=StarTopologyParameters.BANDWIDTH.value,
            delay=StarTopologyParameters.DELAY.value,
            max_queue_size=StarTopologyParameters.QUEUE_SIZE.value,
        )
        # Add the senders to the topology.
        for i in range(num_senders):
            sender = self.addHost(f'sender{i+1}')
            # All senders route traffic to switch1.
            self.addLink(sender, switch1, bw=(StarTopologyParameters.BANDWIDTH.value * 2))
        