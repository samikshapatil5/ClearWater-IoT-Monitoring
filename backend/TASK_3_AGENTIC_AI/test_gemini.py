from api.llm_api import ask_llm

try:
    answer = ask_llm(
        "Reply in one sentence: Explain why monitoring water turbidity matters."
    )
    print("\nGemini response:\n")
    print(answer)
except Exception as e:
    print(f"Gemini test failed: {e}")