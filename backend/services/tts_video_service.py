"""
TTS Video Service —  PPT 

:
  1. edge-tts 
  2. Ken Burns  (zoompan, ) 
  3. FFmpeg 
  4. ASS 
"""
import asyncio
import logging
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import unicodedata
from typing import List, Optional, Callable, Tuple

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Backend logic
# ═══════════════════════════════════════════════════════════════════════════════

# Backend logic
_MAX_SUBTITLE_SEGMENT_LENGTH = 30

# Backend logic
_DEFAULT_SILENT_DURATION = 3.0

# Backend logic
_LEADING_PAD_SECONDS = 0.8
_TRAILING_PAD_SECONDS = 1.2

# Backend logic
_FFMPEG_IDLE_TIMEOUT_SECONDS = 600.0

# Backend logic
_FFMPEG_PROGRESS_INTERVAL_SECONDS = 1.0


def _inject_ffmpeg_progress_args(cmd: List[str]) -> List[str]:
    """ Backend docstring """
    if '-progress' in cmd:
        return cmd
    return [
        cmd[0],
        '-nostats',
        '-progress', 'pipe:2',
        '-stats_period', str(_FFMPEG_PROGRESS_INTERVAL_SECONDS),
        *cmd[1:],
    ]


def _read_process_lines(stream, output_queue: "queue.Queue[str]", collected_lines: List[str]) -> None:
    """ Backend docstring """
    try:
        for raw_line in iter(stream.readline, b''):
            line = raw_line.decode('utf-8', errors='replace').strip()
            if not line:
                continue
            collected_lines.append(line)
            if len(collected_lines) > 200:
                del collected_lines[:len(collected_lines) - 200]
            output_queue.put(line)
    finally:
        stream.close()


def _wait_for_process_with_idle_watchdog(
    proc: subprocess.Popen,
    error_prefix: str,
    idle_timeout: float = _FFMPEG_IDLE_TIMEOUT_SECONDS,
) -> None:
    """
     FFmpeg . 

    ,  stderr/progress ; 
     idle_timeout , . 
    """
    stderr_queue: "queue.Queue[str]" = queue.Queue()
    stderr_lines: List[str] = []
    reader = threading.Thread(
        target=_read_process_lines,
        args=(proc.stderr, stderr_queue, stderr_lines),
        daemon=True,
    )
    reader.start()

    last_output_at = time.monotonic()
    poll_interval = min(1.0, max(0.01, idle_timeout / 4))

    while True:
        try:
            stderr_queue.get(timeout=poll_interval)
            last_output_at = time.monotonic()
        except queue.Empty:
            pass

        if proc.poll() is not None:
            break

        if time.monotonic() - last_output_at > idle_timeout:
            proc.kill()
            proc.wait()
            reader.join(timeout=1)
            tail = '\n'.join(stderr_lines[-20:])
            raise RuntimeError(
                f"{error_prefix}: FFmpeg stalled after {int(idle_timeout)}s without progress. "
                f"Last output: {tail[-500:]}"
            )

    reader.join(timeout=1)

    if proc.returncode != 0:
        tail = '\n'.join(stderr_lines[-20:])
        raise RuntimeError(f"{error_prefix}: {tail[-500:]}")


def _run_ffmpeg_command(
    cmd: List[str],
    error_prefix: str,
    idle_timeout: float = _FFMPEG_IDLE_TIMEOUT_SECONDS,
) -> None:
    """ Backend docstring """
    proc = subprocess.Popen(
        _inject_ffmpeg_progress_args(cmd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _wait_for_process_with_idle_watchdog(proc, error_prefix, idle_timeout=idle_timeout)


def create_placeholder_frame(
    output_path: str,
    title: str = '',
    width: int = 1920,
    height: int = 1080,
    ffmpeg_path: str = 'ffmpeg',
) -> None:
    """
     ( + ) . 

     FFmpeg , . 
    """
    # Backend logic
    safe_title = title.replace("'", "'").replace(":", "\\:").replace("\\", "\\\\")
    safe_title = safe_title[:60]  # Backend logic

    font_size = max(36, int(height / 20))

    # Backend logic
    font_file = _detect_cjk_font_file()
    if font_file:
        drawtext = (
            f"drawtext=text='{safe_title}':"
            f"fontfile='{font_file}':"
            f"fontsize={font_size}:fontcolor=white:"
            f"x=(w-text_w)/2:y=(h-text_h)/2"
        )
    else:
        drawtext = (
            f"drawtext=text='{safe_title}':"
            f"fontsize={font_size}:fontcolor=white:"
            f"x=(w-text_w)/2:y=(h-text_h)/2"
        )

    # Backend logic
    vf = (
        f"color=c=#1a1a2e:s={width}x{height}:d=1,"
        f"format=rgb24,{drawtext}"
    )

    cmd = [
        ffmpeg_path, '-y',
        '-f', 'lavfi',
        '-i', vf,
        '-frames:v', '1',
        '-update', '1',
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        # Backend logic
        logger.warning(f"Placeholder with text failed, using plain background: {result.stderr[-200:]}")
        vf_plain = f"color=c=#1a1a2e:s={width}x{height}:d=1"
        cmd_plain = [
            ffmpeg_path, '-y',
            '-f', 'lavfi',
            '-i', vf_plain,
            '-frames:v', '1',
            '-update', '1',
            output_path,
        ]
        result2 = subprocess.run(cmd_plain, capture_output=True, text=True, timeout=15)
        if result2.returncode != 0:
            raise RuntimeError(f"FFmpeg placeholder frame failed: {result2.stderr[-300:]}")


def _detect_cjk_font_file() -> Optional[str]:
    """ Backend docstring """
    # Backend logic
    candidates = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    # Backend logic
    try:
        result = subprocess.run(
            ['fc-match', '-f', '%{file}', ':lang=zh'],
            capture_output=True, text=True, timeout=5,
        )
        path = result.stdout.strip()
        if path and os.path.exists(path):
            return path
    except Exception:
        pass

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Backend logic
# ═══════════════════════════════════════════════════════════════════════════════


def check_ffmpeg_available(ffmpeg_path: str = 'ffmpeg') -> bool:
    """ Backend docstring """
    try:
        subprocess.run(
            [ffmpeg_path, '-version'],
            capture_output=True, check=True, timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False


def check_ffmpeg_ass_filter_available(ffmpeg_path: str = 'ffmpeg') -> bool:
    """ Backend docstring """
    try:
        result = subprocess.run(
            [ffmpeg_path, '-hide_banner', '-filters'],
            capture_output=True, text=True, check=True, timeout=5,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False

    filter_listing = f"{result.stdout}\n{result.stderr}"
    return re.search(r'^\s*[TSC\.|]+\s+ass\s+', filter_listing, re.MULTILINE) is not None


def _derive_ffprobe_path(ffmpeg_path: str) -> str:
    """Return the sibling ffprobe executable without rewriting parent folders."""
    return re.sub(
        r'(?i)(^|[/\\])ffmpeg(?P<extension>\.exe)?$',
        lambda match: f"{match.group(1)}ffprobe{match.group('extension') or ''}",
        ffmpeg_path,
    )


def get_audio_duration(audio_path: str, ffmpeg_path: str = 'ffmpeg') -> float:
    """ Backend docstring """
    ffprobe_path = _derive_ffprobe_path(ffmpeg_path)
    cmd = [
        ffprobe_path, '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
    return float(result.stdout.strip())


def pad_audio_with_silence(
    src_path: str,
    dst_path: str,
    leading_seconds: float = 0.0,
    trailing_seconds: float = 0.0,
    ffmpeg_path: str = 'ffmpeg',
) -> float:
    """ Backend docstring """
    if leading_seconds <= 0 and trailing_seconds <= 0:
        shutil.copy2(src_path, dst_path)
        return get_audio_duration(dst_path, ffmpeg_path)

    filters: List[str] = []
    if leading_seconds > 0:
        filters.append(f'adelay={int(leading_seconds * 1000)}|{int(leading_seconds * 1000)}:all=1')
    if trailing_seconds > 0:
        filters.append(f'apad=pad_dur={trailing_seconds}')

    cmd = [
        ffmpeg_path, '-y',
        '-i', src_path,
        '-af', ','.join(filters),
        '-c:a', 'libmp3lame', '-b:a', '128k',
        dst_path,
    ]
    _run_ffmpeg_command(cmd, "FFmpeg failed to pad audio")
    return get_audio_duration(dst_path, ffmpeg_path)


def get_default_voice(language: str, config: Optional[dict] = None) -> str:
    """ Backend docstring """
    defaults = {
        'zh': 'zh-CN-XiaoxiaoNeural',
        'en': 'en-US-JennyNeural',
        'ja': 'ja-JP-NanamiNeural',
    }
    if config:
        voice_map = {
            'zh': config.get('TTS_DEFAULT_VOICE_ZH', defaults['zh']),
            'en': config.get('TTS_DEFAULT_VOICE_EN', defaults['en']),
            'ja': config.get('TTS_DEFAULT_VOICE_JA', defaults['ja']),
        }
        return voice_map.get(language, voice_map['zh'])
    return defaults.get(language, defaults['zh'])


# ═══════════════════════════════════════════════════════════════════════════════
# Backend logic
# ═══════════════════════════════════════════════════════════════════════════════


async def _generate_tts_async(text: str, output_path: str, voice: str, rate: str) -> None:
    """ Backend docstring """
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


def generate_tts_audio_sync(
    text: str,
    output_path: str,
    voice: str = 'zh-CN-XiaoxiaoNeural',
    rate: str = '+0%',
    ffmpeg_path: str = 'ffmpeg',
) -> float:
    """
    :  TTS  (edge-tts) . 

    Args:
        text: 
        output_path:  (MP3) 
        voice: edge-tts 
        rate: 
        ffmpeg_path: ffmpeg  ( ffprobe ) 

    Returns:
        float:  () 
    """
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_generate_tts_async(text, output_path, voice, rate))
    finally:
        loop.close()

    duration = get_audio_duration(output_path, ffmpeg_path)
    logger.debug(f"TTS audio generated: {output_path} ({duration:.1f}s)")
    return duration


def generate_elevenlabs_audio_sync(
    text: str,
    output_path: str,
    api_key: str,
    voice_id: str,
    ffmpeg_path: str = 'ffmpeg',
    speed: float = 1.0,
) -> Tuple[float, Optional[dict]]:
    """
     ElevenLabs TTS  (MP3) , . 

    Returns:
        (duration_seconds, alignment) — alignment 
        {'characters': [...], 'character_start_times_ms': [...], 'character_durations_ms': [...]}
         None. 
    """
    import base64
    from elevenlabs.client import ElevenLabs
    from elevenlabs.core import ApiError as ElevenLabsApiError
    from elevenlabs import VoiceSettings

    client = ElevenLabs(api_key=api_key)
    # Backend logic
    clamped_speed = max(0.7, min(float(speed), 1.2))
    voice_settings = VoiceSettings(
        stability=0.75,
        similarity_boost=0.75,
        style=0.0,
        use_speaker_boost=True,
        speed=clamped_speed,
    )

    def _convert_with_timestamps(model_id: str):
        return client.text_to_speech.convert_with_timestamps(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format='mp3_44100_128',
            voice_settings=voice_settings,
        )

    alignment_dict: Optional[dict] = None
    try:
        try:
            response = _convert_with_timestamps('eleven_v3')
        except ElevenLabsApiError as e:
            logger.warning(
                f"eleven_v3 không khả dụng (status={getattr(e, 'status_code', None)}), chuyển dự phòng sang eleven_multilingual_v2"
            )
            response = _convert_with_timestamps('eleven_multilingual_v2')

        # Backend logic
        audio_b64 = (
            getattr(response, 'audio_base_64', None)
            or getattr(response, 'audio_base64', None)
        )
        if audio_b64 is None and isinstance(response, dict):
            audio_b64 = response.get('audio_base_64') or response.get('audio_base64')
        if not audio_b64:
            raise RuntimeError("ElevenLabs chưa trả về audio_base64 dữ liệu")

        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(audio_b64))

        alignment_obj = getattr(response, 'alignment', None)
        if alignment_obj is None and isinstance(response, dict):
            alignment_obj = response.get('alignment')
        if alignment_obj is not None:
            chars = getattr(alignment_obj, 'characters', None)
            # Backend logic
            starts_sec = getattr(alignment_obj, 'character_start_times_seconds', None)
            ends_sec = getattr(alignment_obj, 'character_end_times_seconds', None)
            if chars is None and isinstance(alignment_obj, dict):
                chars = alignment_obj.get('characters')
                starts_sec = alignment_obj.get('character_start_times_seconds')
                ends_sec = alignment_obj.get('character_end_times_seconds')
            if chars and starts_sec and ends_sec and len(chars) == len(starts_sec) == len(ends_sec):
                alignment_dict = {
                    'characters': list(chars),
                    'character_start_times_ms': [int(s * 1000) for s in starts_sec],
                    'character_durations_ms': [
                        max(int((e - s) * 1000), 0) for s, e in zip(starts_sec, ends_sec)
                    ],
                }
    except ElevenLabsApiError as e:
        status = getattr(e, 'status_code', None)
        body = getattr(e, 'body', None)
        detail = body.get('detail', {}) if isinstance(body, dict) else {}
        err_status = detail.get('status', '') if isinstance(detail, dict) else ''
        msg = (detail.get('message') if isinstance(detail, dict) else None) or str(e)
        if err_status == 'quota_exceeded' or 'quota' in msg.lower() or 'credits' in msg.lower():
            raise RuntimeError(f"ElevenLabs hạn mức miễn phí không đủ: {msg}") from e
        elif err_status == 'invalid_api_key' or status == 401:
            raise RuntimeError(f"ElevenLabs xác thực thất bại, Vui lòng kiểm tra API Key có hợp lệ không") from e
        elif status == 402 or (isinstance(detail, dict) and detail.get('code') == 'paid_plan_required'):
            raise RuntimeError(f"ElevenLabs Giọng đọc này yêu cầu gói trả phí: {msg}") from e
        else:
            raise RuntimeError(f"ElevenLabs API Lỗi (HTTP {status}): {msg}") from e

    duration = get_audio_duration(output_path, ffmpeg_path)
    logger.debug(
        f"ElevenLabs audio generated: {output_path} ({duration:.1f}s, alignment={'yes' if alignment_dict else 'no'})"
    )
    return duration, alignment_dict


def _slice_audio_by_time(
    src_path: str,
    dst_path: str,
    start_seconds: float,
    end_seconds: float,
    ffmpeg_path: str = 'ffmpeg',
) -> None:
    """ Backend docstring """
    if end_seconds <= start_seconds:
        raise ValueError(f"Khoảng cắt không hợp lệ [{start_seconds:.3f}, {end_seconds:.3f}]")
    cmd = [
        ffmpeg_path, '-y',
        '-ss', f'{start_seconds:.3f}',
        '-to', f'{end_seconds:.3f}',
        '-i', src_path,
        '-c:a', 'libmp3lame', '-b:a', '128k',
        dst_path,
    ]
    _run_ffmpeg_command(
        cmd, f"FFmpeg failed to slice audio [{start_seconds:.2f}-{end_seconds:.2f}]"
    )


def _find_page_boundaries_sec(
    page_texts: List[str],
    full_duration_sec: float,
    full_alignment: dict,
    snap_window_sec: float = 2.0,
) -> List[float]:
    """
     N+1  [t_0, ..., t_N], t_0=0, t_N=full_duration. 
    nội bộ N-1 đường viền dùng "ước lượng theo tỷ lệ ký tự + dài nhất gần nhất pause bám dính" định vị bằng thuật toán: 

      1. ; 
      2.  ±snap_window_sec  alignment  (gap) ; 
      3. ;  gap . 

    : TTS  delimiter (\\n\\n)  pause. 
     ElevenLabs ,  alignment  1:1 . 
    """
    n_pages = len(page_texts)
    if n_pages <= 1:
        return [0.0, full_duration_sec]

    chars_per_page = [len(t) for t in page_texts]
    total_chars = sum(chars_per_page) or 1

    # Backend logic
    target_times_sec: List[float] = []
    cum = 0
    for c in chars_per_page[:-1]:
        cum += c
        target_times_sec.append(full_duration_sec * cum / total_chars)

    starts_ms = full_alignment.get('character_start_times_ms') or []
    durs_ms = full_alignment.get('character_durations_ms') or []

    # Backend logic
    gaps: List[Tuple[float, float]] = []
    if len(starts_ms) >= 2 and len(durs_ms) >= 2:
        for i in range(len(starts_ms) - 1):
            gap_start_ms = starts_ms[i] + durs_ms[i]
            gap_end_ms = starts_ms[i + 1]
            gap_size = max(gap_end_ms - gap_start_ms, 0)
            gap_mid = (gap_start_ms + gap_end_ms) / 2.0
            gaps.append((gap_size, gap_mid))

    snap_window_ms = snap_window_sec * 1000
    boundaries_sec: List[float] = [0.0]
    used_gap_indices: set = set()
    last_t_ms = 0.0

    for target_t in target_times_sec:
        target_ms = target_t * 1000
        best_gap = -1.0
        best_idx = -1
        best_mid_ms = target_ms
        for idx, (gap_size, gap_mid) in enumerate(gaps):
            if idx in used_gap_indices:
                continue
            if gap_mid <= last_t_ms:
                continue
            if abs(gap_mid - target_ms) > snap_window_ms:
                continue
            if gap_size > best_gap:
                best_gap = gap_size
                best_idx = idx
                best_mid_ms = gap_mid
        if best_idx >= 0:
            used_gap_indices.add(best_idx)
            chosen_ms = best_mid_ms
        else:
            chosen_ms = target_ms
        # Backend logic
        if chosen_ms <= last_t_ms:
            chosen_ms = last_t_ms + 100
        boundaries_sec.append(chosen_ms / 1000.0)
        last_t_ms = chosen_ms

    final_t = max(full_duration_sec, last_t_ms / 1000.0 + 0.1)
    boundaries_sec.append(final_t)
    return boundaries_sec


def _slice_alignment_by_time(
    full_alignment: dict, t_start_ms: int, t_end_ms: int,
) -> dict:
    """ Backend docstring """
    chars = full_alignment.get('characters') or []
    starts = full_alignment.get('character_start_times_ms') or []
    durs = full_alignment.get('character_durations_ms') or []
    sub_chars: List[str] = []
    sub_starts: List[int] = []
    sub_durs: List[int] = []
    for c, s, d in zip(chars, starts, durs):
        if t_start_ms <= s < t_end_ms:
            sub_chars.append(c)
            sub_starts.append(max(s - t_start_ms, 0))
            sub_durs.append(d)
    return {
        'characters': sub_chars,
        'character_start_times_ms': sub_starts,
        'character_durations_ms': sub_durs,
    }


# Backend logic
# Backend logic
# Backend logic
_ELEVENLABS_BATCH_CHAR_LIMIT = 4500


def _pack_pages_into_batches(
    narration_indexes: List[int],
    page_texts: List[str],
    char_limit: int,
    delimiter: str,
) -> List[List[Tuple[int, str]]]:
    """
     narration  N ,  ≤ char_limit. 

     char_limit,  ( ElevenLabs ) . 
    """
    batches: List[List[Tuple[int, str]]] = []
    cur: List[Tuple[int, str]] = []
    cur_chars = 0
    delim_len = len(delimiter)
    for idx, text in zip(narration_indexes, page_texts):
        added = len(text) + (delim_len if cur else 0)
        if cur and cur_chars + added > char_limit:
            batches.append(cur)
            cur = []
            cur_chars = 0
            added = len(text)
        cur.append((idx, text))
        cur_chars += added
    if cur:
        batches.append(cur)
    return batches


def _synthesize_batch_and_split(
    batch_indexes: List[int],
    batch_texts: List[str],
    tmp_dir: str,
    batch_slug: str,
    batch_label: str,
    api_key: str,
    voice_id: str,
    ffmpeg_path: str,
    speed: float,
) -> List[Tuple[str, dict, float]]:
    """
    :  →  ElevenLabs  →  alignment . 

     batch_indexes  (audio_path, sub_alignment, duration) . 
    alignment  raise,  fail-fast . 

    :  j  [t_j, t_{j+1}), . delimiter 
    , . 
    """
    if not batch_texts:
        return []

    # Backend logic
    if len(batch_texts) == 1:
        page_idx = batch_indexes[0]
        audio_path = os.path.join(tmp_dir, f'audio_{page_idx:03d}.mp3')
        duration, alignment = generate_elevenlabs_audio_sync(
            batch_texts[0], audio_path,
            api_key=api_key, voice_id=voice_id,
            ffmpeg_path=ffmpeg_path, speed=speed,
        )
        if not alignment:
            raise RuntimeError(
                f"ElevenLabs không trả về cấp độ ký tự alignment (batch {batch_label}) , không thể xác định thời gian phụ đề, đã dừng xuất"
            )
        return [(audio_path, alignment, duration)]

    delimiter = '\n\n'
    full_text = delimiter.join(batch_texts)
    full_audio_path = os.path.join(tmp_dir, f'audio_full_{batch_slug}.mp3')

    duration_full, full_alignment = generate_elevenlabs_audio_sync(
        full_text, full_audio_path,
        api_key=api_key, voice_id=voice_id,
        ffmpeg_path=ffmpeg_path, speed=speed,
    )

    if not full_alignment:
        raise RuntimeError(
            f"ElevenLabs không trả về cấp độ ký tự alignment (batch {batch_label}) , không thể cắt toàn đoạn, đã dừng xuất"
        )

    chars = full_alignment.get('characters') or []
    starts_ms = full_alignment.get('character_start_times_ms') or []
    durs_ms = full_alignment.get('character_durations_ms') or []
    if not chars or len(chars) != len(starts_ms) or len(chars) != len(durs_ms):
        raise RuntimeError(
            f"ElevenLabs alignment dữ liệu không đầy đủ (batch {batch_label}) , đã dừng xuất"
        )

    boundaries_sec = _find_page_boundaries_sec(
        batch_texts, full_duration_sec=duration_full, full_alignment=full_alignment,
    )

    results: List[Tuple[str, dict, float]] = []
    for j in range(len(batch_texts)):
        t_start = boundaries_sec[j]
        t_end = boundaries_sec[j + 1]
        page_idx = batch_indexes[j]

        page_audio_path = os.path.join(tmp_dir, f'audio_{page_idx:03d}.mp3')
        _slice_audio_by_time(
            full_audio_path, page_audio_path, t_start, t_end, ffmpeg_path=ffmpeg_path,
        )
        page_duration = get_audio_duration(page_audio_path, ffmpeg_path=ffmpeg_path)

        sub_alignment = _slice_alignment_by_time(
            full_alignment, int(t_start * 1000), int(t_end * 1000),
        )
        results.append((page_audio_path, sub_alignment, page_duration))

    logger.info(
        f"batch {batch_label} Hoàn tất tổng hợp toàn đoạn: {len(batch_texts)} trang → 1 lần ElevenLabs gọi, "
        f"toàn bài {duration_full:.1f}s, bám dính viền {len(boundaries_sec) - 2} nơi "
    )
    return results


def _generate_elevenlabs_whole_and_split(
    pages_data: List[dict],
    narration_indexes: List[int],
    tmp_dir: str,
    api_key: str,
    voice_id: str,
    ffmpeg_path: str,
    speed: float,
    progress_callback: Optional[Callable[[str, str, int], None]] = None,
) -> List[Tuple[str, dict, float]]:
    """
     narration ,  + . 

     narration_indexes ,  (audio_path, sub_alignment, duration). 
     alignment  /  / API  raise (fail-fast, ) . 
    """
    delimiter = '\n\n'
    page_texts = [
        _strip_invisible_unicode(
            (pages_data[i].get('narration_text') or '').strip(), keep_newlines=True,
        )
        for i in narration_indexes
    ]
    if not all(page_texts):
        raise RuntimeError("Tổng hợp toàn đoạn: có giá trị rỗng narration, không thể tạo văn bản hoàn chỉnh")

    batches = _pack_pages_into_batches(
        narration_indexes, page_texts,
        char_limit=_ELEVENLABS_BATCH_CHAR_LIMIT, delimiter=delimiter,
    )

    results_by_index: dict = {}
    for b_idx, batch in enumerate(batches):
        batch_indexes = [pair[0] for pair in batch]
        batch_texts = [pair[1] for pair in batch]
        slug = f"{b_idx + 1:03d}of{len(batches):03d}"
        label = f"{b_idx + 1}/{len(batches)}"
        if progress_callback:
            total_chars = sum(len(t) for t in batch_texts)
            progress_callback(
                "TTS",
                f"Tổng hợp toàn đoạn trang {label} lô ({len(batch)} trang / {total_chars} chữ ) ",
                22,
            )
        batch_results = _synthesize_batch_and_split(
            batch_indexes, batch_texts, tmp_dir,
            batch_slug=slug, batch_label=label,
            api_key=api_key, voice_id=voice_id,
            ffmpeg_path=ffmpeg_path, speed=speed,
        )
        for idx, r in zip(batch_indexes, batch_results):
            results_by_index[idx] = r

    return [results_by_index[i] for i in narration_indexes]


# ═══════════════════════════════════════════════════════════════════════════════
# Backend logic
# ═══════════════════════════════════════════════════════════════════════════════

# Backend logic
KEN_BURNS_EFFECTS = ['zoom_in', 'zoom_out', 'pan_left', 'pan_right']

# Backend logic
KEN_BURNS_MAX_ZOOM = 1.08
KEN_BURNS_PAN_CANVAS_SCALE = 1.08


def _prepare_canvas(src, content_w: int, content_h: int, canvas_w: int, canvas_h: int):
    """ contain  content ,  canvas , . 

    content_w/h:  (zoom=1.0 ) 
    canvas_w/h:  () 
    """
    import cv2

    sh, sw = src.shape[:2]

    bg = cv2.resize(src, (canvas_w, canvas_h), interpolation=cv2.INTER_LINEAR)
    ksize = max(canvas_w, canvas_h) // 10 | 1
    bg = cv2.GaussianBlur(bg, (ksize, ksize), 0)

    scale = min(content_w / sw, content_h / sh)
    new_w = int(sw * scale)
    new_h = int(sh * scale)
    fg = cv2.resize(src, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    x_off = (canvas_w - new_w) // 2
    y_off = (canvas_h - new_h) // 2
    bg[y_off:y_off + new_h, x_off:x_off + new_w] = fg
    return bg, (x_off, y_off, new_w, new_h)


def create_ken_burns_clip(
    image_path: str,
    output_path: str,
    duration: float,
    width: int = 1920,
    height: int = 1080,
    fps: int = 25,
    effect_type: str = 'zoom_in',
    ffmpeg_path: str = 'ffmpeg',
    idle_timeout: float = _FFMPEG_IDLE_TIMEOUT_SECONDS,
    fade_in_seconds: float = 0.0,
    fade_out_seconds: float = 0.0,
) -> None:
    """OpenCV  Ken Burns , pipe rawvideo  FFmpeg . 
     dùng _prepare_canvas tương thích mọi tỷ lệ khung hình, getRectSubPix thực hiện cắt với độ chính xác dấu phẩy động. """
    import cv2

    total_frames = max(int(duration * fps), 1)
    src = cv2.imread(image_path)
    if src is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    max_zoom = KEN_BURNS_MAX_ZOOM
    pan_canvas_scale = KEN_BURNS_PAN_CANVAS_SCALE
    canvas_scale = max(max_zoom, pan_canvas_scale)
    canvas_w = int(width * canvas_scale)
    canvas_h = int(height * canvas_scale)
    # Backend logic
    safe_content_w = max(1, int(width / max_zoom))
    safe_content_h = max(1, int(height / max_zoom))
    img, (slide_x, slide_y, slide_w, slide_h) = _prepare_canvas(
        src,
        safe_content_w,
        safe_content_h,
        canvas_w,
        canvas_h,
    )
    ih, iw = img.shape[:2]

    fade_filters: List[str] = []
    if fade_in_seconds > 0:
        fade_filters.append(f'fade=t=in:st=0:d={fade_in_seconds}')
    if fade_out_seconds > 0:
        fade_out_start = max(duration - fade_out_seconds, 0.0)
        fade_filters.append(f'fade=t=out:st={fade_out_start}:d={fade_out_seconds}')

    cmd = [
        ffmpeg_path, '-y',
        '-f', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', f'{width}x{height}', '-r', str(fps),
        '-i', 'pipe:0',
        '-t', str(duration),
    ]
    if fade_filters:
        cmd += ['-vf', ','.join(fade_filters)]
    cmd += [
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-preset', 'medium', '-crf', '23',
        '-movflags', '+faststart',
        output_path,
    ]

    proc = subprocess.Popen(
        _inject_ffmpeg_progress_args(cmd),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    try:
        for i in range(total_frames):
            t = i / max(total_frames - 1, 1)

            if effect_type == 'zoom_in':
                z = 1.0 + (max_zoom - 1.0) * t
                cx, cy = iw / 2.0, ih / 2.0
            elif effect_type == 'zoom_out':
                z = max_zoom - (max_zoom - 1.0) * t
                cx, cy = iw / 2.0, ih / 2.0
            elif effect_type == 'pan_right':
                z = 1.0
                min_cx = max(width / 2.0, slide_x + slide_w - width / 2.0)
                max_cx = min(iw - width / 2.0, slide_x + width / 2.0)
                cx = min_cx + max(max_cx - min_cx, 0.0) * t
                cy = ih / 2.0
            elif effect_type == 'pan_left':
                z = 1.0
                min_cx = max(width / 2.0, slide_x + slide_w - width / 2.0)
                max_cx = min(iw - width / 2.0, slide_x + width / 2.0)
                cx = max_cx - max(max_cx - min_cx, 0.0) * t
                cy = ih / 2.0
            else:
                z = 1.0 + (max_zoom - 1.0) * t
                cx, cy = iw / 2.0, ih / 2.0

            crop_w = width / z
            crop_h = height / z
            cx = max(crop_w / 2.0, min(cx, iw - crop_w / 2.0))
            cy = max(crop_h / 2.0, min(cy, ih - crop_h / 2.0))

            patch = cv2.getRectSubPix(img, (int(crop_w + 0.5), int(crop_h + 0.5)), (cx, cy))
            frame = cv2.resize(patch, (width, height), interpolation=cv2.INTER_LINEAR)
            proc.stdin.write(frame.tobytes())

        proc.stdin.close()
        _wait_for_process_with_idle_watchdog(
            proc,
            "FFmpeg failed for Ken Burns clip",
            idle_timeout=idle_timeout,
        )
    except Exception:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise


def create_silent_clip(
    image_path: str,
    output_path: str,
    duration: float = 3.0,
    width: int = 1920,
    height: int = 1080,
    fps: int = 25,
    effect_type: str = 'zoom_in',
    enable_ken_burns: bool = True,
    ffmpeg_path: str = 'ffmpeg',
    idle_timeout: float = _FFMPEG_IDLE_TIMEOUT_SECONDS,
    fade_in_seconds: float = 0.0,
    fade_out_seconds: float = 0.0,
) -> None:
    """ Backend docstring """
    if enable_ken_burns:
        tmp_video = output_path + '.tmp.mp4'
        create_ken_burns_clip(
            image_path, tmp_video, duration,
            width=width, height=height, fps=fps,
            effect_type=effect_type, ffmpeg_path=ffmpeg_path, idle_timeout=idle_timeout,
            fade_in_seconds=fade_in_seconds, fade_out_seconds=fade_out_seconds,
        )
        cmd = [
            ffmpeg_path, '-y',
            '-i', tmp_video,
            '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-c:v', 'copy', '-c:a', 'aac', '-shortest',
            '-movflags', '+faststart',
            output_path,
        ]
        try:
            _run_ffmpeg_command(cmd, "FFmpeg failed for silent clip", idle_timeout=idle_timeout)
        finally:
            if os.path.exists(tmp_video):
                os.remove(tmp_video)
    else:
        vf = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        if fade_in_seconds > 0:
            vf += f",fade=t=in:st=0:d={fade_in_seconds}"
        if fade_out_seconds > 0:
            fade_out_start = max(duration - fade_out_seconds, 0.0)
            vf += f",fade=t=out:st={fade_out_start}:d={fade_out_seconds}"
        cmd = [
            ffmpeg_path, '-y',
            '-loop', '1',
            '-i', image_path,
            '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-vf', vf,
            '-t', str(duration),
            '-r', str(fps),
            '-c:v', 'libx264', '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium', '-crf', '23',
            '-shortest', '-movflags', '+faststart',
            output_path,
        ]
        _run_ffmpeg_command(cmd, "FFmpeg failed for silent clip", idle_timeout=idle_timeout)


def create_static_clip(
    image_path: str,
    output_path: str,
    duration: float,
    width: int = 1920,
    height: int = 1080,
    fps: int = 25,
    ffmpeg_path: str = 'ffmpeg',
    idle_timeout: float = _FFMPEG_IDLE_TIMEOUT_SECONDS,
    fade_in_seconds: float = 0.0,
    fade_out_seconds: float = 0.0,
) -> None:
    """ Backend docstring """
    vf = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    if fade_in_seconds > 0:
        vf += f",fade=t=in:st=0:d={fade_in_seconds}"
    if fade_out_seconds > 0:
        fade_out_start = max(duration - fade_out_seconds, 0.0)
        vf += f",fade=t=out:st={fade_out_start}:d={fade_out_seconds}"

    cmd = [
        ffmpeg_path, '-y',
        '-loop', '1',
        '-i', image_path,
        '-vf', vf,
        '-t', str(duration),
        '-r', str(fps),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'medium',
        '-crf', '23',
        '-movflags', '+faststart',
        output_path,
    ]

    logger.debug(f"Static clip: {duration:.1f}s, {width}x{height}")
    _run_ffmpeg_command(cmd, "FFmpeg failed for static clip", idle_timeout=idle_timeout)


# ═══════════════════════════════════════════════════════════════════════════════
# Backend logic
# ═══════════════════════════════════════════════════════════════════════════════


def _format_ass_time(seconds: float) -> str:
    """ Backend docstring """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _split_narration_to_sentences(text: str) -> List[str]:
    """
    . 
    /, , , 
    /. 
    """
    # Backend logic
    raw_parts = re.split(r'(?<=[. ! ? !?\n])', text.strip())
    sentences = [p.strip() for p in raw_parts if p.strip()]

    # Backend logic
    result = []
    for sent in sentences:
        if len(sent) <= _MAX_SUBTITLE_SEGMENT_LENGTH:
            result.append(sent)
            continue
        # Backend logic
        sub_parts = re.split(r'(?<=[, ; , ,;])', sent)
        current = ''
        for part in sub_parts:
            if len(current) + len(part) <= _MAX_SUBTITLE_SEGMENT_LENGTH:
                current += part
            else:
                if current:
                    result.append(current)
                # Backend logic
                while len(part) > _MAX_SUBTITLE_SEGMENT_LENGTH:
                    result.append(part[:_MAX_SUBTITLE_SEGMENT_LENGTH])
                    part = part[_MAX_SUBTITLE_SEGMENT_LENGTH:]
                current = part
        if current:
            result.append(current)

    return result if result else [text.strip()]


def _build_timed_subtitle_entries_from_alignment(
    narration_text: str,
    page_start: float,
    alignment: dict,
) -> List[dict]:
    """
     ElevenLabs , . 

    : sentence  vs alignment.characters , 
     () ,  start  start+duration . 
    """
    sentences = _split_narration_to_sentences(narration_text)
    if not sentences:
        return []

    chars = alignment.get('characters') or []
    starts = alignment.get('character_start_times_ms') or []
    durs = alignment.get('character_durations_ms') or []
    if not chars or len(chars) != len(starts) or len(chars) != len(durs):
        return []

    entries: List[dict] = []
    align_idx = 0
    n = len(chars)

    for sent in sentences:
        target = sent
        # Backend logic
        while align_idx < n and not chars[align_idx].strip():
            align_idx += 1
        if align_idx >= n:
            break

        sent_start_idx = align_idx
        # Backend logic
        ti = 0
        i = align_idx
        last_match_idx = align_idx
        while i < n and ti < len(target):
            tch = target[ti]
            ach = chars[i]
            if not tch.strip():
                ti += 1
                continue
            if not ach.strip():
                i += 1
                continue
            # Backend logic
            if tch == ach or tch.lower() == ach.lower():
                last_match_idx = i
                i += 1
                ti += 1
            else:
                # Backend logic
                i += 1

        sent_end_idx = last_match_idx
        start_ms = starts[sent_start_idx]
        end_ms = starts[sent_end_idx] + durs[sent_end_idx]
        entries.append({
            'start': page_start + start_ms / 1000.0,
            'end': page_start + end_ms / 1000.0,
            'text': sent,
        })
        align_idx = i

    return entries


def _build_timed_subtitle_entries(
    narration_text: str,
    page_start: float,
    page_duration: float,
) -> List[dict]:
    """
    . 

    Thời lượng của mỗi mục tỷ lệ thuận với số ký tự của nó, thực hiện"đọc theo"hiệu quả. 
    """
    sentences = _split_narration_to_sentences(narration_text)
    if not sentences:
        return []

    total_chars = sum(len(s) for s in sentences)
    if total_chars == 0:
        return []

    entries = []
    t = page_start
    for sent in sentences:
        # Backend logic
        seg_duration = page_duration * len(sent) / total_chars
        entries.append({
            'start': t,
            'end': t + seg_duration,
            'text': sent,
        })
        t += seg_duration

    # Backend logic
    if entries:
        entries[-1]['end'] = page_start + page_duration

    return entries


# Backend logic
# Backend logic
_CJK_FONT_FILE_CANDIDATES: List[Tuple[str, str]] = [
    # macOS
    ('/System/Library/Fonts/PingFang.ttc', 'PingFang SC'),
    ('/System/Library/Fonts/Hiragino Sans GB.ttc', 'Hiragino Sans GB'),
    ('/System/Library/Fonts/STHeiti Medium.ttc', 'Heiti SC'),
    ('/System/Library/Fonts/STHeiti Light.ttc', 'Heiti SC'),
    ('/Library/Fonts/Songti.ttc', 'Songti SC'),
    # Linux
    ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'Noto Sans CJK SC'),
    ('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 'Noto Sans CJK SC'),
    ('/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc', 'Noto Sans CJK SC'),
    ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 'Noto Sans CJK SC'),
    ('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', 'Noto Serif CJK SC'),
    # Windows
    ('C:/Windows/Fonts/msyh.ttc', 'Microsoft YaHei'),
    ('C:/Windows/Fonts/msyh.ttf', 'Microsoft YaHei'),
    ('C:/Windows/Fonts/simhei.ttf', 'SimHei'),
]


def _resolve_cjk_font_file() -> Optional[Tuple[str, str]]:
    """
     CJK . 

     (font_file_path, font_family_name);  None. 
     ( fc-list  macOS  libass ) . 
    """
    for path, family in _CJK_FONT_FILE_CANDIDATES:
        if os.path.exists(path):
            return path, family

    # Backend logic
    try:
        env = {**os.environ, 'LC_ALL': 'C', 'LANG': 'C'}
        result = subprocess.run(
            ['fc-match', '-f', '%{file}|%{family}', ':lang=zh'],
            capture_output=True, text=True, timeout=5, env=env,
        )
        out = result.stdout.strip()
        if out and '|' in out:
            file_part, family_part = out.split('|', 1)
            family = family_part.split(',')[0].strip()
            if file_part and os.path.exists(file_part) and family:
                return file_part, family
    except Exception:
        pass

    return None


def _detect_cjk_font() -> str:
    """ Backend docstring """
    resolved = _resolve_cjk_font_file()
    if resolved:
        return resolved[1]
    return 'Noto Sans CJK SC'


def _detect_cjk_font_dir() -> Optional[str]:
    """ Backend docstring """
    resolved = _resolve_cjk_font_file()
    if resolved:
        return os.path.dirname(resolved[0])
    return None


def generate_ass_subtitle(
    subtitle_entries: List[dict],
    output_path: str,
    width: int = 1920,
    height: int = 1080,
    font_size: int = 0,
) -> None:
    """
     ASS  (, CJK ) . 

    Args:
        subtitle_entries: ,  start/end/text
        output_path:  ASS 
        width: 
        height: 
        font_size: , 0 
    """
    if font_size <= 0:
        font_size = max(28, int(height / 25))  # 1080p → 43

    font_name = _detect_cjk_font()
    margin_v = max(40, int(height / 18))  # Backend logic
    outline = max(2, int(font_size / 16))
    shadow = 1
    spacing = 1  # Backend logic

    # Backend logic
    # Backend logic
    # Backend logic
    # Backend logic
    # Backend logic

    header = f"""[Script Info]
Title: Narration Subtitles
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00202020,&H96000000,-1,0,0,0,100,100,{spacing},0,3,{outline},{shadow},2,50,50,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    with open(output_path, 'w', encoding='utf-8-sig') as f:
        f.write(header)
        for entry in subtitle_entries:
            start = _format_ass_time(entry['start'])
            end = _format_ass_time(entry['end'])
            text = _sanitize_ass_dialogue_text(entry['text'])
            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")


def _strip_invisible_unicode(text: str, keep_newlines: bool = False) -> str:
    """
     Unicode ,  ASS  TTS alignment . 

     Cc/Cf/Co/Cs/Cn , / U+2028/U+2029. 
    keep_newlines=True  \n / \r / \t ( TTS , ) . 
    """
    out = []
    for ch in text:
        if keep_newlines and ch in ('\n', '\r', '\t'):
            out.append(ch)
            continue
        if ch in ('\u2028', '\u2029'):
            continue
        cat = unicodedata.category(ch)
        if cat[0] == 'C':
            continue
        out.append(ch)
    return ''.join(out)


def _sanitize_ass_dialogue_text(text: str) -> str:
    """
    ,  libass  ASS override . 

    libass  Dialogue Text : 
      - `{...}` là nội tuyến override khối , sẽ bị mất hoặc kết xuất sai; 
      - `\\N` `\\h` `\\n` và các chuỗi dấu gạch chéo ngược là libass escape; 
      -  (ZWSP / BOM / LRE )  shaping. 

    Khi lời thuyết minh đôi lúc xuất hiện các ký tự này, toàn bộ lời thoại sẽ bị phân tích sai, trở thành hiển thị trực quan"lỗi phông chữ/ô vuông". 
    loại bỏ ký tự điều khiển trước, sau đó đem `\\` `{` `}` thay thế bằng ký tự toàn giác tương đương. 
    """
    cleaned = _strip_invisible_unicode(text, keep_newlines=False)
    return (
        cleaned
        .replace('\\', '')
        .replace('{', '')
        .replace('}', '')
    )


def _escape_ffmpeg_filter_value(value: str) -> str:
    """ Backend docstring """
    escaped = value.replace('\\', '/')
    for old, new in (
        (':', '\\:'),
        ("'", "\\'"),
        (',', '\\,'),
        ('[', '\\['),
        (']', '\\]'),
        (';', '\\;'),
    ):
        escaped = escaped.replace(old, new)
    return escaped


def burn_subtitles(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    ffmpeg_path: str = 'ffmpeg',
    idle_timeout: float = _FFMPEG_IDLE_TIMEOUT_SECONDS,
) -> None:
    """ Backend docstring """
    escaped_sub = _escape_ffmpeg_filter_value(subtitle_path)

    ass_args = f"ass=filename='{escaped_sub}'"
    fonts_dir = _detect_cjk_font_dir()
    if fonts_dir:
        escaped_fontsdir = _escape_ffmpeg_filter_value(fonts_dir)
        ass_args += f":fontsdir='{escaped_fontsdir}'"

    cmd = [
        ffmpeg_path, '-y',
        '-i', video_path,
        '-vf', ass_args,
        '-c:v', 'libx264',
        '-c:a', 'copy',
        '-pix_fmt', 'yuv420p',
        '-preset', 'medium',
        '-crf', '23',
        '-movflags', '+faststart',
        output_path,
    ]
    _run_ffmpeg_command(cmd, "FFmpeg subtitle burn failed", idle_timeout=idle_timeout)


# ═══════════════════════════════════════════════════════════════════════════════
# Backend logic
# ═══════════════════════════════════════════════════════════════════════════════


def mux_video_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
    ffmpeg_path: str = 'ffmpeg',
    idle_timeout: float = _FFMPEG_IDLE_TIMEOUT_SECONDS,
) -> None:
    """ Backend docstring """
    cmd = [
        ffmpeg_path, '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        '-movflags', '+faststart',
        output_path,
    ]
    _run_ffmpeg_command(cmd, "FFmpeg mux failed", idle_timeout=idle_timeout)


def composite_video(
    clip_paths: List[str],
    output_path: str,
    fps: int = 25,
    ffmpeg_path: str = 'ffmpeg',
    idle_timeout: float = _FFMPEG_IDLE_TIMEOUT_SECONDS,
) -> None:
    """
     FFmpeg concat demuxer  MP4. 

    Args:
        clip_paths: 
        output_path:  MP4 
        fps:  () 
        ffmpeg_path: ffmpeg 
        idle_timeout: 
    """
    if len(clip_paths) == 1:
        # Backend logic
        shutil.copy2(clip_paths[0], output_path)
        return

    # Backend logic
    concat_file = output_path + '.concat.txt'
    try:
        with open(concat_file, 'w') as f:
            for path in clip_paths:
                # Backend logic
                safe_path = os.path.abspath(path)
                if '\n' in safe_path or '\r' in safe_path:
                    raise ValueError(f"Invalid clip path contains newline: {safe_path}")
                # Backend logic
                escaped = safe_path.replace("'", "''")
                f.write(f"file '{escaped}'\n")

        cmd = [
            ffmpeg_path, '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-r', str(fps),
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium',
            '-crf', '23',
            '-movflags', '+faststart',
            output_path,
        ]
        _run_ffmpeg_command(cmd, "FFmpeg concat failed", idle_timeout=idle_timeout)
    finally:
        if os.path.exists(concat_file):
            os.remove(concat_file)

    logger.info(f"Final video composited: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# Backend logic
# ═══════════════════════════════════════════════════════════════════════════════


def generate_narration_video(
    pages_data: List[dict],
    output_path: str,
    voice: str = 'zh-CN-XiaoxiaoNeural',
    rate: str = '+0%',
    width: int = 1920,
    height: int = 1080,
    fps: int = 25,
    enable_ken_burns: bool = False,
    ffmpeg_path: str = 'ffmpeg',
    progress_callback: Optional[Callable[[str, str, int], None]] = None,
    silent_duration: float = 0,
    fail_fast: bool = False,
    elevenlabs_config: Optional[dict] = None,
    speed: float = 1.0,
) -> None:
    """
    . 

    Args:
        pages_data: , :
            - image_path: str  
            - narration_text: str | None  
            - page_index: int   ( 0 ) 
        output_path:  MP4 
        voice: TTS 
        rate: 
        width: 
        height: 
        fps: 
        enable_ken_burns:  Ken Burns  () 
        ffmpeg_path: ffmpeg 
        progress_callback:  (step, message, percent)
        silent_duration:  () , 0 
        fail_fast: 
    """
    if not pages_data:
        raise ValueError("No pages to process")

    # Backend logic
    if not check_ffmpeg_available(ffmpeg_path):
        raise RuntimeError(
            "FFmpeg is not installed or not found in PATH. "
            "Please install FFmpeg to use video export."
        )

    requires_subtitles = any((page.get('narration_text') or '').strip() for page in pages_data)
    if requires_subtitles and not check_ffmpeg_ass_filter_available(ffmpeg_path):
        raise RuntimeError(
            "hiện tại FFmpeg không hỗ trợ ASS gắn phụ đề (thiếu libass / ass filter) . "
            "Xuất video cần cài đặt bản có libass FFmpeg. "
            "Vui lòng cài đặt hoặc cài lại bản hỗ trợ ASS có phụ đề FFmpeg rồi thử lại. "
        )

    if silent_duration <= 0:
        silent_duration = _DEFAULT_SILENT_DURATION

    tmp_dir = output_path + '_tmp'
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        total = len(pages_data)
        muxed_clips: List[str] = []
        subtitle_entries: List[dict] = []
        cumulative_time = 0.0

        # Backend logic
        # Backend logic
        page_durations: List[float] = []
        audio_paths: List[Optional[str]] = []
        alignments: List[Optional[dict]] = []
        silent_page_indexes: List[int] = []

        # Backend logic
        # Backend logic
        # Backend logic
        narration_indexes = [
            idx for idx, p in enumerate(pages_data)
            if (p.get('narration_text') or '').strip()
        ]
        whole_text_results: Optional[dict] = None
        if (
            elevenlabs_config and elevenlabs_config.get('api_key')
            and len(narration_indexes) >= 2
        ):
            whole_text_pairs = _generate_elevenlabs_whole_and_split(
                pages_data, narration_indexes, tmp_dir,
                api_key=elevenlabs_config['api_key'],
                voice_id=elevenlabs_config.get('voice_id') or 'JBFqnCBsd6RMkjVDRZzb',
                ffmpeg_path=ffmpeg_path,
                speed=speed,
                progress_callback=progress_callback,
            )
            whole_text_results = dict(zip(narration_indexes, whole_text_pairs))

        for i, page in enumerate(pages_data):
            narration = page.get('narration_text')
            page_idx = page.get('page_index', i)

            audio_path = None
            alignment: Optional[dict] = None
            duration = silent_duration
            if narration and narration.strip():
                if whole_text_results is not None and i in whole_text_results:
                    audio_path, alignment, duration = whole_text_results[i]
                else:
                    audio_path = os.path.join(tmp_dir, f'audio_{i:03d}.mp3')
                    try:
                        if elevenlabs_config and elevenlabs_config.get('api_key'):
                            duration, alignment = generate_elevenlabs_audio_sync(
                                narration, audio_path,
                                api_key=elevenlabs_config['api_key'],
                                voice_id=elevenlabs_config.get('voice_id') or 'JBFqnCBsd6RMkjVDRZzb',
                                ffmpeg_path=ffmpeg_path,
                                speed=speed,
                            )
                        else:
                            # Backend logic
                            effective_rate = rate
                            if abs(speed - 1.0) > 1e-3:
                                pct = int(round((speed - 1.0) * 100))
                                effective_rate = f"{'+' if pct >= 0 else ''}{pct}%"
                            duration = generate_tts_audio_sync(
                                narration, audio_path, voice=voice, rate=effective_rate, ffmpeg_path=ffmpeg_path,
                            )
                    except Exception as e:
                        if fail_fast:
                            raise RuntimeError(
                                f" {page_idx + 1} , "", : {e}"
                            ) from e

                        logger.warning(f"TTS failed for page {page_idx}: {e}, using silent clip")
                        audio_path = None
                        alignment = None
                        duration = silent_duration
                        silent_page_indexes.append(page_idx + 1)
            else:
                if fail_fast:
                    raise RuntimeError(
                        f" {page_idx + 1} , "", . "
                    )
                silent_page_indexes.append(page_idx + 1)

            page_durations.append(duration)
            audio_paths.append(audio_path)
            alignments.append(alignment)

            if progress_callback:
                pct = int(20 + (i + 1) / total * 30)  # 20-50%
                if audio_path:
                    message = f"Đã tạo trang {i+1}/{total} trang âm thanh"
                else:
                    message = f"trang {i+1}/{total} trang không có giọng đọc hợp lệ, chuyển thành đoạn âm thanh tĩnh"
                progress_callback("TTS", message, pct)

        if fail_fast and silent_page_indexes:
            pages = ', '.join(str(idx) for idx in silent_page_indexes)
            raise RuntimeError(
                f":  {pages} . "", . "
            )

        # Backend logic
        for i, page in enumerate(pages_data):
            image_path = page['image_path']
            narration = page.get('narration_text')
            page_idx = page.get('page_index', i)
            effect = KEN_BURNS_EFFECTS[page_idx % len(KEN_BURNS_EFFECTS)]
            audio_duration = page_durations[i]
            audio_path = audio_paths[i]
            alignment = alignments[i]

            # Backend logic
            is_first = (i == 0)
            is_last = (i == total - 1)
            leading_pad = _LEADING_PAD_SECONDS if is_first else 0.0
            trailing_pad = _TRAILING_PAD_SECONDS if is_last else 0.0

            if audio_path and (leading_pad > 0 or trailing_pad > 0):
                padded_audio = os.path.join(tmp_dir, f'audio_padded_{i:03d}.mp3')
                pad_audio_with_silence(
                    audio_path, padded_audio,
                    leading_seconds=leading_pad,
                    trailing_seconds=trailing_pad,
                    ffmpeg_path=ffmpeg_path,
                )
                audio_path = padded_audio

            display_duration = audio_duration + leading_pad + trailing_pad

            # Backend logic
            sub_start = cumulative_time + leading_pad
            if narration and narration.strip() and audio_paths[i]:
                if alignment:
                    page_subs = _build_timed_subtitle_entries_from_alignment(
                        narration.strip(), sub_start, alignment,
                    )
                else:
                    page_subs = _build_timed_subtitle_entries(
                        narration.strip(), sub_start, audio_duration,
                    )
                subtitle_entries.extend(page_subs)
            cumulative_time += display_duration

            if audio_paths[i]:
                video_clip = os.path.join(tmp_dir, f'video_{i:03d}.mp4')
                if enable_ken_burns:
                    create_ken_burns_clip(
                        image_path, video_clip, display_duration,
                        width=width, height=height, fps=fps,
                        effect_type=effect, ffmpeg_path=ffmpeg_path,
                        fade_in_seconds=leading_pad,
                        fade_out_seconds=trailing_pad,
                    )
                else:
                    create_static_clip(
                        image_path, video_clip, display_duration,
                        width=width, height=height, fps=fps,
                        ffmpeg_path=ffmpeg_path,
                        fade_in_seconds=leading_pad,
                        fade_out_seconds=trailing_pad,
                    )

                # Mux video + audio
                muxed_path = os.path.join(tmp_dir, f'muxed_{i:03d}.mp4')
                mux_video_audio(video_clip, audio_path, muxed_path, ffmpeg_path=ffmpeg_path)
                muxed_clips.append(muxed_path)
            else:
                # Backend logic
                silent_path = os.path.join(tmp_dir, f'silent_{i:03d}.mp4')
                create_silent_clip(
                    image_path, silent_path, duration=display_duration,
                    width=width, height=height, fps=fps,
                    effect_type=effect, enable_ken_burns=enable_ken_burns,
                    ffmpeg_path=ffmpeg_path,
                    fade_in_seconds=leading_pad,
                    fade_out_seconds=trailing_pad,
                )
                muxed_clips.append(silent_path)

            if progress_callback:
                pct = int(50 + (i + 1) / total * 30)  # 50-80%
                progress_callback("Video", f"Đã tạo trang {i+1}/{total} đoạn video trang", pct)

        # Backend logic
        if progress_callback:
            progress_callback("Tổng hợp", "Đang ghép nối video...", 82)

        raw_video = os.path.join(tmp_dir, 'raw_composite.mp4')
        composite_video(muxed_clips, raw_video, fps=fps, ffmpeg_path=ffmpeg_path)

        # Backend logic
        if subtitle_entries:
            if progress_callback:
                progress_callback("Phụ đề", "Đang gắn phụ đề vào video...", 88)

            ass_path = os.path.join(tmp_dir, 'subtitles.ass')
            generate_ass_subtitle(subtitle_entries, ass_path, width=width, height=height)
            burn_subtitles(raw_video, ass_path, output_path, ffmpeg_path=ffmpeg_path)
        else:
            shutil.copy2(raw_video, output_path)

        if progress_callback:
            progress_callback("Hoàn tất", "Hoàn tất xuất video", 100)

    finally:
        # Backend logic
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)