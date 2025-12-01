# Constants for WordCount MapReduce System

# Splitter → Mapper Communication
SPLITTER_HOST = "127.0.0.1"
MAPPER_PORT = "50020"

# Mapper → Reducer Communication
REDUCER_HOSTS = ["127.0.0.1", "127.0.0.1"]
REDUCER_PORTS = ["50021", "50022"]

# Number of reducers
NUM_REDUCERS = 2
