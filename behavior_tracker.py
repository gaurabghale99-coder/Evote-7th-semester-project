import time
import json
import psycopg2
from rnn_from_scratch import get_fraud_detector

class BehaviorTracker:
    """
    Tracks and analyzes login behavior sequences for a given voter/session.
    """
    def __init__(self, db_config):
        self.db_config = db_config
        self.detector = get_fraud_detector()
        self.max_seq_len = 5

    def log_attempt(self, voter_id, confidence, multiple_faces):
        """
        Logs a login attempt to the database and analyzes the sequence.
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 1. Create table if not exists (in case setup_db wasn't run)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS behavior_logs (
                    id SERIAL PRIMARY KEY,
                    voter_id VARCHAR(50),
                    timestamp FLOAT8,
                    confidence FLOAT8,
                    multiple_faces BOOLEAN
                )
            """)
            
            # 2. Insert current attempt
            now = time.time()
            cur.execute(
                "INSERT INTO behavior_logs (voter_id, timestamp, confidence, multiple_faces) VALUES (%s, %s, %s, %s)",
                (voter_id, now, confidence, multiple_faces)
            )
            conn.commit()
            
            # 3. Fetch recent history for this voter_id
            cur.execute(
                "SELECT timestamp, confidence FROM behavior_logs WHERE voter_id = %s ORDER BY timestamp DESC LIMIT %s",
                (voter_id, self.max_seq_len)
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            if len(rows) < 2:
                return 0.0 # Not enough data for sequence analysis
                
            # 4. Prepare sequence for RNN
            # rows are (timestamp, confidence)
            # we need [time_delta_normalized, confidence]
            seq = []
            for i in range(len(rows) - 1):
                t_current, conf_current = rows[i]
                t_prev, _ = rows[i+1]
                
                delta = t_current - t_prev
                # Normalize delta: 0.0 (very fast < 1s) to 1.0 (slow > 60s)
                norm_delta = min(delta / 60.0, 1.0)
                seq.append([norm_delta, conf_current])
            
            # RNN expects oldest to newest
            seq.reverse()
            
            # 5. Run RNN
            fraud_score = self.detector.forward(seq)[0]
            
            # If multiple faces were detected, artificially boost the score
            if multiple_faces:
                fraud_score = min(fraud_score + 0.4, 1.0)
                
            return fraud_score

        except Exception as e:
            print(f"Error in BehaviorTracker: {e}")
            if conn:
                conn.close()
            return 0.0

if __name__ == "__main__":
    # Test logic
    DB_CONFIG = {
        "host": "localhost",
        "dbname": "evote",
        "user": "postgres",
        "password": "gaurab4445",
        "port": 5432
    }
    tracker = BehaviorTracker(DB_CONFIG)
    # Mock some data
    print("Testing behavior tracker (requires DB connection)...")
    # result = tracker.log_attempt("TEST_VOTER", 0.9, False)
    # print(f"Fraud Score: {result}")
