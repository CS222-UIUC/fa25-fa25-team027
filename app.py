from __future__ import annotations
import io
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import whisperx
import tempfile

import streamlit as st

st.set_page_config(page_title="Meeting Minion", page_icon="📝", layout="wide")
device = "cpu"
batch_size = 4 # reduce if low on GPU mem
compute_type = "int8" # change to "int8" if low on GPU mem (may reduce accuracy)
model_dir = "./model/whisperx_base"
model = whisperx.load_model("base", device, compute_type=compute_type, download_root=model_dir)
alignment_model, alignment_metadata = whisperx.load_align_model(language_code="en", device=device)
hf_token = ""  # Add your Hugging Face token here if needed
@dataclass
class MeetingRecord:
    id: str
    created_at: str
    title: str
    transcript: str
    summary: List[str]
    action_items: List[str]


def _init_state() -> None:
    if "history" not in st.session_state:
        st.session_state.history: List[MeetingRecord] = []
    if "history_page" not in st.session_state:
        st.session_state.history_page = 0


def _now_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")


def run_pipeline(audio_bytes: Optional[bytes], transcript_text: Optional[str]) -> Dict[str, Any]:

    time.sleep(0.2)
    transcript = transcript_text or "[PLACEHOLDER]\n"
    summary = [
        "Key decision: TODO — replace with model output",
        "Discussion point: TODO — replace with model output",
    ]
    action_items = [
        "@owner — TODO action, due MM/DD",
    ]
    return {"transcript": transcript, "summary": summary, "action_items": action_items}

def sidebar_uploader() -> Dict[str, Any]:
    st.sidebar.header("Upload")

    if "audio_file" not in st.session_state:
        st.session_state.audio_name = None

    audio_file = st.sidebar.file_uploader(
        "Audio file (.mp3, .wav, .m4a)", type=["mp3", "wav", "m4a"], accept_multiple_files=False
    )

    speakers = st.sidebar.slider("Pick the number of speakers in the audio", min_value = 1, max_value = 5)
    speaker_names = ["" for _ in range(speakers)]
    for i in range(speakers):
        speaker_names[i] = st.sidebar.text_input("Speaker {}".format(i+1))

    transcript_text = ""
    st.subheader("Transcript")
    transcript_box = st.empty()
    if audio_file is not None and audio_file.name != st.session_state.audio_name:
        st.session_state.audio_name = audio_file.name
        st.audio(audio_file)
        suffix = "." + audio_file.name.split(".")[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_file.read())
            tmp_path = tmp.name

        audio = whisperx.load_audio(tmp_path)
        result = model.transcribe(audio, batch_size=batch_size)
        transcript_box.code("\n".join([seg["text"] for seg in result["segments"]]), language="text")

        result = whisperx.align(result["segments"], alignment_model, alignment_metadata, audio, device, return_char_alignments=False)
        transcript_box.code("\n".join([seg["text"] for seg in result["segments"]]), language="text")
        
        diarize_model = whisperx.diarize.DiarizationPipeline("pyannote/speaker-diarization-3.0", use_auth_token=hf_token, device=device)
        diarize_segments = diarize_model(audio, min_speakers=speakers, max_speakers=speakers)
        result = whisperx.assign_word_speakers(diarize_segments, result)
        transcript_text = "\n".join([(seg["speaker"] + ": " + seg["text"]) for seg in result["segments"]])
        for i in range(speakers):
            transcript_text = transcript_text.replace("SPEAKER_0"+str(i), speaker_names[i])
        transcript_box.code(transcript_text, language="text")

    for i in range(speakers):
        transcript_text = transcript_text.replace("SPEAKER_0"+str(i), speaker_names[i])
    transcript_box.code(transcript_text, language="text")
        
    st.sidebar.markdown("**OR** paste a transcript:")
    transcript_text = st.sidebar.text_area("Transcript", placeholder="Paste transcript text here…", value=transcript_text, height=160)

    title = st.sidebar.text_input("Meeting title", value=f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    process = st.sidebar.button("Process", type="primary", use_container_width=True)

    return {"audio_file": audio_file, "transcript_text": transcript_text.strip() or None, "title": title.strip(), "process": process}


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
                "Download transcript", data=record.transcript.encode("utf-8"), file_name=f"{record.id}_transcript.txt"
            )

        with st.expander("Structured Summary", expanded=True):
            st.markdown("\n".join([f"- {item}" for item in record.summary]) or "_No summary._")
            st.download_button(
                "Download summary (.txt)",
                data=("\n".join(record.summary)).encode("utf-8"),
                file_name=f"{record.id}_summary.txt",
            )

        with st.expander("Action Items", expanded=True):
            st.markdown("\n".join([f"- {ai}" for ai in record.action_items]) or "_No action items._")

    with right:
        st.subheader("Meta")
        st.write({"id": record.id, "created_at": record.created_at, "title": record.title})


def save_record(title: str, payload: Dict[str, Any]) -> MeetingRecord:
    rec = MeetingRecord(
        id=_now_id(),
        created_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        title=title or "Untitled Meeting",
        transcript=payload.get("transcript", ""),
        summary=payload.get("summary", []),
        action_items=payload.get("action_items", []),
    )
    st.session_state.history.insert(0, rec)
    return rec


def history_panel(page_size: int = 5) -> None:
    st.subheader("History")
    history = st.session_state.history
    if not history:
        st.info("No past meetings.")
        return

    total = len(history)
    start = st.session_state.history_page * page_size
    end = min(start + page_size, total)

    st.caption(f"Showing {start+1}–{end} of {total}")

    for rec in history[start:end]:
        with st.container(border=True):
            st.markdown(f"**{rec.title}** · _{rec.created_at}_")
            st.markdown("**Summary preview:**")
            st.write("\n".join([f"- {s}" for s in rec.summary[:3]]) or "(empty)")
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
                st.download_button(
                    "Download summary",
                    data=("\n".join(rec.summary)).encode("utf-8"),
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

                result = run_pipeline(audio_bytes=audio_bytes, transcript_text=controls["transcript_text"])

                rec = save_record(controls["title"], result)
                results_panel(rec)
        else:
            st.info("Ready.")

    st.divider()
    history_panel(page_size=5)


if __name__ == "__main__":
    main()
