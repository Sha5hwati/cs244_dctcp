import os
from run_experiment import run_experiment
from parameters import *
from mininet.log import setLogLevel, info

def check_parameters(topology, sender_cca, switch_qm, receiver_feedback, traffic_pattern) -> bool:
    if topology not in TopologyType:
        return False
    if sender_cca not in CongestionControlAlgo:
        return False
    if switch_qm not in QueueManagement:
        return False
    if receiver_feedback not in ReceiverFeedback:
        return False
    if traffic_pattern not in TrafficPattern:
        return False
    return True

def main():
    setLogLevel('info')

    # Each row of the experiment table defines a scenario to run.
    # TODO: update the list of scenarios
    experiment_table = [
        {
            "topology": TopologyType.DUMBBELL,
            "cca": CongestionControlAlgo.CUBIC,
            "qm": QueueManagement.TAILDROP,
            "feedback": ReceiverFeedback.IMMEDIATE_ACK,
            "traffic": TrafficPattern.CONSTANT
        },
        {
            "topology": TopologyType.DUMBBELL,
            "cca": CongestionControlAlgo.BBR,
            "qm": QueueManagement.RED,
            "feedback": ReceiverFeedback.DELAYED_ACK,
            "traffic": TrafficPattern.ELEPHANT_VS_MICE
        },
        {
            "topology": TopologyType.STAR,
            "cca": CongestionControlAlgo.DCTCP,
            "qm": QueueManagement.ECN,
            "feedback": ReceiverFeedback.IMMEDIATE_ACK,
            "traffic": TrafficPattern.BURSTY
        },
        {
            "topology": TopologyType.STAR,
            "cca": CongestionControlAlgo.RENO,
            "qm":QueueManagement.TAILDROP,
            "feedback": ReceiverFeedback.DELAYED_ACK,
            "traffic": TrafficPattern.CONSTANT
        }
    ]

    for scenario in experiment_table: 
        topology = scenario['topology']   
        sender_cca = scenario['cca']
        switch_qm = scenario['qm']
        receiver_feedback = scenario['feedback']
        traffic_pattern = scenario['traffic']
        info(f"\n\nSTARTING: {topology}_{sender_cca}_{switch_qm}_{receiver_feedback}_{traffic_pattern}\n\n\n")

        if not check_parameters(topology=topology, sender_cca=sender_cca, switch_qm=switch_qm, 
                                receiver_feedback=receiver_feedback, traffic_pattern=traffic_pattern):
            # Continue to the next scenario if any parameters are invalid.
            continue

        run_experiment(
            topology_type=topology,
            sender_cca=sender_cca,
            switch_qm=switch_qm,
            receiver_feedback=receiver_feedback,
            traffic_pattern=traffic_pattern,
        )

if __name__ == '__main__':
    os.system('sudo mn -c')
    main()