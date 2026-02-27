from rnn_from_scratch import get_fraud_detector

def run_test():
    detector = get_fraud_detector()
    
    print("--- Behavioral Analysis RNN Verification ---")
    
    # 1. Normal Sequential Entry
    # sequence of [normalized_time_delta, confidence]
    # Slow entries (norm_delta=1.0) with high confidence (0.9)
    normal = [[1.0, 0.9], [0.95, 0.92], [1.0, 0.9]]
    normal_score = detector.forward(normal)[0]
    print(f"Normal User Score: {normal_score:.4f}")
    
    # 2. Suspicious "Bot-like" Entry
    # Fast entries (norm_delta=0.01) with lower confidence/variability (0.4)
    suspicious = [[0.01, 0.4], [0.02, 0.35], [0.01, 0.45]]
    suspicious_score = detector.forward(suspicious)[0]
    print(f"Suspicious User Score: {suspicious_score:.4f}")
    
    if suspicious_score > normal_score:
        print("\n✅ Verification SUCCESS: RNN correctly distinguishes between normal and suspicious behavior sequences.")
    else:
        print("\n❌ Verification FAILED: RNN did not differentiate behavior adequately.")

if __name__ == "__main__":
    run_test()
