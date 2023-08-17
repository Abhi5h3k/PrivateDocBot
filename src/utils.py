import multiprocessing
import os

import yaml
from box import Box  # Python dictionaries with advanced dot notation access.


def get_available_cpu_cores():
    if os.name == "posix":
        return os.cpu_count()  # Get the number of CPU cores on Unix-based systems
    else:
        return multiprocessing.cpu_count()  # Get the number of CPU cores on Windows


def determine_threads_to_use():
    available_cores = get_available_cpu_cores()

    # Calculate 50% of the available CPU cores
    threads_to_use = int(0.5 * available_cores)

    # Ensure that at least 1 thread is used
    threads_to_use = max(1, threads_to_use)

    return threads_to_use


def load_config():
    with open(r"./config/config.yml", "r", encoding="utf8") as ymlfile:
        cfg = Box(yaml.safe_load(ymlfile))
        return cfg
