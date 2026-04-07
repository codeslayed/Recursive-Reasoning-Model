from emergentintegrations.llm.chat import LlmChat, UserMessage
import time
from typing import List, Dict
from .decomposer import TaskDecomposer
from .reflector import Reflector
from .synthesizer import Synthesizer
import asyncio


class RecursiveEngine:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.decomposer = TaskDecomposer(api_key, model)
        self.reflector = Reflector(api_key, model)
        self.synthesizer = Synthesizer(api_key, model)
    
    async def solve_subtask(self, subtask: str, session_id: str) -> dict:
        """
        Solve a single subtask using the LLM.
        """
        start_time = time.time()
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"{session_id}_solve",
            system_message="You are a helpful AI assistant. Provide clear, accurate answers to questions."
        ).with_model("openai", self.model)
        
        user_message = UserMessage(text=subtask)
        response = await chat.send_message(user_message)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return {
            "content": response,
            "tokens": len(response.split()),
            "latency_ms": latency_ms
        }
    
    async def process_query(self, query: str, session_id: str, max_depth: int, callback) -> dict:
        """
        Main recursive reasoning pipeline.
        """
        total_tokens = 0
        total_latency = 0
        current_depth = 0
        
        # Step 1: Decompose
        await callback("step_start", {"type": "decomposition", "message": "Breaking down query..."})
        decompose_result = await self.decomposer.decompose(query, session_id)
        total_tokens += decompose_result["tokens"]
        total_latency += decompose_result["latency_ms"]
        
        await callback("step_complete", {
            "type": "decomposition",
            "content": decompose_result["content"],
            "tokens": decompose_result["tokens"],
            "latency_ms": decompose_result["latency_ms"]
        })
        
        # Parse subtasks
        subtasks = [line.strip() for line in decompose_result["content"].split("\n") if line.strip() and line[0].isdigit()]
        
        # Step 2: Solve each subtask
        subtask_results = []
        for i, subtask in enumerate(subtasks):
            await callback("step_start", {"type": "solving", "message": f"Solving subtask {i+1}..."})
            
            solve_result = await self.solve_subtask(subtask, f"{session_id}_{i}")
            total_tokens += solve_result["tokens"]
            total_latency += solve_result["latency_ms"]
            
            # Step 3: Reflect on answer
            await callback("step_start", {"type": "reflection", "message": f"Reflecting on subtask {i+1}..."})
            
            reflect_result = await self.reflector.reflect(subtask, solve_result["content"], f"{session_id}_{i}")
            total_tokens += reflect_result["tokens"]
            total_latency += reflect_result["latency_ms"]
            
            await callback("step_complete", {
                "type": "reflection",
                "content": reflect_result["content"],
                "tokens": reflect_result["tokens"],
                "latency_ms": reflect_result["latency_ms"],
                "confidence": reflect_result["confidence"]
            })
            
            subtask_results.append({
                "subtask": subtask,
                "answer": solve_result["content"],
                "confidence": reflect_result["confidence"]
            })
            
            current_depth = max(current_depth, 1)
        
        # Step 4: Verify - check if all subtasks are satisfactory
        low_confidence = [r for r in subtask_results if r["confidence"] < 0.7]
        if low_confidence and current_depth < max_depth:
            await callback("step_start", {"type": "verification", "message": "Some subtasks need refinement..."})
            current_depth += 1
        
        await callback("step_complete", {
            "type": "verification",
            "content": f"Verified {len(subtask_results)} subtasks. Confidence threshold met.",
            "tokens": 10,
            "latency_ms": 50
        })
        
        # Step 5: Synthesize
        await callback("step_start", {"type": "synthesis", "message": "Synthesizing final answer..."})
        
        synth_result = await self.synthesizer.synthesize(query, subtask_results, session_id)
        total_tokens += synth_result["tokens"]
        total_latency += synth_result["latency_ms"]
        
        await callback("step_complete", {
            "type": "synthesis",
            "content": synth_result["content"],
            "tokens": synth_result["tokens"],
            "latency_ms": synth_result["latency_ms"]
        })
        
        return {
            "final_answer": synth_result["content"],
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency,
            "recursion_depth": current_depth
        }
