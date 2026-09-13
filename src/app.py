"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPOfficeServer, MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv(override=True)

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list, append: bool = True):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json (hỗ trợ lưu tích lũy nhiều log)"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    
    existing_data = []
    if append and os.path.exists(trace_path):
        try:
            with open(trace_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, list):
                    existing_data = content
        except Exception:
            existing_data = []
            
    # Tích lũy các sự kiện mới vào danh sách cũ
    combined_data = existing_data + trace_data
    
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu tích lũy {len(combined_data)} sự kiện Waterfall Trace ({len(trace_data)} sự kiện mới) tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def format_prompt_with_history(user_query: str, history: list) -> str:
    """Đóng gói ngữ cảnh lịch sử suy luận ReAct và các Observation đưa lại cho LLM"""
    if not history:
        return user_query
    
    prompt = f"Yêu cầu ban đầu của người dùng: {user_query}\n\n"
    prompt += "📋 LỊCH SỬ CÁC BƯỚC ĐÃ THỰC THI (ReAct Trace):\n"
    for h in history:
        prompt += f"- Bước {h['step']}:\n"
        prompt += f"  • Thought: {h.get('thought', '')}\n"
        prompt += f"  • Action: {h.get('tool_name')}({json.dumps(h.get('arguments', {}), ensure_ascii=False)})\n"
        prompt += f"  • Observation: {json.dumps(h.get('observation', {}), ensure_ascii=False)}\n"
    
    prompt += (
        "\n👉 DỰA TRÊN CÁC OBSERVATION TRÊN, HÃY SUY LUẬN BƯỚC TIẾP THEO:\n"
        "- Nếu bạn cần thêm thông tin hoặc cần thực hiện tiếp hành động (ví dụ: đã tìm thấy email thì đọc email; đã đọc email có giờ hẹn thì tìm lịch trống; đã có lịch trống thì đặt lịch họp hoặc tạo bản nháp), hãy GỌI CÔNG CỤ TIẾP THEO tương ứng.\n"
        "- Nếu bạn đã hoàn thành trọn vẹn yêu cầu hoặc không cần gọi thêm công cụ nào nữa, hãy TRẢ LỜI TRỰC TIẾP (Final Answer) bằng văn bản tổng kết đầy đủ, rõ ràng cho người dùng."
    )
    return prompt


def run_react_agent(user_query: str, provider, mcp_server) -> list:
    """
    [TRUE REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation
    Observation được đưa ngược lại context của LLM ở bước kế tiếp để đưa ra Dynamic Decision.
    Vòng lặp tiếp tục cho đến khi LLM tự quyết định Final Answer hoặc đạt MAX_ITERATIONS.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    conversation_history = []
    
    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Tạo prompt ngữ cảnh chứa toàn bộ lịch sử Thought -> Action -> Observation đã diễn ra
        current_prompt = format_prompt_with_history(user_query, conversation_history)
        
        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(current_prompt, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)
        
        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")
        
        # Trường hợp 1: LLM trả về văn bản hoặc đề xuất Tool dạng text
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            
            # Kiểm tra nếu LLM sinh ra Action dạng văn bản (Action: tool_name({...}))
            parsed_tool = None
            valid_tool_names = [t["name"] for t in tools_list]
            for tname in valid_tool_names:
                if tname in final_content and ("Action" in final_content or f"{tname}(" in final_content):
                    import re
                    pattern = rf"{tname}\s*\(\s*(\{{.*?\}})\s*\)"
                    match = re.search(pattern, final_content, re.DOTALL)
                    if match:
                        try:
                            targs = json.loads(match.group(1))
                            parsed_tool = (tname, targs)
                            break
                        except Exception:
                            pass
            
            if parsed_tool:
                tool_name, arguments = parsed_tool
                llm_response = {"type": "tool_call", "tool_name": tool_name, "arguments": arguments}
            else:
                print(f"🏁 [Final Answer]:\n{final_content}")
                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": thought,
                    "output": final_content,
                    "latency_ms": latency_ms
                })
                # Chỉ khi LLM chủ động đưa ra Final Answer thì mới kết thúc ReAct Loop
                break
                
        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        if llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")
            
            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            
            obs_str = json.dumps(obs_data, ensure_ascii=False)
            print(f"👁️ [Observation từ MCP Server]: {obs_str}")
            
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })
            
            # Lưu lại trạng thái của bước này vào conversation_history để chuyển tiếp cho bước sau
            conversation_history.append({
                "step": step,
                "thought": thought,
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data
            })
            
            # QUAN TRỌNG: KHÔNG break tại đây! Vòng lặp tiếp tục để LLM quan sát và suy luận bước tiếp theo!

    # Xử lý khi chạm ngưỡng MAX_ITERATIONS mà chưa xuất text
    if step >= MAX_ITERATIONS and not any(t.get("action_type") == "FINAL_ANSWER" for t in trace_logs):
        print(f"\n⚠️ [MAX ITERATIONS REACHED]: Đã đạt giới hạn {MAX_ITERATIONS} bước suy luận. Đang tổng hợp câu trả lời cuối cùng...")
        summary_prompt = f"Tổng kết kết quả cho yêu cầu '{user_query}' dựa trên các bước: {json.dumps(conversation_history, ensure_ascii=False)}"
        fallback_final = provider.generate(summary_prompt, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        print(f"🏁 [Final Answer]:\n{fallback_final}")
        trace_logs.append({
            "step": step + 1,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": "Đạt số bước tối đa, tổng hợp kết quả cuối cùng.",
            "output": fallback_final,
            "latency_ms": 10.0
        })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🤖 DAY 03 LAB: AI EMAIL & MEETING OPERATIONS AGENT")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPOfficeServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm thực tế:")
        print("   • Tra cứu email:   'Kiểm tra xem tôi có email nào chưa đọc trong hòm thư không?'")
        print("   • Đọc chi tiết:    'Đọc nội dung chi tiết email MSG-2026-004 của Sarah Davis'")
        print("   • Kiểm tra lịch:   'Kiểm tra lịch ngày 16/09/2026 xem có khung giờ rảnh nào 45 phút không?'")
        print("   • Multi-step ReAct: 'Thầy Mentor hẹn họp, hãy đọc email của thầy và lên lịch họp giúp tôi'")
        print("   • Quy định họp:    'Quy định công ty về thời lượng tối đa cho cuộc họp nội bộ'")
        print("   • Thoát phiên:     Gõ 'exit' hoặc 'quit'\n")
        while True:
            try:
                user_input = input("👤 Người dùng hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        tests = load_test_cases()
        print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        tests = load_test_cases()
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu email) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
