import asyncio
import functools

from models.schemas import TranscriptSegment, TranscriptWord


def _run_whisper_sync(audio_path: str) -> list[TranscriptSegment]:
    """Synchronous Whisper transcription (runs in thread pool)."""
    from faster_whisper import WhisperModel

    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(
        audio_path,
        language="zh",
        word_timestamps=True,
        vad_filter=True,
    )

    result = []
    for seg in segments_iter:
        words = []
        if seg.words:
            words = [
                TranscriptWord(word=w.word.strip(), start=w.start, end=w.end)
                for w in seg.words
                if w.word.strip()
            ]
        result.append(TranscriptSegment(
            text=seg.text.strip(),
            start=seg.start,
            end=seg.end,
            words=words,
        ))

    return result


async def transcribe_with_whisper(audio_path: str) -> list[TranscriptSegment]:
    """Async wrapper that runs Whisper in a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(_run_whisper_sync, audio_path),
    )
