import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional dependency
    genai = None


# System Prompt (Vietnamese only) for house price assistant
SYSTEM_PROMPT_VI = """Bạn là trợ lý AI hỗ trợ dự đoán giá nhà tại Bengaluru.

NGÔN NGỮ:
- Luôn trả lời 100% bằng tiếng Việt, kể cả khi người dùng nhập tiếng Anh.

VAI TRÒ:
- Không tự ý tính toán hoặc dự đoán khi thiếu thông tin.
- Thu thập đủ thông tin đầu vào rồi chuyển tiếp cho backend mô hình giá nhà.

THÔNG TIN CẦN HỎI:
- location (tên khu vực)
- total_sqft (diện tích)
- bath (số phòng W/C)
- bhk (số phòng)

HƯỚNG DẪN TRẢ LỜI:
- Nếu thiếu bất kỳ trường nào, hãy hỏi thêm để lấy đủ.
- Khi đã đủ 4 trường, tóm tắt ngắn gọn các giá trị người dùng cung cấp và cho biết sẽ gửi sang mô hình để dự đoán giá."""


def _get_env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class LLMService:
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):

        api_key = os.getenv("GEMINI_API_KEY")
        if genai is not None and api_key:
            genai.configure(api_key=api_key)

        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME")
        self.temperature = (
            temperature
            if temperature is not None
            else _get_env_float("GEMINI_TEMPERATURE", 0.6)
        )
        self.max_tokens = (
            max_tokens
            if max_tokens is not None
            else _get_env_int("GEMINI_MAX_TOKENS", 1024)
        )

    def get_system_prompt(self) -> str:
        """Return the Vietnamese system prompt for the house price assistant."""
        return SYSTEM_PROMPT_VI

    async def chat(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        """
        Gửi request hội thoại đến Gemini.
        """
        import asyncio

        system_prompt = self.get_system_prompt()
        full_messages = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]
        print("Full messages sent to LLM (Gemini):")
        print(full_messages)

        # Nếu không có SDK hoặc API key, trả lời stub để tránh crash môi trường dev
        if genai is None or not os.getenv("GEMINI_API_KEY"):
            return "Hiện tại chưa cấu hình GEMINI_API_KEY, nên tôi chỉ trả lời nháp: " + messages[-1]["content"]

        gemini_history = []
        for m in messages:
            role = m.get("role", "user")
            gemini_role = "model" if role == "assistant" else "user"
            gemini_history.append({"role": gemini_role, "parts": [{"text": m["content"]}]})

        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )

        def _sync_call():
            return model.generate_content(
                gemini_history,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
            )

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            response = await loop.run_in_executor(None, _sync_call)
        except Exception as e:
            print(f"LLM (Gemini) error: {e}")
            raise

        try:
            return response.text
        except Exception:
            try:
                return str(response)
            except Exception:
                return ""

    def parse_function_call(self, response: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Placeholder parser. Update when adding function-calling schema for house price prediction.
        """
        # No structured function call needed for current flow.
        return False, None


llm_service = LLMService()
