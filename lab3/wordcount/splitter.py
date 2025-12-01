"""
Splitter for WordCount MapReduce System
Reads text file and distributes lines to mappers
"""
import pickle
import time
import zmq
import constWC
import os


def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    text_file = os.path.join(script_dir, "textdata.txt")
    
    # Check if text file exists
    if not os.path.exists(text_file):
        print(f"Error: {text_file} not found!")
        return
    
    # Create ZMQ context and PUSH socket
    context = zmq.Context()
    push_socket = context.socket(zmq.PUSH)
    
    # Bind to address for mappers
    address = f"tcp://{constWC.SPLITTER_HOST}:{constWC.MAPPER_PORT}"
    push_socket.bind(address)
    
    print(f"Splitter started on {address}")
    print(f"Reading from: {text_file}")
    print("Waiting for mappers to connect...")
    
    # Wait for mappers to connect (important for fair distribution)
    time.sleep(2)
    
    print("\nStarting to distribute lines...\n")
    
    # Read and distribute lines
    line_count = 0
    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    line_count += 1
                    print(f"Splitter: Sending line {line_count}: '{line}'")
                    push_socket.send(pickle.dumps(line))
                    time.sleep(0.1)  # Small delay for visibility
        
        # Send termination signal to all mappers
        print(f"\nSplitter: All lines sent. Sending termination signal...")
        # Send DONE signal (will be distributed to all connected mappers)
        for _ in range(10):  # Send multiple times to ensure all mappers get it
            push_socket.send(pickle.dumps("DONE"))
            time.sleep(0.1)
        
    except KeyboardInterrupt:
        print("\nSplitter interrupted by user")
    except Exception as e:
        print(f"Splitter error: {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Splitter Summary:")
    print(f"  Total lines sent: {line_count}")
    print(f"{'='*50}")
    
    # Wait a moment before closing
    time.sleep(1)


if __name__ == "__main__":
    main()
