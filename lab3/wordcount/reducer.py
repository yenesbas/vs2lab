"""
Reducer for WordCount MapReduce System
Receives words from mappers and counts them
"""
import pickle
import sys
import zmq
import constWC


def main():
    if len(sys.argv) != 2:
        print("Usage: python reducer.py <reducer_id>")
        print("Example: python reducer.py 0")
        sys.exit(1)
    
    reducer_id = int(sys.argv[1])
    
    if reducer_id < 0 or reducer_id >= constWC.NUM_REDUCERS:
        print(f"Error: reducer_id must be between 0 and {constWC.NUM_REDUCERS - 1}")
        sys.exit(1)
    
    # Create ZMQ context and PULL socket
    context = zmq.Context()
    pull_socket = context.socket(zmq.PULL)
    
    # Bind to the address for this reducer
    host = constWC.REDUCER_HOSTS[reducer_id]
    port = constWC.REDUCER_PORTS[reducer_id]
    address = f"tcp://{host}:{port}"
    pull_socket.bind(address)
    
    print(f"Reducer {reducer_id} started on {address}")
    print(f"Reducer {reducer_id} waiting for words...")
    
    # Dictionary to store word counts
    word_count = {}
    
    # Receive and count words
    while True:
        try:
            # Receive word from mapper
            word = pickle.loads(pull_socket.recv())
            
            # Check for termination signal
            if word == "DONE":
                print(f"\nReducer {reducer_id} received termination signal")
                break
            
            # Update word count
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1
            
            # Print current count for this word
            print(f"Reducer {reducer_id}: {word}:{word_count[word]}")
            
        except KeyboardInterrupt:
            print(f"\nReducer {reducer_id} interrupted by user")
            break
        except Exception as e:
            print(f"Reducer {reducer_id} error: {e}")
            break
    
    # Print final summary
    print(f"\n{'='*50}")
    print(f"Reducer {reducer_id} - Final Word Count:")
    print(f"{'='*50}")
    for word, count in sorted(word_count.items()):
        print(f"{word}: {count}")
    print(f"{'='*50}")
    print(f"Total unique words: {len(word_count)}")
    print(f"Total words processed: {sum(word_count.values())}")


if __name__ == "__main__":
    main()
