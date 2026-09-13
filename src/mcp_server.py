"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPOfficeServer:
    """
    Giả lập MCP Server tuân thủ chuẩn giao thức Model Context Protocol
    Chủ đề: AI Email & Meeting Operations (MCPOfficeServer)
    """
    def __init__(self, server_name: str = "email-meeting-operations-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        [TASK 2.1] Thực thi request gọi Tool theo chuẩn MCP JSON-RPC 2.0
        Xử lý đầy đủ các trường hợp: UNKNOWN_TOOL, EXECUTION_ERROR, NOT_FOUND, SUCCESS.
        """
        valid_tool_names = [t["name"] for t in TOOLS_SCHEMA]
        
        # 1. Xử lý UNKNOWN_TOOL nếu tên công cụ không tồn tại
        if tool_name not in valid_tool_names:
            return {
                "jsonrpc": "2.0",
                "server": self.server_name,
                "tool": tool_name,
                "error": {
                    "code": -32601,
                    "message": f"Method/Tool '{tool_name}' không tồn tại trong hệ thống (UNKNOWN_TOOL)!"
                },
                "result": {
                    "status": "UNKNOWN_TOOL",
                    "error": f"Tool '{tool_name}' không tồn tại!",
                    "available_tools": valid_tool_names
                }
            }

        # 2. Gọi hàm dispatch_tool_call(tool_name, arguments) qua Tool Router
        try:
            raw_result_str = dispatch_tool_call(tool_name, arguments)
            content = json.loads(raw_result_str)
        except Exception as e:
            # Xử lý EXECUTION_ERROR khi xảy ra ngoại lệ
            return {
                "jsonrpc": "2.0",
                "server": self.server_name,
                "tool": tool_name,
                "error": {
                    "code": -32000,
                    "message": f"Lỗi thực thi trong quá trình chạy Tool (EXECUTION_ERROR): {str(e)}"
                },
                "result": {
                    "status": "EXECUTION_ERROR",
                    "error": str(e)
                }
            }
            
        # 3. Đóng gói phản hồi theo chuẩn giao thức MCP JSON-RPC 2.0
        # content đã có status: "SUCCESS" hoặc "NOT_FOUND" hoặc "CONFLICT"
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }

# Alias để đảm bảo tương thích ngược tuyệt đối với các import cũ
MCPOperationsServer = MCPOfficeServer
MCPAcademicServer = MCPOfficeServer


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (MCPOfficeServer)")
    print("==========================================================")
    
    server = MCPOfficeServer()
    tools = server.list_tools()
    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố: {len(tools)} tools:")
    for t in tools:
        print(f"   - 🛠️ {t['name']}: {t.get('description', '')[:60]}...")
    
    # Kiểm tra trạng thái các Tool Schemas
    missing_props = [t['name'] for t in tools if not t.get("parameters", {}).get("properties")]
    if missing_props:
        print(f"⏳ [CẢNH BÁO]: Các tool sau chưa định nghĩa properties: {missing_props}")
    else:
        print(f"✅ [TASK 1.2]: Tất cả {len(tools)} Tool Schemas đã có đầy đủ schema JSON Schema chuẩn!")

    # 1. Kiểm tra test case SUCCESS
    test_success = server.call_tool("search_emails", {"query": "đồ án tốt nghiệp"})
    print(f"\n1. Test SUCCESS (search_emails):")
    print(f"   Status: {test_success['result'].get('status')} | Found: {test_success['result'].get('total_found')} emails")

    # 2. Kiểm tra test case NOT_FOUND
    test_not_found = server.call_tool("read_email", {"message_id": "MSG-FAKE-999"})
    print(f"2. Test NOT_FOUND (read_email):")
    print(f"   Status: {test_not_found['result'].get('status')} | Message: {test_not_found['result'].get('message')}")

    # 3. Kiểm tra test case UNKNOWN_TOOL
    test_unknown = server.call_tool("non_existent_tool", {})
    print(f"3. Test UNKNOWN_TOOL:")
    print(f"   Status: {test_unknown['result'].get('status')} | Error: {test_unknown['error']['message']}")


