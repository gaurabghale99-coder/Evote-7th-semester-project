import math
import random

class SimpleRNN:
    """
    A pure Python implementation of a simple Recurrent Neural Network.
    No libraries like numpy or torch are used for the math.
    """
    def __init__(self, input_size, hidden_size, output_size):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # Weight matrices initialized with small random values
        # Wxh: Input to hidden weights
        self.Wxh = self._init_weights(hidden_size, input_size)
        # Whh: Hidden to hidden weights (recurrent)
        self.Whh = self._init_weights(hidden_size, hidden_size)
        # Why: Hidden to output weights
        self.Why = self._init_weights(output_size, hidden_size)

        # Biases
        self.bh = [0.0] * hidden_size
        self.by = [0.0] * output_size

    def _init_weights(self, rows, cols):
        return [[random.uniform(-0.1, 0.1) for _ in range(cols)] for _ in range(rows)]

    def _sigmoid(self, x):
        return 1 / (1 + math.exp(-max(min(x, 20), -20)))

    def _tanh(self, x):
        return math.tanh(x)

    def forward(self, inputs):
        """
        inputs: list of vectors (e.g., [[time_delta, confidence], ...])
        """
        h = [0.0] * self.hidden_size # initial hidden state
        
        # Recurrence
        for x in inputs:
            # h = tanh(Wxh * x + Whh * h_prev + bh)
            new_h = [0.0] * self.hidden_size
            for i in range(self.hidden_size):
                # x dot row
                input_part = sum(self.Wxh[i][j] * x[j] for j in range(self.input_size))
                # h dot row
                hidden_part = sum(self.Whh[i][j] * h[j] for j in range(self.hidden_size))
                new_h[i] = self._tanh(input_part + hidden_part + self.bh[i])
            h = new_h

        # Output calculation
        # y = sigmoid(Why * h + by)
        y = [0.0] * self.output_size
        for i in range(self.output_size):
            y[i] = self._sigmoid(sum(self.Why[i][j] * h[j] for j in range(self.hidden_size)) + self.by[i])
        
        return y

# Pre-defined "Behavior Analysis" weights for fraud detection
# This is a heuristic-based set of weights that mimics a trained model
# It looks for patterns like very small time deltas and low confidence
def get_fraud_detector():
    # input_size=2: [time_delta_normalized, confidence_score]
    # hidden_size=3
    # output_size=1: [fraud_probability]
    rnn = SimpleRNN(input_size=2, hidden_size=3, output_size=1)
    
    # Manually setting weights to respond positively to "Suspicious" patterns
    # pattern: very small time_delta (index 0) and low confidence (index 1)
    
    # If time_delta is small (near 0), we want it to contribute to fraud
    # Since we use tanh/sigmoid, we'll favor patterns where inputs are mapped specifically
    rnn.Wxh[0][0] = -1.5 # Negative weight for time_delta (smaller delta = larger contribution if we expect positive fraud)
    rnn.Wxh[0][1] = -0.5 # Negative weight for confidence
    
    rnn.Whh[0][0] = 0.8  # Recurrent reinforcement
    
    rnn.Why[0][0] = 2.0  # High impact on output
    rnn.by[0] = -1.0     # Bias to keep it low by default
    
    return rnn

if __name__ == "__main__":
    detector = get_fraud_detector()
    
    # Test 1: Normal behavior (Large intervals, high confidence)
    # [normalized_time, confidence]
    # normalized_time: 1.0 = slow, 0.0 = fast
    normal_seq = [[1.0, 0.9], [0.9, 0.85], [1.0, 0.95]]
    print(f"Normal Prob: {detector.forward(normal_seq)[0]:.4f}")
    
    # Test 2: Suspicious behavior (Rapid fire, low confidence/failed attempts)
    suspicious_seq = [[0.05, 0.3], [0.02, 0.2], [0.1, 0.4]]
    print(f"Suspicious Prob: {detector.forward(suspicious_seq)[0]:.4f}")
