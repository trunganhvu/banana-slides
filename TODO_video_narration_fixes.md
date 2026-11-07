# Tính năng thuyết minh video — Danh sách vấn đề cần khắc phục (TODO)

Nhánh: `feat/video-narration-template`
Tệp liên quan: `backend/services/tts_video_service.py`, `backend/services/prompts.py`

---

## Vấn đề 1: Phụ đề xuất ra đôi khi bị lỗi hiển thị ô vuông, đôi khi hiển thị bình thường ✅ Đã sửa trong nhánh

### Nguyên nhân gốc rễ

Trong trường Text của dòng ASS Dialogue:
- `{...}` là khối ghi đè nội tuyến (inline override block) của libass;
- Các chuỗi dấu gạch chéo ngược như `\N`, `\h`, `\n` là chuỗi thoát (escape sequence) của libass.

Khi lời thuyết minh vô tình chứa `{` / `}` / `\`, libass sẽ xử lý đoạn thoại đó như mã điều khiển, khiến kết quả kết xuất hiển thị thành ký tự lỗi hoặc ô vuông. Biến số duy nhất giữa các lần xuất trên cùng máy và cùng phông chữ là nội dung văn bản thuyết minh, do đó nguyên nhân nằm ở bước phân tích cú pháp chứ không phải phông chữ.

### Cách khắc phục

Làm sạch văn bản trước khi ghi dòng Dialogue trong `tts_video_service.py`, thay thế ba ký tự dễ bị libass hiểu nhầm bằng các ký tự tương đương an toàn:

```python
def _sanitize_ass_dialogue_text(text: str) -> str:
    return (text
        .replace('\\', '\uff3c')
        .replace('{', '\uff5b')
        .replace('}', '\uff5d')
        .replace('\n', ' ')
        .replace('\r', ''))
```

Đồng thời thay thế dòng `text = entry['text'].replace('\n', ' ').replace('\r', '')` trong `generate_ass_subtitle` bằng lời gọi hàm này.

### Nghiệm thu

- [ ] Xuất video với văn bản thuyết minh có chứa `{điểm chính}` hoặc `\N`, phụ đề hiển thị bình thường và không bị lỗi ô vuông.
- [ ] Kiểm thử hồi quy với các đoạn thuyết minh bình thường trước đó, kết quả xuất vẫn hoạt động tốt.

---

## Vấn đề 2: Thuyết minh giữa các trang nghe rời rạc, thiếu liền mạch 🔧 Cần cải tiến (Thay đổi kiến trúc)

### Nguyên nhân cốt lõi

Hiện tại Phase A của `generate_narration_video` gọi TTS tuần tự theo từng trang:

```python
for i, page in enumerate(pages_data):
    duration, alignment = generate_elevenlabs_audio_sync(narration, ...)
```

Mỗi trang là một lệnh gọi TTS độc lập, mô hình TTS khởi động lại từ đầu ở mỗi trang mà không có ngữ cảnh ngữ điệu của trang trước. Vì vậy dù văn bản có từ chuyển tiếp, âm thanh đầu mỗi trang vẫn có cảm giác ngắt quãng giữa các trang.

**Kết luận**: Để giải quyết triệt để, cần chuyển sang tổng hợp TTS một lần cho toàn bộ văn bản. Việc chỉ sửa prompt chỉ cải thiện tầng nội dung chứ không giải quyết được tầng âm học, do đó giữ nguyên prompt và tập trung cải tiến Phase A.

### Cách khắc phục (Ưu tiên luồng ElevenLabs)

Chuyển Phase A sang tổng hợp một lần rồi cắt theo dấu thời gian (timestamps), giữ nguyên logic ghép nối từ Phase B trở đi:

1. **Ghép toàn bộ văn bản**: Nối `narration_text` của tất cả các trang có thuyết minh bằng ký tự phân tách ổn định (khuyến nghị `\n\n`) thành một chuỗi dài; đồng thời ghi lại khoảng vị trí ký tự `[char_start_i, char_end_i)` của từng trang trong chuỗi dài (tính cả độ dài ký tự phân tách vào độ lệch).
2. **Gọi ElevenLabs một lần**: Gọi `client.text_to_speech.convert_with_timestamps(...)` để nhận toàn bộ tệp mp3 cùng căn chỉnh cấp độ ký tự (`character_start_times_seconds` / `character_end_times_seconds`).
3. **Ánh xạ khoảng ký tự sang khoảng thời gian**: Tra cứu `[char_start_i, char_end_i)` của mỗi trang trong dữ liệu alignment để lấy `[t_start_i, t_end_i)` tương ứng (độ chính xác mili-giây).
4. **Cắt thành tệp mp3 cho từng trang**: Dùng ffmpeg `-ss t_start_i -to t_end_i -c copy` (hoặc mã hóa lại) để cắt tệp mp3 tổng thành N tệp mp3 đơn lẻ, ghi vào vị trí `audio_paths[i]` ban đầu. `page_durations[i]` lấy giá trị `t_end_i - t_start_i`.
5. **Cắt dữ liệu alignment theo trang cho logic phụ đề**: Chia alignment tổng theo khoảng ký tự thành alignment con cho từng trang và truyền vào `_build_timed_subtitle_entries_from_alignment`. Độ chính xác đồng bộ phụ đề sẽ cao hơn so với căn chỉnh từng trang riêng lẻ.
6. **Giữ nguyên logic sau Phase B**: `audio_path`, `page_durations` và `alignment` của mỗi trang vẫn là mảng N phần tử, không cần sửa đổi mã nguồn ghép kênh ở phía sau.

Khi tổng hợp toàn văn thất bại (lỗi API, vượt giới hạn, v.v.), hệ thống tự động quay lại luồng tổng hợp theo từng trang hiện tại để đảm bảo khả năng chịu lỗi.

### Luồng edge-tts

edge-tts không có dữ liệu alignment đầu-cuối như ElevenLabs. Có hai phương án:

- **Phương án A (Khuyến nghị giữ nguyên ở giai đoạn đầu)**: Giữ cách tổng hợp theo từng trang vì bản thân edge-tts là công cụ TTS cơ bản.
- **Phương án B (Mở rộng sau)**: Sử dụng sự kiện `WordBoundary` (chứa offset/duration) trong giao diện luồng `edge_tts.Communicate` để tổng hợp toàn văn và cắt theo ranh giới từ.

### Nghiệm thu

- [ ] Video thuyết minh từ ba trang trở lên khi nghe thử có ngữ điệu tự nhiên, liền mạch giữa các trang.
- [ ] Sai số đồng bộ giữa phụ đề và giọng đọc < 200ms.
- [ ] Số lần gọi ElevenLabs giảm từ N trang xuống 1 lần; thời gian xuất tổng thể và tỷ lệ lỗi ở mức chấp nhận được.
- [ ] Khi tổng hợp toàn văn thất bại, hệ thống chuyển mượt mà về chế độ tổng hợp từng trang mà không làm gián đoạn quá trình xuất.
- [ ] Luồng tạo phụ đề `_build_timed_subtitle_entries_from_alignment` hiện tại vẫn hoạt động bình thường với dấu thời gian chính xác hơn.

### Những điều không nên làm

- Không thêm hiệu ứng âm lượng mờ dần (fade in/out) hoặc đệm khoảng lặng ở điểm nối giữa các trang chỉ để che giấu vết cắt âm thanh.
- Không sửa đổi mã nguồn liên quan đến prompt hoặc phông chữ cho vấn đề này.
