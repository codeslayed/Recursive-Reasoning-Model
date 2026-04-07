from emergentintegrations.llm.chat import LlmChat, UserMessage
import time


class Reflector:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
    
    async def reflect(self, subtask: str, answer: str, session_id: str) -> dict:
        """
        Reflect on a subtask answer to assess quality and completeness.
        """
        start_time = time.time()
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"{session_id}_reflect",
            system_message="You are a critical thinking expert. Evaluate answers for completeness, accuracy, and logical consistency. Provide a confidence score (0-1) and brief assessment."
        ).with_model("openai", self.model)
        
        prompt = f"""Reflect on this answer:

Subtask: {subtask}
Answer: {answer}

Provide:
1. Confidence score (0.0-1.0)
2. Brief assessment (1-2 sentences)
3. Recommendation: ACCEPT or REFINE

Format: CONFIDENCE: X.X | ASSESSMENT: ... | RECOMMENDATION: ..."""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Parse confidence
        confidence = 0.8
        try:
            if "CONFIDENCE:" in response:
                conf_str = response.split("CONFIDENCE:")[1].split("|")[0].strip()
                confidence = float(conf_str)
        except:
            pass
        
        return {
            "content": response,
            "tokens": len(response.split()),
            "latency_ms": latency_ms,
            "confidence": confidence
        }
