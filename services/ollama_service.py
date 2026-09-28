import requests
import json
from config import Config

class OllamaService:
    @staticmethod
    def get_available_models() -> list:
        """
        Fetches all locally downloaded models from the local Ollama instance.
        Returns a list of model names (e.g. ['gemma2:latest', 'qwen2.5:latest']).
        """
        url = f"{Config.OLLAMA_URL}/api/tags"
        try:
            response = requests.get(url, timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                return [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception:
            pass
        return []

    @staticmethod
    def get_status(model_name: str = None) -> dict:
        """
        Checks whether Ollama is running and if the given model is present locally.
        Returns a dict with connectivity status and installed models.
        """
        target_model = model_name or Config.OLLAMA_MODEL
        url = f"{Config.OLLAMA_URL}/api/tags"
        try:
            response = requests.get(url, timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                target_base = target_model.split(":")[0]
                model_installed = any(
                    target_model in m or m.startswith(target_base) 
                    for m in models
                )
                return {
                    "connected": True,
                    "status": "online",
                    "url": Config.OLLAMA_URL,
                    "model": target_model,
                    "model_installed": model_installed,
                    "available_models": models
                }
            return {
                "connected": False,
                "status": "offline",
                "url": Config.OLLAMA_URL,
                "model": target_model,
                "model_installed": False,
                "available_models": []
            }
        except Exception:
            return {
                "connected": False,
                "status": "offline",
                "url": Config.OLLAMA_URL,
                "model": target_model,
                "model_installed": False,
                "available_models": []
            }

    @staticmethod
    def generate_explanation(candidate_data: dict, model_name: str = None) -> str:
        """
        Sends candidate details to Ollama (e.g., Qwen, Llama, Gemma) for an explanation.
        Falls back safely if Ollama is offline or times out.
        """
        target_model = model_name or Config.OLLAMA_MODEL

        fallback_text = (
            f"{candidate_data.get('candidate_name', 'The candidate')} is the safest replacement because the available "
            f"workforce data shows strong required-skill capability ({candidate_data.get('skill_score')}%), "
            f"good historical performance ({candidate_data.get('performance_score')}%), and sufficient workload capacity."
        )

        prompt = (
            f"Affected task: {candidate_data.get('task_name')}\n"
            f"Required skill: {candidate_data.get('required_skill')}\n"
            f"Candidate: {candidate_data.get('candidate_name')}\n"
            f"Skill: {candidate_data.get('skill_score')}\n"
            f"Historical performance: {candidate_data.get('performance_score')}\n"
            f"Current workload: {candidate_data.get('current_workload')}%\n"
            f"Availability: {candidate_data.get('availability_status')}\n"
            f"Shift: {candidate_data.get('shift')}\n"
            f"Task conflict: {candidate_data.get('task_conflict', 'None')}\n"
            f"Final score: {candidate_data.get('final_score')}\n\n"
            f"Explain why this candidate is suitable for the task. Use only the information provided. "
            f"Do not invent facts. Keep the explanation short, professional, and understandable."
        )

        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 120
            }
        }

        try:
            url = f"{Config.OLLAMA_URL}/api/generate"
            response = requests.post(url, json=payload, timeout=Config.OLLAMA_TIMEOUT)
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                if response_text:
                    return response_text
        except Exception:
            # Fallback when Ollama is offline or times out
            pass

        return fallback_text
