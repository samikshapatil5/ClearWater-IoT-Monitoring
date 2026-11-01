from chatbot.chatbot import generate_response, give_feedback


print("======================================")
print("       FULL INTEGRATION TEST")
print("======================================")


# 1. Run chatbot with a user question
result = generate_response(
    "Is my water safe right now?"
)

print("\n1. User Question:")
print(result["question"])

print("\n2. Chatbot Response:")
print(result["response"])


# 2. Display Agent Decision
print("\n3. Agent Decision:")
print(result["agent_result"]["decision"])


# 3. Display Recommendations
print("\n4. Recommendations:")
for item in result["agent_result"]["recommendation"]:
    print("-", item)


# 4. Submit prediction feedback
prediction_feedback = give_feedback(
    feedback_type="prediction",
    user_feedback="Prediction was correct",
    agent_result=result["agent_result"]
)

print("\n5. Prediction Feedback:")
print(prediction_feedback)


# 5. Submit chatbot feedback
chatbot_feedback = give_feedback(
    feedback_type="chatbot",
    user_feedback="Chatbot response was helpful",
    agent_result=result["agent_result"]
)

print("\n6. Chatbot Feedback:")
print(chatbot_feedback)


print("\n======================================")
print("       FULL INTEGRATION COMPLETE")
print("======================================")