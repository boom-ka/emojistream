import requests
import threading
import random
import time
from datetime import datetime
import uuid

# Configuration
API_URL = 'http://localhost:5000/emoji'
NUM_CLIENTS = 10  # Reduced to 1 for testing
#EMOJIS = ['👍', '❤️', '😂', '🎉', '😍', '🤔', '😱', '🥳', '👏', '🚀']
EMOJIS = ['👍', '❤️']
EMOJIS_PER_CLIENT = 1000  # Reduced to 5 for testing

def generate_emoji_data():
    """Generate random emoji data"""
    return {
        "user_id": str(uuid.uuid4()),
        "emoji_type": random.choice(EMOJIS),
        "timestamp": datetime.utcnow().isoformat()
    }

def send_emojis(client_id):
    """Simulate a client sending emojis"""
    print(f"Client {client_id} started sending emojis...")  # Debug print
    
    sent_count = 0
    errors = 0
    
    for _ in range(EMOJIS_PER_CLIENT):
        try:
            emoji_data = generate_emoji_data()
            response = requests.post(API_URL, json=emoji_data)
            
            if response.status_code == 200:
                sent_count += 1
            else:
                errors += 1
            
            # Random slight delay to simulate realistic user behavior
            #time.sleep(random.uniform(0.001, 0.01))
        
        except requests.RequestException as e:
            print(f"Client {client_id} error: {e}")
            errors += 1
    
    print(f"Client {client_id}: Sent {sent_count} emojis, {errors} errors")

def run_simulation():
    """Run emoji sending simulation"""
    start_time = time.time()
    
    # Create and start threads for each client
    threads = []
    for i in range(NUM_CLIENTS):
        thread = threading.Thread(target=send_emojis, args=(i,))
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    print(f"\nSimulation completed in {end_time - start_time:.2f} seconds")
    print(f"Total emojis sent: {NUM_CLIENTS * EMOJIS_PER_CLIENT}")

if __name__ == "__main__":
    run_simulation()
