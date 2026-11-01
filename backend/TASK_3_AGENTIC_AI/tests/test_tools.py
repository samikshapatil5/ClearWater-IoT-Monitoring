from tools.water_quality_tool import get_current_water_quality
from tools.model_tool import get_model_prediction
from tools.knowledge_tool import get_standards
from tools.history_tool import get_water_quality_history


print("====================================")
print("      TESTING AGENT TOOLS")
print("====================================")


# 1. Test current water-quality tool
water_data = get_current_water_quality()

print("\n1. Current Water Quality:")
print(water_data)


# 2. Test model prediction tool
prediction = get_model_prediction(water_data)

print("\n2. CNN-LSTM Prediction:")
print(prediction)


# 3. Test knowledge-base tool
standards = get_standards()

print("\n3. BIS Standards Loaded:")
print(standards["standard"]["name"])


# 4. Test history tool
history = get_water_quality_history()

print("\n4. Historical Readings:")
for reading in history:
    print(reading)


print("\n====================================")
print("      ALL TOOLS TESTED")
print("====================================")