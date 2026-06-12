import signal
import tempfile

from config import (
    MIC_DEVICE_NAME,
    STT_MAX_DURATION,
    STT_MODEL,
    STT_SILENCE_SECONDS,
    STT_SILENCE_THRESHOLD,
)

def _raise_timeout(signum, frame):
    raise TimeoutError("audio setup timed out")

class SpeechToText:
    def __init__(self):
        print(f"Loading Whisper {STT_MODEL} model...")
        from faster_whisper import WhisperModel
        print("[STT] Whisper library loaded.")
        # Prefer float16 for better accuracy when supported; fall back to int8 on CPUs without float16
        try:
            self.model = WhisperModel(STT_MODEL, device="cpu", compute_type="float16", local_files_only=False)
            print("[STT] Whisper model ready (multilingual, float16).")
            self.compute_type = "float16"
        except ValueError as e:
            print(f"[STT] float16 not supported on this device: {e}. Falling back to int8 compute.")
            self.model = WhisperModel(STT_MODEL, device="cpu", compute_type="int8", local_files_only=False)
            print("[STT] Whisper model ready (multilingual, int8).")
            self.compute_type = "int8"
        self.sd = None
        self.np = None
        self.sf = None
        self.device_index = None
        self.sample_rate = 16000
        print("STT ready.")

    def _ensure_audio(self):
        if self.sd is None:
            self.sd = self._load_sounddevice()
            self.np = self._load_numpy()
            self.sf = self._load_soundfile()
            self.device_index = self._find_best_mic()
            self.sample_rate = self._get_device_samplerate(self.device_index)
            print(f"[MIC] Selected device index: {self.device_index} at {self.sample_rate} Hz")

    def _load_sounddevice(self):
        old_handler = signal.signal(signal.SIGALRM, _raise_timeout)
        try:
            signal.alarm(5)
            import sounddevice as sd
            signal.alarm(0)
            return sd
        except Exception as e:
            signal.alarm(0)
            raise RuntimeError(f"Microphone support is unavailable: {e}") from e
        finally:
            signal.signal(signal.SIGALRM, old_handler)

    def _load_numpy(self):
        import numpy as np
        return np

    def _load_soundfile(self):
        import soundfile as sf
        return sf

    def _find_best_mic(self):
        old_handler = signal.signal(signal.SIGALRM, _raise_timeout)
        try:
            signal.alarm(5)
            devices = self.sd.query_devices()
            signal.alarm(0)
            input_devices = [
                (i, d) for i, d in enumerate(devices)
                if d["max_input_channels"] > 0 and "monitor" not in d["name"].lower()
            ]

            preferred = MIC_DEVICE_NAME.strip().lower()
            if preferred:
                for i, d in input_devices:
                    if d["name"].lower() == preferred:
                        print(f"[MIC] Selected configured device: {d['name']}")
                        return i
                if preferred not in ["default", "pulse"]:
                    for i, d in input_devices:
                        if preferred in d["name"].lower():
                            print(f"[MIC] Selected configured device: {d['name']}")
                            return i

            default = self.sd.default.device[0]
            if isinstance(default, int) and default >= 0:
                default_name = self.sd.query_devices(default)["name"]
                if "monitor" not in default_name.lower():
                    print(f"[MIC] Selected system default: {default_name}")
                    return default

            for i, d in input_devices:
                name = d["name"].lower()
                if any(x in name for x in ["pulse", "pipewire", "default"]):
                    print(f"[MIC] Selected audio server device: {d['name']}")
                    return i

            for i, d in enumerate(devices):
                if d["max_input_channels"] > 0:
                    name = d["name"].lower()
                    if any(x in name for x in ["usb", "webcam", "headset", "micro", "built"]):
                        print(f"[MIC] Selected: {d['name']}")
                        return i
            for i, d in input_devices:
                if d["max_input_channels"] > 0:
                    print(f"[MIC] Selected fallback: {d['name']}")
                    return i
            print("[MIC] No microphone input device found.")
            return None
        except Exception as e:
            signal.alarm(0)
            print(f"[MIC] Using system default: {e}")
            return None
        finally:
            signal.signal(signal.SIGALRM, old_handler)

    def _get_device_samplerate(self, device_index):
        try:
            info = self.sd.query_devices(device_index, 'input')
            return int(info['default_samplerate'])
        except Exception:
            return 16000

    def listen_until_silence(self, max_duration=None, silence_threshold=None, silence_seconds=None):
        """Record audio for up to max_duration seconds.
        
        Instead of manually detecting speech via volume thresholds (unreliable
        with noisy/hot mics), we always record and rely on Whisper's built-in
        VAD filter to separate speech from noise during transcription.
        """
        self._ensure_audio()
        max_duration = max_duration or STT_MAX_DURATION

        frames = []
        print(f"[STT] Listening... speak now (recording up to {max_duration:g}s)")
        try:
            with self.sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=512,
                device=self.device_index
            ) as stream:
                max_blocks = int(max_duration * self.sample_rate / 512)
                for _ in range(max_blocks):
                    data, _ = stream.read(512)
                    frames.append(data.copy())

        except Exception as e:
            print(f"[STT] Listen error: {e}")
            return self.np.array([])

        if not frames:
            return self.np.array([])

        audio = self.np.concatenate(frames).flatten()
        print(f"[STT] Recorded {len(audio)/self.sample_rate:.1f}s of audio")
        return audio

    # Known Whisper hallucination phrases on silence/noise
    _HALLUCINATIONS = {
        "thank you", "thank you.", "thanks.", "thank you for watching",
        "thank you for watching.", "thank you very much",
        "thank you very much.", "thank you very much for watching",
        "thank you so much", "thanks for watching",
        "i don't know what to do", "i don't know what to say",
        "i don't know", "i'm here for dinner", "hello", "hello.",
        "bye", "bye.", "goodbye", "goodbye.", "yes, yes",
        "what are you doing", "what are you doing?",
        "subtitles by the amara.org community",
        "you", "the", "i", "a", "it", "is",
        "hmm", "hmm.", "mm.", "uh.", "oh.", "ah.", "so.", "so,",
    }

    def _is_hallucination(self, text: str) -> bool:
        t = (text or "").strip().lower().rstrip(".")
        if not t:
            return True
        if t in self._HALLUCINATIONS or (t + ".") in self._HALLUCINATIONS:
            return True
        # All non-latin characters (Japanese/Chinese/Arabic hallucinations)
        import re
        if re.fullmatch(r"[^a-z0-9\s]+", t.replace(",", "").replace(".", "")):
            return True
        # Repetitive dots/punctuation
        if re.fullmatch(r"[\s.,!?]+", t):
            return True
        # Repetitive words pattern
        words = t.split()
        if len(words) >= 4 and len(set(words)) <= 2:
            return True
        return False

    def transcribe(self, audio) -> str:
        if self.sf is None:
            self.sf = self._load_soundfile()
        if audio is None or len(audio) < 100:
            return ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                fname = f.name
            self.sf.write(fname, audio, self.sample_rate)
            segments, _ = self.model.transcribe(
                fname,
                language=None,
                vad_filter=True,
                vad_parameters=dict(threshold=0.1, min_silence_duration_ms=500),
                beam_size=5,
                best_of=5,
                temperature=[0.0, 0.2, 0.4],
                no_speech_threshold=0.6,
                condition_on_previous_text=False,
            )
            text = " ".join([s.text.strip() for s in segments]).strip()
            if self._is_hallucination(text):
                print(f"[STT] Rejected hallucination: '{text}'")
                return ""
            print(f"[STT] Heard: '{text}'")
            return text
        except Exception as e:
            print(f"[STT] Transcribe error: {e}")
            return ""

    def listen_and_transcribe(self) -> str:
        audio = self.listen_until_silence()
        return self.transcribe(audio)
