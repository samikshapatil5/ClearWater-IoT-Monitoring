from tools.model_tool import get_model_prediction
from agent.reasoning import analyze_water_quality
from agent.decision import make_decision
from agent.recommendation import get_recommendation


# Warning condition test
water_quality = {
    "pH": 7.2,
    "TDS": 800,
    "turbidity": 0.8,
    "temperature": 27.0
}

print("====================================")
print("       WARNING CONDITION TEST")
print("====================================")

# 1. CNN-LSTM prediction (currently simulated)
model_prediction = get_model_prediction(water_quality)

# 2. Reasoning
analysis = analyze_water_quality(
    water_quality,
    model_prediction
)

# 3. Decision
decision = make_decision(analysis)

# 4. Recommendation
recommendation = get_recommendation(
    analysis,
    decision
)

print("\n1. Water Quality:")
print(water_quality)

print("\n2. CNN-LSTM Prediction:")
print(model_prediction)

print("\n3. Reasoning:")
print(analysis)

print("\n4. Final Decision:")
print(decision)

print("\n5. Recommendation:")
for item in recommendation:
    print("-", item)

print("\n====================================")
print("       WARNING TEST COMPLETE")
print("====================================")