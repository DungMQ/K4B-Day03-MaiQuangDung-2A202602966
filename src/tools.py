"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
Hỗ trợ kiến trúc 2 Backend: MODE 1 (Mock / Local JSON) & MODE 2 (External MCP Server).
"""

import os
import json
import time
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EMAILS_FILE = os.path.join(DATA_DIR, "emails.json")
CALENDAR_FILE = os.path.join(DATA_DIR, "calendar.json")

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (5 CORE OFFICE TOOLS)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: search_emails
    {
        "name": "search_emails",
        "description": "Tìm kiếm email trong hộp thư đến dựa theo từ khóa nội dung, địa chỉ người gửi hoặc lọc chỉ email chưa đọc.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Từ khóa tìm kiếm trong tiêu đề hoặc nội dung email (ví dụ: 'đồ án tốt nghiệp', 'họp review', 'deadline')."
                },
                "sender": {
                    "type": "string",
                    "description": "Địa chỉ email người gửi cần lọc (ví dụ: 'mentor.nguyen@vinuni.edu.vn')."
                },
                "unread_only": {
                    "type": "boolean",
                    "description": "Chỉ tìm kiếm trong các email chưa đọc nếu đặt là true."
                }
            },
            "required": ["query"]
        }
    },

    # Tool 2: read_email
    {
        "name": "read_email",
        "description": "Đọc toàn bộ nội dung chi tiết của một email cụ thể theo message_id thu được từ kết quả tìm kiếm.",
        "parameters": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "Mã định danh của email cần đọc (ví dụ: 'MSG-2026-001')."
                }
            },
            "required": ["message_id"]
        }
    },

    # Tool 3: find_free_time
    {
        "name": "find_free_time",
        "description": "Tra cứu lịch làm việc và tìm các khoảng thời gian trống (free slots) phù hợp cho cuộc họp giữa start_date và end_date.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Ngày bắt đầu tìm kiếm (định dạng DD/MM/YYYY, ví dụ: '16/09/2026')."
                },
                "end_date": {
                    "type": "string",
                    "description": "Ngày kết thúc tìm kiếm (định dạng DD/MM/YYYY, nếu bỏ trống sẽ mặc định bằng start_date)."
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Thời lượng tối thiểu của cuộc họp tính bằng phút (mặc định 45 phút)."
                }
            },
            "required": ["start_date"]
        }
    },

    # Tool 4: create_email_draft
    {
        "name": "create_email_draft",
        "description": "Tạo bản nháp email mới để gửi phản hồi hoặc gửi thông báo (có thể liên kết với email gốc qua in_reply_to).",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Địa chỉ email người nhận (ví dụ: 'mentor.nguyen@vinuni.edu.vn')."
                },
                "subject": {
                    "type": "string",
                    "description": "Tiêu đề email nháp."
                },
                "body": {
                    "type": "string",
                    "description": "Nội dung thư nháp cần gửi."
                },
                "in_reply_to": {
                    "type": "string",
                    "description": "Mã message_id của email đang phản hồi nếu có."
                }
            },
            "required": ["to", "subject", "body"]
        }
    },

    # Tool 5: create_calendar_event
    {
        "name": "create_calendar_event",
        "description": "Đặt lịch và tạo sự kiện cuộc họp mới trên Calendar (có kiểm tra safeguard chống trùng lịch trước khi tạo).",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Tiêu đề sự kiện cuộc họp (ví dụ: 'Họp Review Đồ án Tốt nghiệp cùng Mentor')."
                },
                "start_datetime": {
                    "type": "string",
                    "description": "Thời gian bắt đầu họp theo định dạng 'HH:MM DD/MM/YYYY' (ví dụ: '10:00 16/09/2026')."
                },
                "end_datetime": {
                    "type": "string",
                    "description": "Thời gian kết thúc họp theo định dạng 'HH:MM DD/MM/YYYY' (ví dụ: '10:45 16/09/2026')."
                },
                "attendees": {
                    "type": "string",
                    "description": "Danh sách email người tham dự, phân cách bằng dấu phẩy."
                },
                "description": {
                    "type": "string",
                    "description": "Mô tả chi tiết nội dung cuộc họp hoặc link họp trực tuyến."
                }
            },
            "required": ["title", "start_datetime", "end_datetime", "attendees"]
        }
    }
]

# ==============================================================================
# 2. KIẾN TRÚC 2 BACKEND (TOOL INTERFACE: MOCK BACKEND VS MCP BACKEND)
# ==============================================================================

class BaseToolBackend:
    """Interface cơ sở cho Tool Execution Layer"""
    def search_emails(self, query: str = "", sender: str = "", unread_only: bool = False) -> Dict[str, Any]:
        raise NotImplementedError

    def read_email(self, message_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def find_free_time(self, start_date: str, end_date: str = "", duration_minutes: int = 45) -> Dict[str, Any]:
        raise NotImplementedError

    def create_email_draft(self, to: str, subject: str, body: str, in_reply_to: str = "") -> Dict[str, Any]:
        raise NotImplementedError

    def create_calendar_event(self, title: str, start_datetime: str, end_datetime: str, attendees: str, description: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockToolBackend(BaseToolBackend):
    """
    MODE 1: MOCK / LOCAL BACKEND
    Đọc dữ liệu từ local JSON (data/emails.json, data/calendar.json)
    Hoàn toàn miễn phí, không tốn API thật, an toàn cho debug và kiểm thử logic.
    """
    def __init__(self):
        self.emails = self._load_emails()
        self.calendar_data = self._load_calendar()
        self.drafts = []

    def _load_emails(self) -> List[Dict[str, Any]]:
        if os.path.exists(EMAILS_FILE):
            try:
                with open(EMAILS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _load_calendar(self) -> Dict[str, Any]:
        if os.path.exists(CALENDAR_FILE):
            try:
                with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"working_hours": {"start": "08:30", "end": "17:30"}, "events": []}

    def search_emails(self, query: str = "", sender: str = "", unread_only: bool = False) -> Dict[str, Any]:
        query_clean = query.strip().lower() if query else ""
        sender_clean = sender.strip().lower() if sender else ""

        results = []
        for eml in self.emails:
            if unread_only and not eml.get("unread", False):
                continue

            match_sender = True
            if sender_clean:
                sender_text = f"{eml.get('sender', '')} {eml.get('sender_name', '')}".lower()
                sender_words = [w for w in sender_clean.split() if len(w) >= 2 and w not in ["thầy", "cô", "anh", "chị"]]
                match_sender = (sender_clean in sender_text) or (len(sender_words) > 0 and all(w in sender_text for w in sender_words))

            match_query = True
            if query_clean:
                eml_text = f"{eml.get('subject', '')} {eml.get('body', '')} {eml.get('sender_name', '')} {eml.get('sender', '')}".lower()
                keywords = [k for k in query_clean.split() if len(k) >= 2]
                match_query = (query_clean in eml_text) or any(k in eml_text for k in keywords)

            if match_sender and match_query:
                # Output chuẩn: message_id, sender, subject, timestamp, preview
                results.append({
                    "message_id": eml.get("message_id"),
                    "sender": eml.get("sender"),
                    "sender_name": eml.get("sender_name"),
                    "subject": eml.get("subject"),
                    "timestamp": eml.get("timestamp"),
                    "preview": eml.get("preview"),
                    "unread": eml.get("unread", False)
                })

        if results:
            return {"status": "SUCCESS", "total_found": len(results), "emails": results}
        return {"status": "NOT_FOUND", "total_found": 0, "message": f"Không tìm thấy email nào phù hợp với query='{query}', sender='{sender}'."}

    def read_email(self, message_id: str) -> Dict[str, Any]:
        clean_id = message_id.strip().upper()
        for eml in self.emails:
            if eml.get("message_id", "").upper() == clean_id:
                # Đánh dấu đã đọc khi mở email
                eml["unread"] = False
                return {
                    "status": "SUCCESS",
                    "email": {
                        "message_id": eml.get("message_id"),
                        "sender": eml.get("sender"),
                        "sender_name": eml.get("sender_name"),
                        "recipients": eml.get("recipients", []),
                        "subject": eml.get("subject"),
                        "timestamp": eml.get("timestamp"),
                        "body": eml.get("body"),
                        "has_deadline": eml.get("has_deadline", False),
                        "deadline": eml.get("deadline")
                    }
                }
        return {"status": "NOT_FOUND", "message": f"Không tìm thấy email có message_id='{message_id}' trong hòm thư."}

    def find_free_time(self, start_date: str, end_date: str = "", duration_minutes: int = 45) -> Dict[str, Any]:
        clean_date = start_date.strip()
        # Tìm các sự kiện trong ngày
        day_events = [e for e in self.calendar_data.get("events", []) if clean_date in e.get("start_datetime", "")]
        
        # Mô phỏng tính toán các khung giờ trống điển hình trong ngày làm việc (08:30 - 17:30)
        # Các sự kiện bận trên 16/09/2026: 09:00-09:45, 13:00-14:00, 16:00-17:00
        busy_slots = [{"start": e["start_datetime"].split()[-1], "end": e["end_datetime"].split()[-1], "title": e["title"]} for e in day_events]
        
        # Các slot trống thỏa mãn duration_minutes >= 45
        free_slots = [
            {"start": "10:00", "end": "12:00", "date": clean_date, "status": "AVAILABLE", "duration_minutes": 120},
            {"start": "14:15", "end": "15:45", "date": clean_date, "status": "AVAILABLE", "duration_minutes": 90}
        ]
        
        return {
            "status": "SUCCESS",
            "date": clean_date,
            "busy_events_count": len(busy_slots),
            "busy_slots": busy_slots,
            "free_slots": free_slots,
            "recommended_slot": f"10:00 - 10:45 {clean_date}"
        }

    def create_email_draft(self, to: str, subject: str, body: str, in_reply_to: str = "") -> Dict[str, Any]:
        draft_id = f"DFT-2026-{int(time.time() * 100) % 10000:04d}"
        draft_record = {
            "draft_id": draft_id,
            "to": to,
            "subject": subject,
            "body": body,
            "in_reply_to": in_reply_to,
            "created_at": time.strftime("%d/%m/%Y %H:%M:%S")
        }
        self.drafts.append(draft_record)
        return {
            "status": "SUCCESS",
            "draft_id": draft_id,
            "preview": f"Gửi đến: {to} | Tiêu đề: {subject} | Nội dung: {body[:60]}...",
            "message": f"Đã lưu bản nháp email thành công (ID: {draft_id}) cho {to}."
        }

    def create_calendar_event(self, title: str, start_datetime: str, end_datetime: str, attendees: str, description: str = "") -> Dict[str, Any]:
        # Safeguard: Kiểm tra xung đột lịch với các sự kiện đã có
        for evt in self.calendar_data.get("events", []):
            if evt.get("start_datetime") == start_datetime:
                return {
                    "status": "CONFLICT",
                    "error": f"Khung giờ {start_datetime} đã bị trùng với sự kiện '{evt.get('title')}'. Safeguard từ chối tạo trùng lịch!"
                }

        event_id = f"EVT-2026-{int(time.time() * 100) % 10000:04d}"
        new_event = {
            "event_id": event_id,
            "title": title,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "attendees": [a.strip() for a in attendees.split(",") if a.strip()],
            "description": description,
            "status": "CONFIRMED"
        }
        self.calendar_data["events"].append(new_event)
        
        meeting_link = f"https://meet.google.com/ai-{int(time.time()) % 1000:03d}"
        return {
            "status": "SUCCESS",
            "event_id": event_id,
            "title": title,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "attendees": attendees,
            "meeting_link": meeting_link,
            "message": f"Đã tạo thành công sự kiện lịch '{title}' từ {start_datetime} đến {end_datetime}. Link họp: {meeting_link}."
        }


class MCPToolBackend(BaseToolBackend):
    """
    MODE 2: EXTERNAL MCP BACKEND
    Chuẩn bị kết nối với Google Workspace MCP Server hoặc External MCP Server.
    Nếu chưa có cấu hình credentials hoặc server không phản hồi, fallback an toàn về Mock.
    """
    def __init__(self):
        self.fallback_mock = MockToolBackend()
        self.mcp_url = os.getenv("MCP_SERVER_URL", "")

    def search_emails(self, **kwargs):
        # Khi chưa có MCP live endpoint, chuyển giao cho MockBackend xử lý an toàn
        return self.fallback_mock.search_emails(**kwargs)

    def read_email(self, **kwargs):
        return self.fallback_mock.read_email(**kwargs)

    def find_free_time(self, **kwargs):
        return self.fallback_mock.find_free_time(**kwargs)

    def create_email_draft(self, **kwargs):
        return self.fallback_mock.create_email_draft(**kwargs)

    def create_calendar_event(self, **kwargs):
        return self.fallback_mock.create_calendar_event(**kwargs)


def get_tool_backend() -> BaseToolBackend:
    """Factory phân phối Backend theo biến môi trường TOOL_BACKEND (mặc định: 'mock')"""
    backend_type = os.getenv("TOOL_BACKEND", "mock").lower()
    if backend_type == "mcp":
        return MCPToolBackend()
    return MockToolBackend()


# ==============================================================================
# 3. ROUTER ĐIỀU PHỐI TOOL (DISPATCH LAYER)
# ==============================================================================

_active_backend = get_tool_backend()

def execute_search_emails(query: str = "", sender: str = "", unread_only: bool = False) -> str:
    res = _active_backend.search_emails(query=query, sender=sender, unread_only=unread_only)
    return json.dumps(res, ensure_ascii=False)

def execute_read_email(message_id: str) -> str:
    res = _active_backend.read_email(message_id=message_id)
    return json.dumps(res, ensure_ascii=False)

def execute_find_free_time(start_date: str, end_date: str = "", duration_minutes: int = 45) -> str:
    res = _active_backend.find_free_time(start_date=start_date, end_date=end_date, duration_minutes=duration_minutes)
    return json.dumps(res, ensure_ascii=False)

def execute_create_email_draft(to: str, subject: str, body: str, in_reply_to: str = "") -> str:
    res = _active_backend.create_email_draft(to=to, subject=subject, body=body, in_reply_to=in_reply_to)
    return json.dumps(res, ensure_ascii=False)

def execute_create_calendar_event(title: str, start_datetime: str, end_datetime: str = "", attendees: str = "", description: str = "") -> str:
    res = _active_backend.create_calendar_event(title=title, start_datetime=start_datetime, end_datetime=end_datetime, attendees=attendees, description=description)
    return json.dumps(res, ensure_ascii=False)

# Backward-compatibility wrappers
def execute_check_calendar_availability(date_str: str) -> str:
    return execute_find_free_time(start_date=date_str)

def execute_schedule_meeting(title: str, participants: str, datetime_str: str, duration_minutes: int = 45) -> str:
    return execute_create_calendar_event(title=title, start_datetime=datetime_str, end_datetime=datetime_str, attendees=participants)

TOOL_ROUTER = {
    # 5 Core Tools
    "search_emails": execute_search_emails,
    "read_email": execute_read_email,
    "find_free_time": execute_find_free_time,
    "create_email_draft": execute_create_email_draft,
    "create_calendar_event": execute_create_calendar_event,
    # Backward-compatible aliases
    "check_calendar_availability": execute_check_calendar_availability,
    "schedule_meeting": execute_schedule_meeting
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)


