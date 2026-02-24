from mininet.topo import Topo

class MininetTopology(Topo):
    # Type can be 'dumbbell' or 'star'
    def create(self, num_senders, type):
        # First add a single switch and a receiver.
        switch1 = self.addSwitch('switch1')
        receiver = self.addHost('receiver')
        
        if type == 'dumbbell':
            # For dumbbell, we need a second switch on the path.
            switch2 = self.addSwitch('switch2')
            # The bottleneck link should be between switches 1 and 2.
            # We choose a small bandwidth value to make sure this link is the 
            # bottleneck.
            self.addLink(switch1, switch2, bw=10, delay='20ms', max_queue_size=100)
            self.addLink(switch2, receiver)
            # Add the senders to the topology.
            for i in range(num_senders):
                sender = self.addHost(f'sender{i+1}')
                # All senders route traffic to switch1.
                self.addLink(sender, switch1)
        # TODO: expand star topology to include multiple layers.
        elif type == 'star':
            # The bottleneck link should be between switch1 and the receiver.
            # We choose a smaller delay since switch and receiver should be located 
            # near each other.
            self.addLink(switch1, receiver, bw=10, delay='1ms', max_queue_size=64)
            # Add the senders to the topology.
            for i in range(num_senders):
                sender = self.addHost(f'sender{i+1}')
                # All senders route traffic to switch1.
                self.addLink(sender, switch1, bw=100)