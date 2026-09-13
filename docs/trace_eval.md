# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Mai Quang Dũng  
> **Mã Sinh Viên / Mã Học viên:** 2A202602966  
> **Chủ đề Lựa chọn:** AI Email & Meeting Operations Agent (AI Agent hỗ trợ quản lý Email và Lịch họp)  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | **5** / 5 | Bài toán điều phối lịch họp từ email bắt buộc chia nhỏ thành chuỗi suy luận nối tiếp: (1) Đọc email để trích xuất ngữ cảnh/thời gian đề xuất -> (2) Phân tích xem khung giờ đó là khi nào -> (3) Tra cứu lịch biểu cá nhân -> (4) Ra quyết định đặt lịch nếu trống hoặc tìm khung giờ thay thế nếu bận. |
| **2. Tool Interaction** | **5** / 5 | Hệ thống bắt buộc phải tương tác với các công cụ bên ngoài qua MCP Server: Hộp thư email (`search_emails`), hệ thống lịch biểu (`check_calendar_availability`), và dịch vụ tạo cuộc họp (`schedule_meeting`). Chatbot thông thường không thể tự bịa ra email hay tự động đặt lịch vào hệ thống. |
| **3. Dynamic Decision** | **5** / 5 | Bước tiếp theo phụ thuộc hoàn toàn vào Observation của bước trước: Nếu email không có đề xuất giờ -> Agent phải hỏi lại hoặc tìm email khác; nếu lịch ngày hôm đó bị trùng (Conflict) -> Agent không được đặt bừa mà phải thông báo bận; nếu lịch trống -> Agent tự động kích hoạt tạo lịch. |
| **4. Long Horizon Goal** | **5** / 5 | Hệ thống phải duy trì trạng thái ngữ cảnh và mục tiêu xuyên suốt từ yêu cầu ban đầu của người dùng (ví dụ: "giải quyết email của đối tác Sarah") qua nhiều vòng lặp ReAct cho đến khi cuộc họp được xác nhận thành công. |
| **TỔNG ĐIỂM AGENTIC FIT** | **20 / 20** | *Đạt 20/20 điểm (> 12/20): Bài toán hoàn toàn mang tính Agentic cao cấp, vượt xa năng lực của Chatbot văn bản thông thường.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Hãy tìm email từ Mentor Nguyễn Văn A, sau đó đọc chi tiết nội dung email đó và tóm tắt các yêu cầu của thầy cho tôi.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_emails",
    "arguments": {
      "query": "Nguyễn Văn A"
    },
    "observation": {
      "status": "SUCCESS",
      "total_found": 1,
      "emails": [
        {
          "message_id": "MSG-2026-001",
          "sender": "mentor.nguyen@vinuni.edu.vn",
          "sender_name": "PGS.TS Nguyễn Văn A (Mentor)",
          "subject": "Yêu cầu hẹn họp review tiến độ đồ án tốt nghiệp AI",
          "timestamp": "15/09/2026 08:30",
          "preview": "Chào Dũng, thầy cần một buổi họp review tiến độ đồ án vào ngày 16/09/2026 khoảng 45 phút...",
          "unread": true
        }
      ]
    },
    "latency_ms": 1936.97
  },
  {
    "step": 2,
    "query": "Hãy tìm email từ Mentor Nguyễn Văn A, sau đó đọc chi tiết nội dung email đó và tóm tắt các yêu cầu của thầy cho tôi.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "read_email",
    "arguments": {
      "message_id": "MSG-2026-001"
    },
    "observation": {
      "status": "SUCCESS",
      "email": {
        "message_id": "MSG-2026-001",
        "sender": "mentor.nguyen@vinuni.edu.vn",
        "sender_name": "PGS.TS Nguyễn Văn A (Mentor)",
        "recipients": [
          "dung.mq@vinuni.edu.vn"
        ],
        "subject": "Yêu cầu hẹn họp review tiến độ đồ án tốt nghiệp AI",
        "timestamp": "15/09/2026 08:30",
        "body": "Chào Dũng, thầy đã đọc qua báo cáo tiến độ tuần trước. Thầy cần một buổi họp trực tiếp hoặc trực tuyến 45 phút vào ngày 16/09/2026 trong khoảng 10:00 - 12:00 hoặc đầu giờ chiều để chốt kiến trúc mô hình. Em kiểm tra lịch rảnh rồi tạo lịch họp và gửi lại link cho thầy nhé.",
        "has_deadline": false,
        "deadline": null
      }
    },
    "latency_ms": 1619.41
  },
  {
    "step": 3,
    "query": "Hãy tìm email từ Mentor Nguyễn Văn A, sau đó đọc chi tiết nội dung email đó và tóm tắt các yêu cầu của thầy cho tôi.",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Dựa trên nội dung email từ PGS.TS Nguyễn Văn A (`mentor.nguyen@vinuni.edu.vn`), dưới đây là tóm tắt các yêu cầu của thầy dành cho bạn:\n\n- **Nội dung yêu cầu:** Họp review tiến độ đồ án tốt nghiệp AI để chốt kiến trúc mô hình (sau khi thầy đã đọc báo cáo tiến độ tuần trước).\n- **Thời gian đề xuất:** Ngày **16/09/2026**, thời lượng **45 phút**, trong khoảng **10:00 - 12:00** hoặc đầu giờ chiều.\n- **Yêu cầu hành động từ thầy:** Kiểm tra lịch rảnh của bạn, tạo lịch họp và gửi lại link cho thầy.\n\nBạn có muốn tôi tiến hành kiểm tra lịch trống và đặt lịch họp cho khung giờ này không?",
    "latency_ms": 2042.2
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 4 lượt (TC02: search_emails, TC03: find_free_time, TC04: search_emails, TC05: read_email NOT_FOUND).
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
