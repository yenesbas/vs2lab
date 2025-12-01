"""
Mapper for WordCount MapReduce System
Receives lines from splitter, splits into words, and distributes to reducers
"""
import pickle
import sys
import time
import zmq
import constWC


def main():
    if len(sys.argv) != 2:
        print("Usage: python mapper.py <mapper_id>")
        print("Example: python mapper.py 0")
        sys.exit(1)
    
    mapper_id = int(sys.argv[1])
    
    # Create ZMQ context
    context = zmq.Context()
    
    # Create PULL socket to receive lines from splitter
    pull_socket = context.socket(zmq.PULL)
    splitter_address = f"tcp://{constWC.SPLITTER_HOST}:{constWC.MAPPER_PORT}"
    pull_socket.connect(splitter_address)
    
    # Create PUSH sockets to send words to reducers
    push_sockets = []
    for i in range(constWC.NUM_REDUCERS):
        push_socket = context.socket(zmq.PUSH)
        reducer_address = f"tcp://{constWC.REDUCER_HOSTS[i]}:{constWC.REDUCER_PORTS[i]}"
        push_socket.connect(reducer_address)
        push_sockets.append(push_socket)
    
    # Wait a moment for connections to establish
    time.sleep(1)
    
    print(f"Mapper {mapper_id} started")
    print(f"Mapper {mapper_id} connected to splitter at {splitter_address}")
    print(f"Mapper {mapper_id} connected to {constWC.NUM_REDUCERS} reducers")
    print(f"Mapper {mapper_id} waiting for lines...\n")
    
    line_count = 0
    word_count = 0
    
    # Receive and process lines
    while True:
        try:
            # Receive line from splitter
            line = pickle.loads(pull_socket.recv())
            
            # Check for termination signal
            if line == "DONE":
                print(f"\nMapper {mapper_id} received termination signal")
                # Forward termination signal to all reducers
                for push_socket in push_sockets:
                    push_socket.send(pickle.dumps("DONE"))
                break
            
            line_count += 1
            print(f"Mapper {mapper_id} received line {line_count}: '{line}'")
            
            # Split line into words
            words = line.split()
            
            # Distribute words to reducers based on hash
            for word in words:
                # Determine which reducer should get this word
                reducer_id = hash(word) % constWC.NUM_REDUCERS
                
                # Send word to the appropriate reducer
                push_sockets[reducer_id].send(pickle.dumps(word))
                word_count += 1
                
                print(f"  Mapper {mapper_id}: '{word}' -> Reducer {reducer_id}")
            
        except KeyboardInterrupt:
            print(f"\nMapper {mapper_id} interrupted by user")
            break
        except Exception as e:
            print(f"Mapper {mapper_id} error: {e}")
            break
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Mapper {mapper_id} Summary:")
    print(f"  Lines processed: {line_count}")
    print(f"  Words distributed: {word_count}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
