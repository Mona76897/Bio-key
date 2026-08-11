import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization

# Load ONLY your data (The "Golden Standard")
df = pd.read_csv('biokey_profile.csv')
X = df.values.reshape(-1, 1, 2)
y = np.ones(len(X))

# Module 3: High-Precision LSTM
model = Sequential([
    LSTM(128, input_shape=(1, 2), return_sequences=True),
    BatchNormalization(),
    Dropout(0.3),
    LSTM(64),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
# We train for more epochs to "overfit" slightly to YOUR specific rhythm
model.fit(X, y, epochs=50, batch_size=16, verbose=1)

model.save('biokey_final_model.h5')
print("High-Precision Model Saved.")