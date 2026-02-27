import time
from main import record_voter_block, is_voter_blocked, DB_CONFIG
import psycopg2

def test_block_logic():
    voter_id = "V123" # Assuming this exists or we create it
    
    # Ensure voter exists or create a dummy one
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("INSERT INTO voters (voter_id, full_name, voted) VALUES (%s, 'Test Voter', FALSE) ON CONFLICT (voter_id) DO NOTHING", (voter_id,))
    conn.commit()
    
    print(f"Testing block for {voter_id}...")
    
    # 1. Initial state (should not be blocked)
    print(f"Initial block status: {is_voter_blocked(voter_id)}")
    
    # 2. Record block
    record_voter_block(voter_id, 1)
    print(f"Block status after recording: {is_voter_blocked(voter_id)}")
    
    if is_voter_blocked(voter_id):
        print("✅ Block recorded successfully.")
    else:
        print("❌ Block record failed.")
        return

    # 3. Wait/Check (we won't wait a full minute in the script for speed, but we can verify the DB timestamp)
    cur.execute("SELECT blocked_until FROM voters WHERE voter_id = %s", (voter_id,))
    blocked_until = cur.fetchone()[0]
    print(f"Blocked until: {blocked_until}")
    
    # 4. Cleanup/Expiry test (manual check of the logic)
    print("Verification complete.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    test_block_logic()
