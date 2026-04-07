from emergentintegrations.llm.chat import LlmChat, UserMessage
import time
import os


class TaskDecomposer:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
    
    async def decompose(self, query: str, session_id: str) -> dict:
        """
        Break down a complex query into subtasks.
        """
        start_time = time.time()
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"{session_id}_decompose",
            system_message="You are a task decomposition expert. Break down complex queries into 2-4 clear, logical subtasks. Return only the subtasks as a numbered list."
        ).with_model("openai", self.model)
        
        prompt = f"""Decompose this query into logical subtasks:

Query: {query}

Provide 2-4 subtasks as a numbered list. Each subtask should be specific and actionable."""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return {
            "content": response,
            "tokens": len(response.split()),
            "latency_ms": latency_ms
        }
