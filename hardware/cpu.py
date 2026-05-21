"""
CPU Execution Module
Handles raw silicon workload simulation via multiprocessing.
"""


def hardware_worker(pid, intensity):
    """
    Executes on a dedicated physical CPU core.
    Simulates hardware load by performing mathematical operations.

    Args:
        pid (int): The Process ID assigned to this core.
        intensity (int): The multiplier for the computational loop (1 = ~1M ops).

    Returns:
        int: The Process ID upon completion.
    """
    result = 0
    # Simulate CPU cycles
    for i in range(intensity * 1000000):
        result += (i * i)
    return pid