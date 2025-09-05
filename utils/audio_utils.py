"""
音檔處理工具模組
"""

import io
import tempfile
from pathlib import Path
from typing import List, Union
from pydub import AudioSegment


def combine_audio_segments(
    audio_segments: List[bytes], output_format: str = "mp3"
) -> bytes:
    """
    合併多個音檔片段

    Args:
        audio_segments: 音檔數據列表
        output_format: 輸出格式

    Returns:
        合併後的音檔數據
    """
    if not audio_segments:
        raise ValueError("音檔片段列表不能為空")

    combined = AudioSegment.empty()

    for segment_data in audio_segments:
        # 將bytes轉換為AudioSegment
        audio_io = io.BytesIO(segment_data)
        segment = AudioSegment.from_file(audio_io, format="mp3")
        combined += segment

    # 輸出為bytes
    output_io = io.BytesIO()
    combined.export(output_io, format=output_format)
    return output_io.getvalue()


def create_silence(duration_seconds: float) -> bytes:
    """
    創建指定時長的靜音音檔

    Args:
        duration_seconds: 靜音時長（秒）

    Returns:
        靜音音檔數據
    """
    silence = AudioSegment.silent(duration=int(duration_seconds * 1000))

    output_io = io.BytesIO()
    silence.export(output_io, format="mp3")
    return output_io.getvalue()


def save_audio_file(audio_data: bytes, file_path: Union[str, Path]) -> None:
    """
    將音檔數據保存到檔案

    Args:
        audio_data: 音檔數據
        file_path: 保存路徑
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(audio_data)


def get_audio_duration(file_path: Union[str, Path]) -> float:
    """
    獲取音檔時長

    Args:
        file_path: 音檔路徑

    Returns:
        音檔時長（秒）
    """
    audio = AudioSegment.from_file(str(file_path))
    return len(audio) / 1000.0  # 轉換為秒


def create_temp_file(suffix: str = ".mp3") -> str:
    """
    創建臨時檔案

    Args:
        suffix: 檔案後綴

    Returns:
        臨時檔案路徑
    """
    temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
    import os

    os.close(temp_fd)  # 關閉檔案描述符
    return temp_path
