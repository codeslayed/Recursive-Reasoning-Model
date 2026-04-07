from emergentintegrations.llm.chat import LlmChat, UserMessage
import time
from typing import List, Dict


class Synthesizer:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
    
    async def synthesize(self, query: str, subtask_results: List[Dict], session_id: str) -> dict:
        """
        Synthesize subtask results into a final comprehensive answer.
        """
        start_time = time.time()
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"{session_id}_synthesize",
            system_message="You are an expert at synthesizing information. Combine multiple subtask results into a coherent, comprehensive final answer."
        ).with_model("openai", self.model)
        
        subtask_text = "\n\n".join([
            f"Subtask {i+1}: {r['subtask']}\nResult: {r['answer']}"
            for i, r in enumerate(subtask_results)
        ])
        
        prompt = f"""Original Query: {query}

Subtask Results:
{subtask_text}

Synthesize these results into a clear, comprehensive final answer that directly addresses the original query."""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return {
            "content": response,
            "tokens": len(response.split()),
            "latency_ms": latency_ms
        }
