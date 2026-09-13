"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv(override=True)

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được yêu cầu '{prompt}'. (Chế độ Chatbot Cấp 2 chỉ có thể cung cấp thông tin chính sách chung và không thể tra cứu hòm thư hay đặt lịch thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        
        # Kiểm tra nếu prompt chứa lịch sử ReAct trace (Multi-step loop)
        if "LỊCH SỬ CÁC BƯỚC ĐÃ THỰC THI" in prompt:
            # Nhánh 1: Sau khi search_emails tìm thấy email Mentor -> Tiếp tục đọc email
            if "search_emails" in prompt and "read_email" not in prompt and ("mentor" in prompt_lower or "đồ án" in prompt_lower):
                return {
                    "type": "tool_call",
                    "tool_name": "read_email",
                    "arguments": {"message_id": "MSG-2026-001"},
                    "thought": "Đã tìm thấy email từ Mentor. Bước tiếp theo tôi cần đọc nội dung chi tiết bằng tool 'read_email' để nắm rõ yêu cầu thời gian họp."
                }
            # Nhánh 2: Sau khi read_email -> Tra cứu lịch rảnh
            elif "read_email" in prompt and "find_free_time" not in prompt and "NOT_FOUND" not in prompt and ("mentor" in prompt_lower or "họp" in prompt_lower):
                return {
                    "type": "tool_call",
                    "tool_name": "find_free_time",
                    "arguments": {"start_date": "16/09/2026", "duration_minutes": 45},
                    "thought": "Sau khi đọc nội dung email, Mentor cần họp vào ngày 16/09/2026. Bước tiếp theo tôi dùng 'find_free_time' để tìm khung giờ trống phù hợp."
                }
            # Nhánh 3: Sau khi có lịch rảnh -> Đặt lịch họp
            elif "find_free_time" in prompt and "create_calendar_event" not in prompt and ("lên lịch" in prompt_lower or "đặt lịch" in prompt_lower or "tạo sự kiện" in prompt_lower):
                return {
                    "type": "tool_call",
                    "tool_name": "create_calendar_event",
                    "arguments": {
                        "title": "Họp Review Đồ án Tốt nghiệp cùng Mentor",
                        "start_datetime": "10:00 16/09/2026",
                        "end_datetime": "10:45 16/09/2026",
                        "attendees": "mentor.nguyen@vinuni.edu.vn",
                        "description": "Họp review tiến độ và chốt kiến trúc mô hình đồ án tốt nghiệp."
                    },
                    "thought": "Khung giờ 10:00 - 10:45 ngày 16/09/2026 đang trống và hoàn toàn phù hợp. Tôi tiến hành tạo lịch họp bằng 'create_calendar_event'."
                }
            # Nhánh 4: Đã hoàn tất các tác vụ cần thiết -> Trả lời Final Answer
            else:
                if "create_calendar_event" in prompt:
                    content = (
                        "✅ ĐÃ HOÀN TẤT TOÀN BỘ QUY TRÌNH HẸN HỌP CÙNG MENTOR (MULTI-STEP REACT):\n"
                        "1. Đã tìm thấy và đọc chi tiết email MSG-2026-001 từ Mentor Nguyễn Văn A.\n"
                        "2. Đã tra cứu lịch làm việc ngày 16/09/2026 và phát hiện khung giờ trống tối ưu: 10:00 - 10:45.\n"
                        "3. Đã tạo thành công sự kiện lịch 'Họp Review Đồ án Tốt nghiệp cùng Mentor' và gửi giấy mời kèm link Google Meet tới mentor.nguyen@vinuni.edu.vn."
                    )
                elif "NOT_FOUND" in prompt:
                    content = "Không tìm thấy email có mã định danh yêu cầu trong hòm thư của bạn. Vui lòng kiểm tra lại mã thư."
                elif "find_free_time" in prompt:
                    content = "📅 Kết quả tra cứu ngày 16/09/2026: Bạn có 2 khung giờ trống lớn: 10:00 - 12:00 (120 phút) và 14:15 - 15:45 (90 phút). Khung giờ gợi ý tốt nhất là 10:00 - 10:45."
                elif "search_emails" in prompt:
                    content = "Đã tìm thấy các email phù hợp trong hòm thư của bạn. Bạn có thể yêu cầu tôi đọc chi tiết bất kỳ email nào qua mã message_id."
                else:
                    content = "Đã hoàn tất xử lý tác vụ theo yêu cầu của bạn."
                
                return {
                    "type": "text",
                    "content": content,
                    "thought": "Đã thu thập đầy đủ thông tin và hoàn tất các tác vụ cần thiết. Tổng kết kết quả và trả lời trực tiếp cho người dùng."
                }

        # Step 1: Nhận diện intent ban đầu từ câu hỏi người dùng
        if "msg-9999-999" in prompt_lower or ("đọc" in prompt_lower and "msg-" in prompt_lower):
            return {
                "type": "tool_call",
                "tool_name": "read_email",
                "arguments": {"message_id": "MSG-9999-999"},
                "thought": "Người dùng yêu cầu đọc email MSG-9999-999. Tôi sẽ gọi tool read_email."
            }
        elif "alex.turner" in prompt_lower or "unknown-domain" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "search_emails",
                "arguments": {"query": "khẩn cấp", "sender": "alex.turner@unknown-domain.com"},
                "thought": "Người dùng yêu cầu tìm email từ alex.turner@unknown-domain.com. Tôi cần gọi tool search_emails để kiểm tra hòm thư."
            }
        elif "thời gian rảnh" in prompt_lower or "slot trống" in prompt_lower or "lịch trống" in prompt_lower or "tìm lịch" in prompt_lower or "lịch rảnh" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "find_free_time",
                "arguments": {"start_date": "16/09/2026", "duration_minutes": 45},
                "thought": "Người dùng muốn tìm các khung giờ trống phù hợp trong ngày 16/09/2026. Tôi sẽ gọi tool find_free_time."
            }
        elif "mentor" in prompt_lower or "đồ án" in prompt_lower or "tiến độ" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "search_emails",
                "arguments": {"query": "hẹn họp review tiến độ đồ án", "sender": "mentor.nguyen@vinuni.edu.vn"},
                "thought": "Bước 1 trong quy trình ReAct: Tìm kiếm email từ Mentor về yêu cầu họp review tiến độ đồ án."
            }
        elif "sarah" in prompt_lower or "hợp đồng" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "search_emails",
                "arguments": {"query": "hợp đồng", "unread_only": False},
                "thought": "Người dùng muốn tra cứu email từ đối tác Sarah Davis hoặc liên quan đến hợp đồng. Tôi sẽ gọi tool search_emails."
            }
        elif "hộp thư" in prompt_lower or "chưa đọc" in prompt_lower or "email" in prompt_lower or "thư" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "search_emails",
                "arguments": {"query": "", "unread_only": "chưa đọc" in prompt_lower},
                "thought": "Người dùng muốn tra cứu danh sách email trong hộp thư. Tôi sẽ gọi tool search_emails."
            }
        elif "lịch" in prompt_lower or "họp" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "find_free_time",
                "arguments": {"start_date": "16/09/2026", "duration_minutes": 45},
                "thought": "Người dùng hỏi về lịch trình công tác. Tôi sẽ kiểm tra lịch làm việc và tìm khoảng thời gian trống."
            }
        elif "quy định" in prompt_lower or "chính sách" in prompt_lower or "nội bộ" in prompt_lower:
            return {
                "type": "text",
                "content": "Theo quy chế công ty, các cuộc họp trực tuyến nội bộ nên giới hạn tối đa 45-60 phút. Khi cần hủy hoặc dời lịch họp, người chủ trì phải gửi email thông báo trước ít nhất 2 giờ.",
                "thought": "Câu hỏi về quy định và chính sách công ty, trả lời trực tiếp từ kiến thức chung mà không cần gọi Tool."
            }
        else:
            return {
                "type": "text",
                "content": "Chào bạn! Tôi là AI Email & Meeting Operations Agent. Tôi có thể giúp bạn:\n1. 🔍 Tra cứu & đọc email (tìm email chưa đọc, email từ Mentor, Sarah Davis...)\n2. 📅 Quét lịch làm việc & tìm khung giờ rảnh (`find_free_time`)\n3. 🗓️ Tự động đặt lịch họp và gửi link (`create_calendar_event`)\n4. ✍️ Soạn thảo email phản hồi đối tác (`create_email_draft`)\n\nBạn muốn thực hiện tác vụ nào?",
                "thought": "Người dùng gửi câu hỏi mở đầu hoặc chưa rõ ràng. Giới thiệu phạm vi năng lực quản lý Email và Lịch họp."
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        self._quota_exhausted = False

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        if self._quota_exhausted:
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                self._quota_exhausted = True
                print("⚠️ [Gemini Quota Notice]: API Key tạm thời chạm giới hạn lượt gọi (429 Rate Limit - Free Tier). Tự động kích hoạt chế độ Mock Offline mượt mà.")
            else:
                print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({err_msg[:80]}...). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
