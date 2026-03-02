import json
import pandas as pd

def parse_json(file) -> pd.DataFrame:
    """Convert iperf3 json file into Pandas dataframe for easier analysis."""
    with open(file, 'r') as f:
        iperf_data = json.load(f)
    
    data = []
    for interval in iperf_data.get('intervals', []):
        # Use the first stream for cwnd and rtt.
        # Throughput is in Mbps, cwnd is in KB, RTT is in ms
        stream = interval['streams'][0]
        data.append({
            'time': interval['sum']['start'],
            'throughput': interval['sum']['bits_per_second'] / 1e6,
            'congestion_window': stream.get('snd_cwnd', 0) / 1024,
            'rtt': stream.get('rtt', 0) / 1000
        })
    return pd.DataFrame(data)

def calculate_jains_fairness_index(data):
    """Use Jain's fairness index as measure of fairness."""
    # First drop any flows that are not sending data at this time point.
    cleaned_data = data.dropna()
    if cleaned_data.empty: return 1.0
    n = len(cleaned_data)
    # Jain's fairness index = (sum(x)^2) / (n * sum(x^2))
    return (cleaned_data.sum()**2) / (n * (cleaned_data**2).sum())

def calculate_fairness(flows_data) -> pd.DataFrame:
    """Takes in an aggregated list of data from multiple flows and calculates fairness across them."""
    # First, we align all flows by time, so we have throughput of each flow at each timestamp.
    aligned_data = pd.concat([flow.set_index('time')['throughput'] for flow in flows_data], axis=1)
    fairness_index = aligned_data.apply(calculate_jains_fairness_index, axis=1)

    # Return a dataframe representing fairness index over time.
    return fairness_index.reset_index(name='fairness_index')