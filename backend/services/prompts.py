"""
Prompt templates and generators for AI operations.

Organized by function:
1. Helpers & Language Config
2. Outline Prompts
3. Description Prompts
4. Image Generation Prompts
5. Content Extraction Prompts
6. Narration Prompts
7. Template Analysis & Auto-match Prompts
"""
import json
import logging
import os
import re
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


def _build_prompt(main_prompt: str, reference_content: str = "", tag: str = "prompt") -> str:
    """Ghép nối nội dung tệp tham khảo vào prompt nếu có."""
    if reference_content and reference_content.strip():
        prompt = f"{main_prompt}\n\n{reference_content}"
    else:
        prompt = main_prompt

    logger.debug(f"[{tag}] Final prompt:\n{prompt}")
    return prompt


def _get_original_input(project_context: 'ProjectContext') -> str:
    """Lấy nội dung yêu cầu đầu vào ban đầu của người dùng."""
    return project_context.idea_prompt or project_context.description_text or ""


def _get_original_input_labeled(project_context: 'ProjectContext') -> str:
    """Lấy nội dung đầu vào ban đầu có gắn nhãn mô tả."""
    if project_context.idea_prompt:
        return f"Yêu cầu ban đầu của người dùng:\n{project_context.idea_prompt}\n\n"
    elif project_context.description_text:
        return f"Văn bản mô tả ban đầu của người dùng:\n{project_context.description_text}\n\n"
    return ""


def _get_previous_requirements_text(previous_requirements: Optional[List[str]]) -> str:
    """Định dạng danh sách các yêu cầu chỉnh sửa trước đó."""
    if not previous_requirements:
        return ""
    req_lines = [f"{i+1}. {req}" for i, req in enumerate(previous_requirements)]
    return "Các yêu cầu đã đưa ra trước đây:\n" + "\n".join(req_lines) + "\n\n"


def _normalize_word_count(val: Any, default: int, lower: int, upper: int) -> int:
    """Chuẩn hóa số lượng từ."""
    try:
        v = int(val)
        return max(lower, min(upper, v))
    except (TypeError, ValueError):
        return default


def get_default_narration_generation_config() -> dict:
    """Lấy cấu hình mặc định cho việc tạo kịch bản thuyết minh."""
    return dict(DEFAULT_NARRATION_CONFIG)


def normalize_narration_generation_config(user_config: Optional[dict]) -> dict:
    """Chuẩn hóa cấu hình tạo kịch bản thuyết minh."""
    config = dict(DEFAULT_NARRATION_CONFIG)
    if not user_config:
        return config

    for key in ('speaker_persona', 'target_audience', 'speech_tone', 'presentation_topic'):
        val = user_config.get(key)
        if isinstance(val, str) and val.strip():
            config[key] = val.strip()

    min_words = _normalize_word_count(
        user_config.get('min_words'),
        DEFAULT_NARRATION_CONFIG['min_words'],
        _NARRATION_MIN_WORDS_LOWER_BOUND,
        _NARRATION_MAX_WORDS_UPPER_BOUND,
    )
    max_words = _normalize_word_count(
        user_config.get('max_words'),
        DEFAULT_NARRATION_CONFIG['max_words'],
        _NARRATION_MIN_WORDS_LOWER_BOUND,
        _NARRATION_MAX_WORDS_UPPER_BOUND,
    )
    if min_words > max_words:
        min_words = max_words
    config['min_words'] = min_words
    config['max_words'] = max_words
    return config


def parse_narration_generation_result(raw_text: str) -> dict:
    """Phân tích kết quả trả về từ mô hình khi tạo kịch bản thuyết minh."""
    raw = (raw_text or '').strip()
    match = re.search(r'```(?:json)?\s*([\\s\\S]*?)\s*```', raw)
    candidate = match.group(1).strip() if match else raw

    data = None
    try:
        data = json.loads(candidate)
    except Exception:
        first_brace = candidate.find('{')
        last_brace = candidate.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            try:
                data = json.loads(candidate[first_brace:last_brace + 1])
            except Exception:
                data = None

    if not isinstance(data, dict):
        return {
            'narration': raw,
            'word_count': len(raw.split()),
            'speaker_persona': '',
            'speech_tone': '',
            'presentation_topic': '',
            'key_points_covered': [],
        }

    narration = str(data.get('narration') or '').strip()
    key_points = data.get('key_points_covered')
    if not isinstance(key_points, list):
        key_points = []
    else:
        key_points = [str(p).strip() for p in key_points if str(p).strip()]

    return {
        'narration': narration,
        'word_count': len(narration.split()),
        'speaker_persona': str(data.get('speaker_persona') or '').strip(),
        'speech_tone': str(data.get('speech_tone') or '').strip(),
        'presentation_topic': str(data.get('presentation_topic') or '').strip(),
        'key_points_covered': key_points,
    }


def _format_extra_field_instructions(extra_fields: list = None) -> str:
    """Định dạng hướng dẫn cho các trường bổ sung."""
    if not extra_fields:
        return ""
    lines = []
    for f in extra_fields:
        inst = EXTRA_FIELD_INSTRUCTIONS.get(f, f"{f}: [Gợi ý cho {f}, nếu không có thì bỏ qua dòng này]")
        lines.append(inst)
    return "\n" + "\n".join(lines)


def _format_reference_files_xml(reference_files_content: str = "") -> str:
    """Định dạng nội dung tệp tham khảo bọc trong thẻ XML."""
    if not reference_files_content or not reference_files_content.strip():
        return ""
    return f"""\n\n<reference_materials>\n{reference_files_content.strip()}\n</reference_materials>\n"""


def _format_requirements(requirements: str = None, section_type: str = "outline") -> str:
    """Định dạng yêu cầu của người dùng."""
    if not requirements or not requirements.strip():
        return ""
    type_name = "dàn ý" if section_type == "outline" else "mô tả"
    return f"Yêu cầu bổ sung cho việc tạo {type_name}:\n{requirements.strip()}\n\n"


def get_default_output_language() -> str:
    """Lấy ngôn ngữ xuất mặc định từ biến môi trường hoặc cấu hình."""
    return os.getenv('OUTPUT_LANGUAGE', 'vi')


def get_language_instruction(language: str = None) -> str:
    """Lấy chỉ dẫn ngôn ngữ xuất."""
    lang = language if language else get_default_output_language()
    config = LANGUAGE_CONFIG.get(lang, LANGUAGE_CONFIG['vi'])
    return config['instruction']


def get_ppt_language_instruction(language: str = None) -> str:
    """Lấy chỉ dẫn ngôn ngữ văn bản trên slide."""
    lang = language if language else get_default_output_language()
    config = LANGUAGE_CONFIG.get(lang, LANGUAGE_CONFIG['vi'])
    return config['ppt_text']


LANGUAGE_CONFIG = {
    'vi': {
        'name': 'Tiếng Việt',
        'instruction': 'Vui lòng xuất toàn bộ nội dung bằng tiếng Việt.',
        'ppt_text': 'Văn bản trên slide PPT vui lòng sử dụng hoàn toàn bằng tiếng Việt.'
    },
    'zh': {
        'name': 'Tiếng Việt',
        'instruction': 'Vui lòng xuất toàn bộ nội dung bằng tiếng Việt.',
        'ppt_text': 'Văn bản trên slide PPT vui lòng sử dụng hoàn toàn bằng tiếng Việt.'
    },
    'ja': {
        'name': 'English',
        'instruction': 'Please output in English.',
        'ppt_text': 'Use English for PPT text.'
    },
    'en': {
        'name': 'English',
        'instruction': 'Please output all in English.',
        'ppt_text': 'Use English for PPT text.'
    },
    'auto': {
        'name': 'Tự động',
        'instruction': 'Vui lòng xuất toàn bộ bằng tiếng Việt. ',
        'ppt_text': ''
    }
}

DETAIL_LEVEL_SPECS = {
    'concise': 'Văn bản được nén và cô đọng tối đa, mỗi ý chính dùng một từ khóa hoặc số liệu trọng tâm, ví dụ: Hiệu suất ↑80%',
    'default': 'Rõ ràng, súc tích, mỗi ý chính trong khoảng 15-20 từ, ưu tiên dùng cụm từ ngắn gọn thay vì câu dài phức tạp; nội dung trang từ 2-6 câu để phục vụ thuyết trình thay vì đọc thay diễn giả.',
    'detailed': 'Bám sát nội dung gốc với thông tin đầy đủ, chi tiết và logic chặt chẽ.',
}

DEFAULT_NARRATION_CONFIG = {
    'speaker_persona': 'giảng viên đại học tận tâm, uyên bác và giàu kinh nghiệm',
    'target_audience': 'đối tượng đại chúng, không yêu cầu chuyên môn kỹ thuật sâu',
    'speech_tone': 'mang tính phân tích, dựa trên số liệu và chuyên nghiệp cao',
    'presentation_topic': 'các ý tưởng chính và luận điểm cốt lõi của bài thuyết trình',
    'min_words': 100,
    'max_words': 200,
}

_NARRATION_MIN_WORDS_LOWER_BOUND = 30
_NARRATION_MAX_WORDS_UPPER_BOUND = 300

EXTRA_FIELD_INSTRUCTIONS = {
    'Hình ảnh & Tư liệu': (
        'Hình ảnh & Tư liệu: [Đề xuất hình ảnh, biểu đồ, icon, minh họa hoặc ảnh tư liệu cần hiển thị; '
        'không viết văn bản trang và không viết vị trí sắp đặt. Tối đa 3 mục; nếu không cần thì bỏ qua trường này]'
    ),
    'Bố cục & Trọng tâm': (
        'Bố cục & Trọng tâm: [Tối đa hai câu: câu 1 nêu cấu trúc bố cục (như tiêu đề trên nội dung dưới, '
        'chia cột trái phải, dạng thẻ lưới...); câu 2 chỉ rõ điểm nhấn thị giác chính của trang. '
        'Chỉ mô tả cách tổ chức bố cục, không đưa thêm nội dung mới, không nhắc lại văn bản trang]'
    ),
    'Ghi chú thuyết trình': (
        'Ghi chú thuyết trình: [Gợi ý kịch bản mở rộng cho người nói, giải thích thêm thông tin, '
        'không hiển thị lên trang slide]'
    ),
}

_OUTLINE_JSON_FORMAT = """\
1. Simple format (cho bài thuyết trình ngắn không chia phần lớn):
[{"title": "tiêu đề 1", "points": ["ý chính 1", "ý chính 2"]}, {"title": "tiêu đề 2", "points": ["ý chính 1", "ý chính 2"]}]

2. Part-based format (cho bài thuyết trình dài có chia chương/phần):
[{"part": "Tên phần 1", "pages": [{"title": "tiêu đề 1", "points": ["ý chính 1", "ý chính 2"]}]}]
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 2. Dàn ý Prompts
# ═══════════════════════════════════════════════════════════════════════════════

def get_outline_generation_prompt(project_context: 'ProjectContext', language: str = None) -> str:
    """Tạo prompt xuất dàn ý dạng JSON từ ý tưởng."""
    idea_prompt = project_context.idea_prompt or ""

    prompt = (f"""\
You are a helpful assistant that generates an outline for a PPT presentation based on a user prompt.

You can organize the content in two ways:
{_OUTLINE_JSON_FORMAT}

Important rules:
- Generate a professional and well-structured outline
- If the topic naturally divides into distinct phases, topics, or chapters, use the part-based format
- For simple or short presentations, use the simple format
- The cover page and table of contents belong to the deck as a whole, never to a part — do not nest them under a "part"
- Each page should have a clear title and 2-4 key points
- If a page argues something, phrase its FIRST point as that page's takeaway assertion (found in or implied by the user's prompt); functional pages (cover, TOC, section divider) are exempt
- Do not put final slide copy, exact page text, long evidence lists, or detailed visual/layout instructions in the outline points

{_format_requirements(project_context.outline_requirements, "outline")}Now generate the outline for this idea:
{idea_prompt}

Return only the JSON, don't include any other text.
{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_outline_generation_prompt')


def get_outline_generation_prompt_markdown(project_context: 'ProjectContext', language: str = None) -> str:
    """Tạo prompt xuất dàn ý dạng Markdown (hỗ trợ streaming)."""
    idea_prompt = project_context.idea_prompt or ""

    prompt = (f"""\
You are a helpful assistant that generates an outline for a PPT presentation based on a user prompt.

Output format rules:
- Use `# Part Name` for major sections (only if the presentation naturally divides into distinct phases or chapters)
- The cover page and table of contents belong to the deck as a whole, never to a part — output them BEFORE any `# Part` heading
- Use `## Page Title` for each page
- Under each page, use `- ` bullet points for the 2-4 key points
- If a page argues something, phrase its FIRST point as that page's takeaway assertion; functional pages are exempt
- Do not put final slide copy, exact page text, or detailed visual instructions in the outline points
- Do NOT wrap in code blocks (no ```markdown or ```)

Example:
# Bối cảnh & Cơ hội
## Nhu cầu chuyển đổi giải pháp toàn diện
- Nhu cầu đang chuyển từ công cụ đơn lẻ sang giải pháp toàn diện, đây là động lực tăng trưởng thực sự.
- Dữ liệu 3 năm qua cho thấy tốc độ tăng trưởng vượt trội của mô hình mới.

{_format_requirements(project_context.outline_requirements, "outline")}Now generate the outline for this idea:
{idea_prompt}

{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_outline_generation_prompt_markdown')


def get_outline_parsing_prompt(project_context: 'ProjectContext', language: str = None) -> str:
    """Tạo prompt phân tích dàn ý thô sang JSON."""
    outline_text = project_context.outline_text or ""

    prompt = (f"""\
You are a helpful assistant that analyzes a user-provided PPT outline and converts it into a structured format.

The user has provided the following outline text:
{outline_text}

You can organize the content in two ways:
{_OUTLINE_JSON_FORMAT}

Important rules:
- Parse the user's text into the structured format
- Identify page titles and key points from the text
- If the text has clear sections/parts, use the part-based format
- Cover page and TOC belong to the deck as a whole, never to a part
- If a page argues something, phrase its FIRST point as that page's takeaway assertion
- Return only the JSON, don't include any other text.

{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_outline_parsing_prompt')


def get_outline_parsing_prompt_markdown(project_context: 'ProjectContext', language: str = None) -> str:
    """Tạo prompt phân tích dàn ý thô sang Markdown."""
    outline_text = project_context.outline_text or ""

    prompt = (f"""\
You are a helpful assistant that analyzes a user-provided PPT outline and normalizes it into Markdown format.

The user has provided the following outline text:
{outline_text}

Output format rules:
- Use `# Part Name` for major sections (only if text has clear sections)
- Use `## Page Title` for each page
- Under each page, use `- ` bullet points for key points
- Cover page and TOC belong to the deck as a whole, never to a part
- If a page argues something, phrase its FIRST point as that page's takeaway assertion
- Do NOT wrap in code blocks

{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_outline_parsing_prompt_markdown')


def get_description_to_outline_prompt(project_context: 'ProjectContext', language: str = None) -> str:
    """Trích xuất dàn ý JSON từ văn bản mô tả."""
    description_text = project_context.description_text or ""

    prompt = (f"""\
You are a helpful assistant that extracts an outline structure from a detailed PPT description text.

The user has provided the following description text:
{description_text}

You can organize the content in two ways:
{_OUTLINE_JSON_FORMAT}

Important rules:
- Extract the outline structure from the description text
- Identify page titles and key points
- If text has clear sections, use the part-based format
- The points should be concise summaries of the main content for each page
- If a page argues something, phrase its FIRST point as that page's takeaway assertion
- Return only the JSON, don't include any other text.

{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_description_to_outline_prompt')


def get_description_to_outline_prompt_markdown(project_context: 'ProjectContext',
                                               language: str = None,
                                               extra_fields: list = None) -> str:
    """Tạo dàn ý và mô tả trang từ văn bản mô tả ban đầu (dạng Markdown stream)."""
    description_text = project_context.description_text or ""
    detail_level = "default"
    description_format = f"""\
--- Văn bản trang ---
[Tại đây sử dụng trực tiếp markdown để đưa văn bản chính, yêu cầu mức độ chi tiết: {DETAIL_LEVEL_SPECS[detail_level]}. Có thể bao gồm công thức LaTeX, bảng biểu... Không lặp lại tiêu đề trang, không đưa ý đồ thiết kế của người dùng vào văn bản trang.]

--- Kết thúc văn bản trang ---
{_format_extra_field_instructions(extra_fields)}

Hình ảnh tư liệu (đường dẫn cục bộ bắt đầu bằng /files/) được chèn theo định dạng markdown, ví dụ: ![mô tả](/files/xxx/image.png), ưu tiên ghi vào trường "Hình ảnh & Tư liệu"; nếu trường này không bật thì đính kèm ngay sau văn bản trang.
"""

    prompt = (f"""\
You are a helpful assistant that analyzes a user-provided PPT description text and converts it into page-by-page slide structure.

The user has provided the following description text:
{description_text}

Your task is to first split the description into pages, then produce the outline and the page description for each page from that same split.
Each output page must contain both an outline-level narrative structure and the page description.
The parser depends on the HTML comment markers below. Do not translate or modify them.

Output rules:
- Use `# Part Name` for major sections (only if the text has clear parts/chapters)
- Use `## Page Title` for each page
- Under each page, output `<!-- OUTLINE_POINTS -->` followed by one or two `- ` bullet points that describe what the slide should cover at the outline level
- Then output `<!-- PAGE_DESCRIPTION -->` followed by the corresponding page description text using this format:
{description_format}
- Preserve layout, style, material, and content details in the page description
- If a page argues something, phrase its FIRST outline point as that page's takeaway assertion
- Use `<!-- PAGE_END -->` after each page
- Do NOT wrap in code blocks or add any extra text

Example:
## Tổng quan cơ hội thị trường
<!-- OUTLINE_POINTS -->
- Nhu cầu đang chuyển từ công cụ đơn lẻ sang giải pháp toàn diện, đây là động lực tăng trưởng thực sự.
- Dùng số liệu tăng trưởng 3 năm để minh họa quy mô thị trường và sự thay đổi cấu trúc.
<!-- PAGE_DESCRIPTION -->
--- Văn bản trang ---
- Thị trường mục tiêu duy trì tốc độ tăng trưởng cao trong 3 năm qua
- Nhu cầu chuyển đổi từ công cụ đơn lẻ sang giải pháp toàn diện

--- Kết thúc văn bản trang ---

Hình ảnh & Tư liệu: Biểu đồ đường: đường cong tăng trưởng thị trường mục tiêu 3 năm qua, làm nổi bật tốc độ tăng trưởng
Bố cục & Trọng tâm: Tiêu đề ở trên nội dung ở dưới, bên trái là các ý chính bên phải là biểu đồ xu hướng; biểu đồ là điểm nhấn thị giác
<!-- PAGE_END -->

Now split the description text above and output the page-by-page structure. Output `<!-- END -->` on the last line when finished.
{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_description_to_outline_prompt_markdown')


def get_outline_refinement_prompt(current_outline: List[Dict], user_requirement: str,
                                   project_context: 'ProjectContext',
                                   previous_requirements: Optional[List[str]] = None,
                                   language: str = None) -> str:
    """Tạo prompt chỉnh sửa dàn ý theo yêu cầu người dùng."""
    if not current_outline or len(current_outline) == 0:
        outline_text = "(Dàn ý hiện tại đang trống)"
    else:
        outline_text = json.dumps(current_outline, ensure_ascii=False, indent=2)

    prompt = (f"""\
You are a helpful assistant that modifies PPT outlines based on user requirements.

Current outline:
{outline_text}

{_get_previous_requirements_text(previous_requirements)}**Người dùng đưa ra yêu cầu mới: {user_requirement}**

Modify the outline according to the user's requirements while maintaining structural integrity.
Return only the modified outline in the same JSON format, don't include any other text.
{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_outline_refinement_prompt')


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Mô tả Prompts
# ═══════════════════════════════════════════════════════════════════════════════

def get_page_description_prompt(project_context: 'ProjectContext', outline: list,
                                page_outline: dict, page_index: int,
                                part_info: str = "",
                                language: str = None,
                                detail_level: str = "default",
                                extra_fields: list = None) -> str:
    """Tạo prompt mô tả cho một trang slide đơn lẻ."""
    original_input = _get_original_input(project_context)

    prompt = (f"""\
Chúng ta đang tạo mô tả nội dung cho từng trang của bài thuyết trình PPT.
Yêu cầu ban đầu của người dùng là:\n{original_input}\n
Dàn ý hoàn chỉnh:\n{outline}\n{part_info}
{_format_requirements(project_context.description_requirements, "description")}Bây giờ hãy tạo mô tả cho trang thứ {page_index}:
{page_outline}
{"**Trừ khi có yêu cầu đặc biệt, trang bìa (trang 1) cần giữ sự tối giản tuyệt đối, chỉ đặt tiêu đề, phụ đề và tên diễn giả, không thêm hình ảnh tư liệu.**" if page_index == 1 else ""}
## Lưu ý quan trọng
- Nội dung trong "Văn bản trang" sẽ được hiển thị nguyên văn lên slide PPT: chỉ viết những chữ thực sự xuất hiện trên trang, không bao gồm lời giải thích, ghi chú hay ý đồ thiết kế (ý đồ thiết kế ghi vào các trường tương ứng bên dưới).
- Quy tắc tiêu đề: Tiêu đề trang nội dung ưu tiên viết dưới dạng câu khẳng định/luận điểm - tóm tắt kết luận của trang trong một câu (ví dụ: "Nút thắt năng lực tính toán là nguyên nhân cốt lõi của các mùa đông AI"), thay vì một cụm từ chủ đề chung chung. Luận điểm chính (takeaway) đầu tiên trong dàn ý là nguồn ưu tiên hàng đầu cho tiêu đề. Các trang chức năng giữ tiêu đề ngắn gọn.

## Định dạng xuất

--- Văn bản trang ---

[Tại đây sử dụng trực tiếp markdown để đưa văn bản chính, yêu cầu mức độ chi tiết: {DETAIL_LEVEL_SPECS[detail_level]}, có thể bao gồm công thức LaTeX, bảng biểu, không lặp lại tiêu đề trang]

--- Kết thúc văn bản trang ---
{_format_extra_field_instructions(extra_fields)}

## Về hình ảnh tư liệu
Nếu trong tệp tham khảo có URL tệp cục bộ bắt đầu bằng /files/ (ví dụ: /files/mineru/xxx/image.png), hãy chèn theo định dạng markdown (như ![Mô tả ảnh](/files/mineru/xxx/image.png)), đưa vào trường "Hình ảnh & Tư liệu"; nếu trường này không bật thì đính kèm ngay sau văn bản trang. Các hình ảnh này sẽ được đưa vào trang PPT.
{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_page_description_prompt')


def get_all_descriptions_stream_prompt(project_context: 'ProjectContext',
                                       outline: list,
                                       flat_pages: list,
                                       language: str = None,
                                       detail_level: str = "default",
                                       extra_fields: list = None) -> str:
    """Tạo prompt xuất toàn bộ mô tả các trang (dạng stream)."""
    original_input = _get_original_input(project_context)

    outline_lines = []
    for i, page in enumerate(flat_pages):
        part_str = f"  [Phần: {page['part']}]" if page.get('part') else ""
        points_str = ", ".join(page.get('points', []))
        outline_lines.append(f"Trang {i + 1}: {page.get('title', '')}{part_str}\n  Ý chính: {points_str}")
    pages_outline_text = "\n".join(outline_lines)

    prompt = (f"""\
Chúng ta đang tạo mô tả nội dung cho từng trang của bài thuyết trình PPT.
Yêu cầu ban đầu của người dùng là:\n{original_input}\n
Dàn ý hoàn chỉnh như sau:
{pages_outline_text}

{_format_requirements(project_context.description_requirements, "description")}Hãy lần lượt tạo mô tả cho từng trang. Đầu tiên xuất thẻ `<!-- BEGIN -->` để đánh dấu bắt đầu, sau đó xuất nội dung từng trang, mỗi trang kết thúc bằng `<!-- PAGE_END -->`, sau khi hoàn thành tất cả thì xuất `<!-- END -->`.

## Lưu ý quan trọng
- Nội dung trong "Văn bản trang" sẽ được hiển thị nguyên văn lên slide PPT: chỉ viết những chữ thực sự xuất hiện trên trang, không bao gồm lời giải thích, ghi chú hay ý đồ thiết kế (ý đồ thiết kế ghi vào các trường tương ứng bên dưới).
- Quy tắc tiêu đề: Tiêu đề trang nội dung ưu tiên viết dưới dạng câu khẳng định/luận điểm - tóm tắt kết luận của trang trong một câu (ví dụ: "Nút thắt năng lực tính toán là nguyên nhân cốt lõi của các mùa đông AI"), thay vì một cụm từ chủ đề chung chung. Luận điểm chính đầu tiên trong dàn ý là nguồn ưu tiên hàng đầu cho tiêu đề.
- **Trang đầu tiên (trang bìa) giữ tối giản**, chỉ đặt tiêu đề, phụ đề, diễn giả, không thêm tư liệu.
- Yêu cầu mức độ chi tiết: {DETAIL_LEVEL_SPECS[detail_level]}
- Mỗi trang bao gồm "Văn bản trang" và các trường bổ sung bên dưới. Hình ảnh tư liệu (đường dẫn bắt đầu bằng /files/) chèn theo định dạng markdown, ưu tiên ghi vào trường "Hình ảnh & Tư liệu".

## Định dạng xuất
```
<!-- BEGIN -->

--- Văn bản trang ---
[Nội dung văn bản trang 1, có thể bao gồm tiêu đề, phụ đề, các điểm chính, công thức LaTeX, bảng biểu... Không đưa ý đồ thiết kế của người dùng vào văn bản trang]

--- Kết thúc văn bản trang ---
{_format_extra_field_instructions(extra_fields)}
<!-- PAGE_END -->

--- Văn bản trang ---
[Nội dung văn bản trang 2]

--- Kết thúc văn bản trang ---
{_format_extra_field_instructions(extra_fields)}
<!-- PAGE_END -->
...
<!-- END -->
```

Bây giờ hãy bắt đầu tạo, nghiêm ngặt tuân thủ định dạng trên.
{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_all_descriptions_stream_prompt')


def get_description_split_prompt(project_context: 'ProjectContext',
                                 outline: List[Dict],
                                 language: str = None) -> str:
    """Tách văn bản mô tả hoàn chỉnh thành mô tả từng trang dựa theo dàn ý."""
    outline_json = json.dumps(outline, ensure_ascii=False, indent=2)
    description_text = project_context.description_text or ""

    prompt = (f"""\
You are a helpful assistant that splits a complete PPT description text into individual page descriptions.

The user has provided a complete description text:
{description_text}

We have already extracted the outline structure:
{outline_json}

Your task is to split the description text into individual page descriptions based on the outline structure.
For each page in the outline, extract the corresponding description from the original text.

Return a JSON array where each element corresponds to a page in the outline (in the same order).
Each element should be a string containing the page description in the following format:

Tiêu đề trang: [Tiêu đề trang]

Văn bản trang:
- [Ý chính 1]
- [Ý chính 2]
...

Hình ảnh & Tư liệu: [Hình ảnh/biểu đồ/minh họa hiển thị trên trang này, nếu không có thì bỏ qua dòng này]
Bố cục & Trọng tâm: [Cấu trúc bố cục và trọng tâm thị giác, nếu không có thì bỏ qua dòng này]

Ví dụ định dạng xuất:
[
    "Tiêu đề trang: Sự ra đời của Trí tuệ Nhân tạo\nVăn bản trang:\n- Năm 1950, Alan Turing đề xuất phép thử Turing\n- Đặt nền móng lý thuyết vững chắc cho AI\n\nBố cục & Trọng tâm: Tiêu đề căn giữa, phông chữ lớn nổi bật",
    "Tiêu đề trang: Lịch sử phát triển của AI\nVăn bản trang:\n- Thập niên 1950: Chủ nghĩa ký hiệu...",
    ...
]

Important rules:
- Split the description text according to the outline structure
- Each page description should match the corresponding page in the outline
- Preserve all important content from the original text, including layout details, style requirements, material specifications, and design requirements
- If the user described materials or images for a page, put them in the "Hình ảnh & Tư liệu" line; if the user described layout, composition, or emphasis, put them in the "Bố cục & Trọng tâm" line
- Keep the format consistent with the example above

Now split the description text into individual page descriptions. Return only the JSON array, don't include any other text.
{get_language_instruction(language)}
""")
    logger.debug(f"[get_description_split_prompt] Final prompt:\n{prompt}")
    return prompt


def get_descriptions_refinement_prompt(current_descriptions: List[Dict], user_requirement: str,
                                       project_context: 'ProjectContext',
                                       outline: List[Dict] = None,
                                       previous_requirements: Optional[List[str]] = None,
                                       language: str = None) -> str:
    """Chỉnh sửa mô tả trang theo yêu cầu của người dùng."""
    outline_text = "(Hiện chưa có nội dung)"
    if outline:
        outline_json = json.dumps(outline, ensure_ascii=False, indent=2)
        outline_text = f"\n\nDàn ý PPT hoàn chỉnh:\n{outline_json}\n"

    all_descriptions_text = "Mô tả hiện tại của tất cả các trang:\n\n"
    has_any_description = False
    for desc in current_descriptions:
        page_num = desc.get('index', 0) + 1
        title = desc.get('title', 'Chưa đặt tên')
        content = desc.get('description_content', '')
        if isinstance(content, dict):
            extra_fields = content.get('extra_fields') or {}
            content = content.get('text') or ''
            if isinstance(extra_fields, dict):
                field_lines = [
                    f"{name}: {value}" for name, value in extra_fields.items()
                    if value is not None and str(value).strip() != ""
                ]
                if field_lines:
                    content = '\n'.join([content, *field_lines]) if content else '\n'.join(field_lines)

        if content:
            has_any_description = True
            all_descriptions_text += f"--- Trang {page_num}: {title} ---\n{content}\n\n"
        else:
            all_descriptions_text += f"--- Trang {page_num}: {title} ---\n(Hiện tại chưa có nội dung)\n\n"

    if not has_any_description:
        all_descriptions_text = "Mô tả hiện tại của tất cả các trang:\n\n(Hiện tại chưa có nội dung, cần tạo mới dựa theo dàn ý)\n\n"

    prompt = (f"""\
You are a helpful assistant that modifies PPT page descriptions based on user requirements.
{_get_original_input_labeled(project_context)}{outline_text}
{all_descriptions_text}
{_get_previous_requirements_text(previous_requirements)}
**Người dùng đưa ra yêu cầu mới: {user_requirement}**

Hãy điều chỉnh mô tả của các trang theo yêu cầu:
- Sửa tiêu đề và nội dung trang
- Điều chỉnh mức độ chi tiết của văn bản
- Thêm hoặc bớt các điểm chính
- Điều chỉnh cấu trúc và cách diễn đạt
- Đảm bảo tất cả mô tả trang đều thỏa mãn yêu cầu người dùng

Định dạng cho mỗi trang:
Tiêu đề trang: [Tiêu đề trang]

Văn bản trang:
- [Ý chính 1]
- [Ý chính 2]
...
Hình ảnh & Tư liệu: [Hình ảnh/biểu đồ/minh họa hiển thị trên trang này, nếu không có thì bỏ qua dòng này]
Bố cục & Trọng tâm: [Cấu trúc bố cục và trọng tâm thị giác, nếu không có thì bỏ qua dòng này]

Lưu ý:
- "Văn bản trang" sẽ được hiển thị nguyên văn lên slide, không đưa ý đồ thiết kế vào đó; ý đồ thiết kế ghi vào trường tương ứng phía trên.
- Giữ nguyên các trường bổ sung đã có và điều chỉnh theo yêu cầu, không tự ý xóa bỏ.
- Nếu tệp tham khảo có URL bắt đầu bằng /files/, hãy chèn ảnh theo định dạng markdown: ![Mô tả ảnh](/files/mineru/xxx/image.png).

Trả về một mảng JSON, mỗi phần tử là một chuỗi tương ứng với mô tả đã chỉnh sửa của từng trang.

Ví dụ định dạng xuất:
[
    "Tiêu đề trang: Sự ra đời của Trí tuệ Nhân tạo\nVăn bản trang:\n- Năm 1950, Alan Turing đề xuất phép thử Turing...",
    "Tiêu đề trang: Lịch sử phát triển của AI\nVăn bản trang:\n- Thập niên 1950: Chủ nghĩa ký hiệu...",
    ...
]

Bây giờ hãy sửa đổi các mô tả trang theo yêu cầu, chỉ trả về mảng JSON, không kèm thêm chữ nào khác.
{get_language_instruction(language)}
""")
    return _build_prompt(prompt, project_context.reference_files_content, tag='get_descriptions_refinement_prompt')


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Tạo Ảnh Prompts
# ═══════════════════════════════════════════════════════════════════════════════

def get_image_generation_prompt(page_desc: str, outline_text: str,
                                current_section: str,
                                has_material_images: bool = False,
                                extra_requirements: str = None,
                                language: str = None,
                                has_template: bool = True,
                                page_index: int = 1,
                                aspect_ratio: str = "16:9",
                                page_style_text: str = None) -> str:
    """Tạo prompt cho mô hình sinh ảnh slide."""
    material_images_note = ""
    if has_material_images:
        material_images_note = (
            "\n\nGợi ý: " + ("Ngoài ảnh mẫu tham khảo (dùng cho phong cách), người dùng còn cung cấp thêm ảnh tư liệu." if has_template else "Người dùng đã cung cấp thêm ảnh tư liệu.") +
            " Các ảnh tư liệu này là những thành phần có thể sử dụng, bạn có thể chọn ảnh, biểu tượng, biểu đồ hoặc chi tiết thị giác phù hợp"
            " để tích hợp trực tiếp vào trang PPT. Hãy lựa chọn và kết hợp các thành phần một cách thông minh theo nhu cầu nội dung trang."
        )

    extra_req_text = ""
    if extra_requirements and extra_requirements.strip():
        extra_req_text = f"\n\nYêu cầu bổ sung (bắt buộc tuân thủ):\n{extra_requirements}\n"

    template_style_guideline = "- Phối màu và ngôn ngữ thiết kế tương đồng chặt chẽ với ảnh mẫu tham khảo." if has_template else "- Thiết kế chặt chẽ theo mô tả phong cách."
    forbidden_template_text_guidline = "- Chỉ tham khảo phong cách thiết kế, tuyệt đối không xuất hiện chữ từ ảnh mẫu.\n" if has_template else ""

    page_style_block = ""
    if page_style_text and page_style_text.strip():
        page_style_block = (
            "\n\n<page_style>\n"
            f"{page_style_text.strip()}\n"
            "</page_style>\n"
            "- Phải tuân thủ phong cách thị giác, bảng màu và ngôn ngữ bố cục trong page_style ở trên."
        )

    prompt = (f"""\
Bạn là một nhà thiết kế UI/UX bài thuyết trình chuyên nghiệp hàng đầu, chuyên tạo ra các trang slide PPT xuất sắc.
Mô tả nội dung của trang slide hiện tại như sau:
<page_description>
{page_desc}
</page_description>
{page_style_block}

<design_guidelines>
- Yêu cầu chữ sắc nét, rõ ràng, hình ảnh đạt độ phân giải cao 4K, tỷ lệ {aspect_ratio}.
{template_style_guideline}
- Dựa theo nội dung và yêu cầu để thiết kế bố cục hoàn hảo nhất, kết xuất đầy đủ, chính xác, không thừa không thiếu toàn bộ văn bản trong phần "Văn bản trang".
- Trừ khi thật sự cần thiết, tuyệt đối không hiển thị các ký hiệu định dạng markdown (như # và *).
{forbidden_template_text_guidline}
</design_guidelines>
{get_ppt_language_instruction(language)}
{material_images_note}{extra_req_text}

{"**Lưu ý: Trang hiện tại là trang bìa của bài thuyết trình PPT, hãy áp dụng kỹ thuật mỹ thuật thiết kế bìa chuyên nghiệp, làm nổi bật tiêu đề chính, phân cấp rõ ràng chính phụ để thu hút người xem ngay từ cái nhìn đầu tiên.**" if page_index == 1 else ""}
""")
    logger.debug(f"[get_image_generation_prompt] Final prompt:\n{prompt}")
    return prompt


def get_image_edit_prompt(edit_instruction: str, original_description: str = None) -> str:
    """Tạo prompt chỉnh sửa hình ảnh."""
    if original_description:
        if "Tư liệu khác" in original_description:
            original_description = original_description.split("Tư liệu khác")[0].strip()

        prompt = (f"""\
Mô tả gốc của trang PPT này là:
{original_description}

Bây giờ, hãy chỉnh sửa trang PPT này theo chỉ dẫn sau: {edit_instruction}

Yêu cầu giữ nguyên nội dung văn bản và phong cách thiết kế ban đầu, chỉ chỉnh sửa theo đúng chỉ dẫn. Trong các ảnh tham khảo được cung cấp có thể bao gồm tư liệu mới hoặc vùng người dùng khoanh chọn, hãy phán đoán thông minh ý định người dùng dựa trên mối quan hệ giữa ảnh gốc và ảnh tham khảo.
""")
    else:
        prompt = f"Trang PPT: {edit_instruction}\nVui lòng tạo hoặc chỉnh sửa trang theo chỉ dẫn, duy trì tính thẩm mỹ và độ rõ nét cao."

    logger.debug(f"[get_image_edit_prompt] Final prompt:\n{prompt}")
    return prompt


def get_clean_background_prompt(removal_regions: Optional[List[Dict[str, Any]]] = None) -> str:
    """Tạo prompt xóa chữ và chi tiết để lấy nền sạch."""
    regions_info = ""
    if removal_regions:
        regions_json = json.dumps(removal_regions, ensure_ascii=False, indent=2)
        regions_info = f"""
Dưới đây là danh sách hộp giới hạn (bbox) của các phần tử tiền cảnh cần ưu tiên loại bỏ, tọa độ đã được chuẩn hóa về khoảng 0-1 theo chiều rộng và chiều cao:

```json
{regions_json}
```

Giải thích tọa độ:
- `bbox.x0`, `bbox.y0`: Tọa độ góc trên bên trái, khoảng 0-1
- `bbox.x1`, `bbox.y1`: Tọa độ góc dưới bên phải, khoảng 0-1
- `bbox.width`, `bbox.height`: Tỷ lệ chiều rộng, chiều cao so với toàn ảnh
- `element_type`: Loại phần tử ước tính, ví dụ `text` / `image` / `chart` / `table` / `figure`

Vui lòng ưu tiên loại bỏ toàn bộ nội dung tiền cảnh bên trong các bbox này cũng như phần tiếp giáp, tránh bỏ sót.
"""

    prompt = f"""\
Bạn là chuyên gia xóa chữ và hình ảnh trên ảnh chuyên nghiệp. Nhiệm vụ của bạn là xóa bỏ hoàn toàn văn bản và hình minh họa khỏi ảnh gốc, tạo ra một hình nền hoàn toàn sạch sẽ, không có bất kỳ chữ hay biểu đồ nào.
<requirements>
- Xóa triệt để toàn bộ văn bản, hình vẽ minh họa, biểu đồ trên trang. Đảm bảo toàn bộ chữ bị loại bỏ hoàn toàn.
- Duy trì tính toàn vẹn của thiết kế nền gốc (bao gồm dải màu chuyển sắc gradient, hoa văn, kết cấu bề mặt, đường nét, mảng màu...). Giữ lại các khung hộp văn bản và mảng màu trang trí của ảnh gốc.
- Đối với các vùng nền bị che khuất bởi các phần tử phía trước, hãy bù đắp một cách thông minh và liền mạch như thể chưa từng có chi tiết nào ở đó.
- Kích thước, tỷ lệ, phong cách và cách phối màu của ảnh xuất ra phải hoàn toàn đồng nhất với ảnh gốc.
- Tuyệt đối không thêm bất kỳ chi tiết mới nào.
</requirements>

{regions_info}

Lưu ý: Mọi văn bản và biểu đồ ở bất kỳ vị trí nào đều phải được loại bỏ triệt để, kết quả trả về không được chứa bất kỳ chữ hay biểu đồ nào.
"""
    logger.debug(f"[get_clean_background_prompt] Final prompt:\n{prompt}")
    return prompt


def get_quality_enhancement_prompt(inpainted_regions: list = None) -> str:
    """Tạo prompt nâng cao chất lượng ảnh sau khi tẩy xóa."""
    regions_info = ""
    if inpainted_regions and len(inpainted_regions) > 0:
        regions_json = json.dumps(inpainted_regions, ensure_ascii=False, indent=2)
        regions_info = f"""
Dưới đây là các vùng cụ thể đã qua xử lý tẩy xóa ({len(inpainted_regions)} vùng hình chữ nhật), hãy tập trung phục hồi các vị trí này:

```json
{regions_json}
```

Giải thích tọa độ (tính theo phần trăm 0-100% so với kích thước ảnh):
- left, top: Khoảng cách từ cạnh trái và cạnh trên
- right, bottom: Khoảng cách từ cạnh phải và cạnh dưới
- width_percent, height_percent: Tỷ lệ phần trăm chiều rộng và chiều cao
"""

    prompt = f"""\
Bạn là một chuyên gia phục hồi hình ảnh chuyên nghiệp. Hình ảnh trang PPT này vừa trải qua quá trình xóa văn bản và đối tượng, công cụ xóa có thể để lại một số tì vết như:
- Màu sắc không đều, chuyển tiếp màu chưa mượt mà
- Vệt mờ nhòe hoặc loang lổ
- Vùng màu chưa hài hòa với nền xung quanh
- Vân bề mặt hoặc hoa văn bị đứt đoạn
{regions_info}
Nhiệm vụ của bạn là xử lý và làm mịn các tì vết này, giúp bức ảnh trông tự nhiên như một hình nền gốc hoàn chỉnh.

Yêu cầu:
- Tập trung phục hồi các vùng được đánh dấu để hòa hợp hoàn hảo với nền xung quanh
- Đảm bảo tính liên tục của vân bề mặt, màu sắc và hoa văn
- Nâng cao độ sắc nét tổng thể, khử nhiễu, mờ nhòe và hiện tượng giả lập
- Giữ nguyên bố cục, tông màu và phong cách ban đầu của bức ảnh
- Tuyệt đối không thêm chữ, biểu đồ, hình vẽ, khung viền hay bất kỳ chi tiết mới nào
- Kích thước ảnh xuất ra phải khớp chính xác với ảnh gốc

Hãy xuất ra hình nền PPT độ nét cao đã được phục hồi hoàn chỉnh.
"""
    return prompt


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Trích xuất nội dung Prompts
# ═══════════════════════════════════════════════════════════════════════════════

def get_text_attribute_extraction_prompt(content_hint: str = "") -> str:
    """Tạo prompt trích xuất thuộc tính văn bản, màu sắc, công thức LaTeX."""
    prompt = """Nhiệm vụ của bạn là nhận diện chính xác nội dung văn bản và kiểu dáng trong ảnh này, trả về kết quả dưới dạng JSON.

{content_hint}

## Nhiệm vụ cốt lõi
Quan sát kỹ hình ảnh và nhận diện chính xác:
1. **Nội dung văn bản** - Ghi lại chính xác các ký tự bạn nhìn thấy.
2. **Màu sắc** - Mã màu hex thực tế (#RRGGBB) của từng từ/chữ.
3. **Khoảng trắng** - Giữ nguyên vị trí và số lượng khoảng trắng, không tự ý gộp lại.
4. **Công thức** - Nếu là công thức toán học, xuất dưới định dạng LaTeX với is_latex=true.

## Định dạng JSON trả về:
```json
{{
    "colored_segments": [
        {{"text": "Ví dụ tiêu đề", "color": "#000000"}},
        {{"text": "1.827 môi trường tác vụ", "color": "#26397A"}},
        {{"text": " và ", "color": "#000000"}},
        {{"text": "x^2 + y^2 = z^2", "color": "#FF0000", "is_latex": true}}
    ]
}}
```
""".format(content_hint=content_hint)
    return prompt


def get_batch_text_attribute_extraction_prompt(text_elements_json: str) -> str:
    """Tạo prompt trích xuất thuộc tính văn bản hàng loạt."""
    prompt = f"""Bạn là một chuyên gia phân tích bố cục PPT/tài liệu chuyên nghiệp. Hãy phân tích các thuộc tính kiểu dáng của tất cả các vùng chữ được đánh dấu trong ảnh.

Danh sách các phần tử văn bản và vị trí tương ứng:

```json
{text_elements_json}
```

Hãy trả về kết quả phân tích thuộc tính dưới định dạng JSON với cấu trúc rõ ràng cho từng phần tử.
"""
    return prompt


def get_ppt_page_content_extraction_prompt(page_index: int, total_pages: int, ocr_text: str = "") -> str:
    """Tạo prompt trích xuất nội dung trang PPT từ ảnh."""
    prompt = f"""Phân tích ảnh trang PPT (trang {page_index}/{total_pages}). Trích xuất nội dung văn bản đầy đủ và mô tả bố cục theo cấu trúc chuẩn.
Dữ liệu OCR tham khảo:
{ocr_text}

Trả về định dạng có cấu trúc bao gồm tiêu đề, văn bản chính và các lưu ý bố cục.
"""
    return prompt


def get_layout_caption_prompt(image_description: str = "") -> str:
    """Tạo prompt mô tả bố cục hình ảnh."""
    prompt = f"""Mô tả ngắn gọn, chính xác bố cục không gian và cấu trúc trực quan của hình ảnh này:
{image_description}
"""
    return prompt


def get_style_extraction_prompt() -> str:
    """Tạo prompt trích xuất phong cách từ ảnh mẫu."""
    prompt = """Bạn là một chuyên gia phân tích phong cách thiết kế bài thuyết trình. Hãy phân tích hình ảnh mẫu được cung cấp và trích xuất một bản mô tả phong cách thiết kế hoàn chỉnh.

Hãy mô tả chi tiết:
1. Tông màu chủ đạo và màu sắc điểm nhấn (mã màu hex cụ thể)
2. Phong cách hình nền và kết cấu bề mặt (nền phẳng, chuyển sắc, tối giản, công nghệ...)
3. Kiểu dáng phông chữ, phân cấp tiêu đề và độ dày nét chữ
4. Ngôn ngữ thiết kế (tối giản, thương mại, thanh lịch, tạp chí, công nghệ...)
5. Cách sắp xếp bố cục và khoảng cách lề

Hãy viết thành một đoạn văn mô tả súc tích, mạch lạc để AI tạo ảnh có thể bám sát và tái lập chính xác phong cách này.
"""
    return prompt


def get_style_from_content_prompt(content_text: str) -> str:
    """Tạo phong cách thiết kế gợi ý từ nội dung văn bản."""
    prompt = f"""Dựa vào nội dung bài thuyết trình dưới đây, hãy đề xuất phong cách thiết kế slide phù hợp nhất:
{content_text}

Nêu rõ bảng màu, phong cách hình ảnh và ngôn ngữ bố cục được khuyến nghị.
"""
    return prompt


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Thuyết minh Prompts
# ═══════════════════════════════════════════════════════════════════════════════

def get_narration_generation_prompt(page_data: dict, config: dict, language: str = None) -> str:
    """Tạo prompt sinh kịch bản lời nói thuyết minh cho trang slide."""
    title = page_data.get('title', '')
    desc_text = page_data.get('description_text', '')
    points = page_data.get('points', [])
    points_str = "\n".join([f"- {p}" for p in points]) if points else "(Không có ý chính)"

    prompt = f"""Bạn là một người viết kịch bản thuyết trình chuyên nghiệp.
Hãy viết lời thuyết minh (narration script) cho trang slide sau:

Tiêu đề: {title}
Ý chính:
{points_str}

Nội dung chi tiết:
{desc_text}

Yêu cầu kịch bản:
- Phong cách người nói: {config.get('speaker_persona', 'chuyên gia truyền cảm hứng')}
- Giọng điệu: {config.get('speech_tone', 'tự nhiên, cuốn hút và chuyên nghiệp')}
- Đối tượng người nghe: {config.get('target_audience', 'đại chúng')}
- Chủ đề bài nói: {config.get('presentation_topic', title)}
- Độ dài mục tiêu: từ {config.get('min_words', 100)} đến {config.get('max_words', 200)} từ.

Trả về kết quả dưới định dạng JSON:
```json
{{
    "narration": "Lời thuyết minh chi tiết...",
    "speaker_persona": "{config.get('speaker_persona')}",
    "speech_tone": "{config.get('speech_tone')}",
    "presentation_topic": "{config.get('presentation_topic')}",
    "key_points_covered": ["điểm 1", "điểm 2"]
}}
```
{get_language_instruction(language)}
"""
    return prompt


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Phân tích mẫu & Khớp mẫu Prompts
# ═══════════════════════════════════════════════════════════════════════════════

def get_template_analysis_prompt(extracted_text: str = "") -> str:
    """Tạo prompt phân tích mẫu slide chi tiết."""
    prompt = f"""Bạn là chuyên gia phân tích thiết kế mẫu slide thuyết trình. Hãy phân tích hình ảnh mẫu được cung cấp.
Văn bản trích xuất được từ ảnh:
{extracted_text}

Trả về kết quả dưới dạng JSON bao gồm:
- template_role: vai trò của mẫu (cover, toc, content, divider, conclusion...)
- visual_style: mô tả phong cách thị giác
- layout_structure: cấu trúc bố cục
- color_palette: bảng màu chính
- recommendations: gợi ý cách sử dụng cho các trang nội dung
"""
    return prompt


def get_template_auto_match_prompt(pages_summary: str, templates_summary: str) -> str:
    """Tạo prompt tự động ghép nối mẫu phù hợp cho từng trang slide."""
    prompt = f"""Bạn là chuyên gia thiết kế bài thuyết trình. Hãy ghép nối mẫu slide phù hợp nhất từ kho mẫu cho từng trang trong danh sách sau:

Danh sách các trang slide cần gán mẫu:
{pages_summary}

Kho mẫu slide khả dụng:
{templates_summary}

Quy tắc ghép nối:
1. Trang bìa phải ghép với mẫu vai trò cover nếu có.
2. Trang mục lục hoặc chuyển phần ghép với mẫu toc hoặc divider tương ứng.
3. Các trang nội dung ghép với mẫu có bố cục và số lượng khối tương thích nhất.
4. Trả về kết quả JSON với danh sách cặp page_id và template_asset_id kèm độ tin cậy confidence (0.0 đến 1.0).
"""
    return prompt
