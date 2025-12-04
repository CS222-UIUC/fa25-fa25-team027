from __future__ import annotations
import time
import ssl
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import whisperx
import tempfile

import streamlit as st
from meeting_summarizer import MeetingSummarizer
from meeting_db import MeetingDatabase

ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(page_title="Meeting Minion", page_icon="📝", layout="wide")
device = "cpu"
batch_size = 4  # reduce if low on GPU mem
compute_type = "int8"  # change to "int8" if low on GPU mem (may reduce accuracy)
model_dir = "./model/whisperx_base"
hf_token = ""  # Add your Hugging Face token here if needed

# Load models lazily to avoid SSL errors at startup
model = None
alignment_model = None
alignment_metadata = None

# Initialize the meeting summarizer (using Ollama with llama3.2)
try:
    summarizer = MeetingSummarizer(model_name="llama3.2:latest")
except Exception as e:
    st.error(f"Failed to initialize MeetingSummarizer: {e}")
    st.info("Make sure Ollama is running and the model is installed.")
    summarizer = None

# Initialize the meeting database
try:
    meeting_db = MeetingDatabase("meetings.db")
except Exception as e:
    st.error(f"Failed to initialize database: {e}")
    meeting_db = None


@dataclass
class MeetingRecord:
    id: str
    created_at: str
    title: str
    transcript: str
    summary_heading: str
    key_points: List[str]
    action_items: List[Dict[str, Any]]
    decisions: List[str]


def _init_state() -> None:
    # Keep page state in session
    if "history_page" not in st.session_state:
        st.session_state.history_page = 0
    # No longer need to store history in session state - it's in the database!


def _now_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")


def _load_whisper_models():
    """Load WhisperX models lazily on first use"""
    global model, alignment_model, alignment_metadata

    if model is None:
        try:
            with st.spinner("Loading WhisperX models (first time only)..."):
                model = whisperx.load_model(
                    "base", device, compute_type=compute_type, download_root=model_dir
                )
                alignment_model, alignment_metadata = whisperx.load_align_model(
                    language_code="en", device=device
                )
        except Exception as e:
            st.error(f"Failed to load WhisperX models: {e}")
            st.info(
                "Audio transcription will not be available. You can still paste transcripts manually."
            )
            return False
    return True


def run_pipeline(audio_bytes: Optional[bytes], transcript_text: Optional[str]) -> Dict[str, Any]:
    """
    Process meeting audio/transcript using MeetingSummarizer

    Returns:
        Dictionary with transcript, summary_heading, key_points, action_items, decisions
    """
    transcript = transcript_text or "[PLACEHOLDER]\n"

    # If summarizer is not initialized, return basic structure
    if summarizer is None:
        return {
            "transcript": transcript,
            "summary_heading": "Meeting Summary (Summarizer unavailable)",
            "key_points": ["Summarizer not initialized. Please check Ollama setup."],
            "action_items": [],
            "decisions": [],
        }

    # Use summarizer with fallback for graceful error handling
    try:
        summary_result = summarizer.summarize_with_fallback(transcript)

        return {
            "transcript": transcript,
            "summary_heading": summary_result.get("summary_heading", "Meeting Summary"),
            "key_points": summary_result.get("key_points", []),
            "action_items": summary_result.get("action_items", []),
            "decisions": summary_result.get("decisions", []),
        }
    except Exception as e:
        st.error(f"Error during summarization: {e}")
        return {
            "transcript": transcript,
            "summary_heading": "Meeting Summary (Error)",
            "key_points": [f"Error: {str(e)}"],
            "action_items": [],
            "decisions": [],
        }


def sidebar_uploader() -> Dict[str, Any]:
    st.sidebar.header("Upload")

    if "audio_file" not in st.session_state:
        st.session_state.audio_name = None

    audio_file = st.sidebar.file_uploader(
        "Audio file (.mp3, .wav, .m4a)", type=["mp3", "wav", "m4a"], accept_multiple_files=False
    )

    speakers = st.sidebar.slider(
        "Pick the number of speakers in the audio", min_value=1, max_value=5
    )
    speaker_names = ["" for _ in range(speakers)]
    for i in range(speakers):
        speaker_names[i] = st.sidebar.text_input("Speaker {}".format(i + 1))

    transcript_text = ""
    st.subheader("Transcript")
    transcript_box = st.empty()
    if audio_file is not None and audio_file.name != st.session_state.audio_name:
        # Load models on first use
        if not _load_whisper_models():
            st.error("Cannot process audio without WhisperX models.")
        else:
            st.session_state.audio_name = audio_file.name
            st.audio(audio_file)
            suffix = "." + audio_file.name.split(".")[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_file.read())
                tmp_path = tmp.name

            audio = whisperx.load_audio(tmp_path)
            result = model.transcribe(audio, batch_size=batch_size)
            transcript_box.code(
                "\n".join([seg["text"] for seg in result["segments"]]), language="text"
            )

            result = whisperx.align(
                result["segments"],
                alignment_model,
                alignment_metadata,
                audio,
                device,
                return_char_alignments=False,
            )
            transcript_box.code(
                "\n".join([seg["text"] for seg in result["segments"]]), language="text"
            )

            # Try speaker diarization if HuggingFace token is provided
            if hf_token and hf_token.strip():
                try:
                    diarize_model = whisperx.diarize.DiarizationPipeline(
                        "pyannote/speaker-diarization-3.0", use_auth_token=hf_token, device=device
                    )
                    diarize_segments = diarize_model(
                        audio, min_speakers=speakers, max_speakers=speakers
                    )
                    result = whisperx.assign_word_speakers(diarize_segments, result)
                    transcript_text = "\n".join(
                        [
                            (seg.get("speaker", "Unknown") + ": " + seg["text"])
                            for seg in result["segments"]
                        ]
                    )
                    for i in range(speakers):
                        transcript_text = transcript_text.replace(
                            "SPEAKER_0" + str(i), speaker_names[i]
                        )
                except Exception as e:
                    st.warning(
                        f"Speaker diarization not available (requires HuggingFace token): {str(e)[:100]}"
                    )
                    # Fall back to transcript without speaker labels
                    transcript_text = "\n".join([seg["text"] for seg in result["segments"]])
            else:
                # No token provided, skip diarization
                st.info(
                    "Speaker diarization skipped (no HuggingFace token provided). Showing transcript only."
                )
                transcript_text = "\n".join([seg["text"] for seg in result["segments"]])

            transcript_box.code(transcript_text, language="text")

    for i in range(speakers):
        transcript_text = transcript_text.replace("SPEAKER_0" + str(i), speaker_names[i])
    transcript_box.code(transcript_text, language="text")

    st.sidebar.markdown("**OR** paste a transcript:")
    transcript_text = st.sidebar.text_area(
        "Transcript", placeholder="Paste transcript text here…", value=transcript_text, height=160
    )

    title = st.sidebar.text_input(
        "Meeting title", value=f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    process = st.sidebar.button("Process", type="primary", use_container_width=True)

    return {
        "audio_file": audio_file,
        "transcript_text": transcript_text.strip() or None,
        "title": title.strip(),
        "process": process,
    }


def progress_runner(label: str = "Processing") -> None:
    progress = st.progress(0, text=label)
    for i in range(1, 101, 8):
        time.sleep(0.04)
        progress.progress(min(i, 100), text=label)
    time.sleep(0.05)
    progress.empty()


def results_panel(record: MeetingRecord) -> None:
    st.success("Processing complete.")
    left, right = st.columns([2, 1])

    with left:
        with st.expander("Transcript", expanded=True):
            st.code(record.transcript or "", language="text")
            st.download_button(
                "Download transcript",
                data=record.transcript.encode("utf-8"),
                file_name=f"{record.id}_transcript.txt",
            )

        with st.expander("Summary: " + record.summary_heading, expanded=True):
            st.markdown("**Key Points:**")
            st.markdown(
                "\n".join([f"- {item}" for item in record.key_points]) or "_No key points._"
            )

            if record.decisions:
                st.markdown("\n**Decisions Made:**")
                st.markdown("\n".join([f"- {item}" for item in record.decisions]))

            # Create downloadable summary
            summary_text = f"{record.summary_heading}\n\n"
            summary_text += (
                "KEY POINTS:\n" + "\n".join([f"- {kp}" for kp in record.key_points]) + "\n\n"
            )
            if record.decisions:
                summary_text += (
                    "DECISIONS:\n" + "\n".join([f"- {d}" for d in record.decisions]) + "\n\n"
                )

            st.download_button(
                "Download summary (.txt)",
                data=summary_text.encode("utf-8"),
                file_name=f"{record.id}_summary.txt",
            )

        with st.expander("Action Items", expanded=True):
            if record.action_items:
                for ai in record.action_items:
                    if isinstance(ai, dict):
                        assignee = ai.get("assignee", "Unassigned")
                        task = ai.get("task", "")
                        deadline = ai.get("deadline")
                        st.markdown(
                            f"- **{assignee}**: {task}"
                            + (f" (Due: {deadline})" if deadline else "")
                        )
                    else:
                        st.markdown(f"- {ai}")
            else:
                st.markdown("_No action items._")

    with right:
        st.subheader("Meta")
        st.write({"id": record.id, "created_at": record.created_at, "title": record.title})


def save_record(title: str, payload: Dict[str, Any]) -> MeetingRecord:
    meeting_id = _now_id()
    created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # Save to database if available
    if meeting_db is not None:
        try:
            meeting_db.save_meeting(
                meeting_id=meeting_id,
                title=title or "Untitled Meeting",
                transcript=payload.get("transcript", ""),
                summary_heading=payload.get("summary_heading", "Meeting Summary"),
                key_points=payload.get("key_points", []),
                action_items=payload.get("action_items", []),
                decisions=payload.get("decisions", []),
                created_at=created_at,
            )
        except Exception as e:
            st.error(f"Failed to save to database: {e}")

    # Create record for immediate display
    rec = MeetingRecord(
        id=meeting_id,
        created_at=created_at,
        title=title or "Untitled Meeting",
        transcript=payload.get("transcript", ""),
        summary_heading=payload.get("summary_heading", "Meeting Summary"),
        key_points=payload.get("key_points", []),
        action_items=payload.get("action_items", []),
        decisions=payload.get("decisions", []),
    )
    return rec


def history_panel(page_size: int = 5) -> None:  # noqa: C901
    st.subheader("History")

    # Load history from database if available
    if meeting_db is None:
        st.warning("Database not available. History cannot be displayed.")
        return

    try:
        total = meeting_db.count_meetings()
        if total == 0:
            st.info("No past meetings.")
            return

        # Load paginated meetings from database
        offset = st.session_state.history_page * page_size
        history_data = meeting_db.get_all_meetings(limit=page_size, offset=offset)

        start = offset
        end = min(start + len(history_data), total)

        st.caption(f"Showing {start + 1}–{end} of {total}")

        # Convert database records to MeetingRecord objects for display
        history = []
        for db_record in history_data:
            # Create MeetingRecord from database data
            rec = MeetingRecord(
                id=db_record["id"],
                created_at=db_record["created_at"],
                title=db_record["title"],
                transcript=db_record["transcript"],
                summary_heading=db_record["summary_heading"],
                key_points=db_record["key_points"],
                action_items=db_record["action_items"],
                decisions=db_record["decisions"],
            )
            history.append(rec)
    except Exception as e:
        st.error(f"Failed to load history: {e}")
        return

    for rec in history:
        with st.container(border=True):
            st.markdown(f"**{rec.title}** · _{rec.created_at}_")
            st.markdown(f"**{rec.summary_heading}**")
            st.markdown("**Key Points Preview:**")
            st.write("\n".join([f"- {s}" for s in rec.key_points[:3]]) or "(empty)")
            cols = st.columns(3)
            with cols[0]:
                if st.button("View", key=f"view_{rec.id}"):
                    st.session_state.last_view = rec.id
            with cols[1]:
                st.download_button(
                    "Download transcript",
                    data=rec.transcript.encode("utf-8"),
                    file_name=f"{rec.id}_transcript.txt",
                    key=f"dl_t_{rec.id}",
                )
            with cols[2]:
                # Create summary text with new format
                summary_text = f"{rec.summary_heading}\n\n"
                summary_text += (
                    "KEY POINTS:\n" + "\n".join([f"- {kp}" for kp in rec.key_points]) + "\n\n"
                )
                if rec.decisions:
                    summary_text += (
                        "DECISIONS:\n" + "\n".join([f"- {d}" for d in rec.decisions]) + "\n\n"
                    )

                st.download_button(
                    "Download summary",
                    data=summary_text.encode("utf-8"),
                    file_name=f"{rec.id}_summary.txt",
                    key=f"dl_s_{rec.id}",
                )

    nav1, nav2, _, _ = st.columns(4)
    with nav1:
        if st.button("◀ Prev", disabled=start <= 0):
            st.session_state.history_page = max(0, st.session_state.history_page - 1)
    with nav2:
        if st.button("Next ▶", disabled=end >= total):
            st.session_state.history_page += 1


def main() -> None:
    _init_state()

    st.title("Meeting Minion")
    st.caption("Turn meeting recordings into transcripts, summaries, and action items.")

    controls = sidebar_uploader()

    with st.container(border=True):
        st.subheader("New Processing")
        st.write("Upload audio")

        if controls["process"]:
            if not controls["audio_file"] and not controls["transcript_text"]:
                st.warning("Please upload an audio file or paste a transcript.")
            else:
                audio_bytes = None
                if controls["audio_file"] is not None:
                    audio_bytes = controls["audio_file"].read()

                progress_runner("Processing meeting…")

                result = run_pipeline(
                    audio_bytes=audio_bytes, transcript_text=controls["transcript_text"]
                )

                rec = save_record(controls["title"], result)
                results_panel(rec)
        else:
            st.info("Ready.")

    st.divider()
    history_panel(page_size=5)


if __name__ == "__main__":
    main()
