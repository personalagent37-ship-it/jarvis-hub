import tempfile
import signal
import re
from config import MIC_DEVICE_NAME, WAKE_MIN_VOLUME

def _raise_timeout(signum, frame):
    raise TimeoutError("audio setup timed out")

class WakeWordDetector:
    def __init__(self, keyword: str = "jarvis"):
        self.keyword = keyword.lower()
        print("Loading wake word detector...")
        from faster_whisper import WhisperModel
        self.model = WhisperModel("tiny", device="cpu", compute_type="int8", local_files_only=True)
        self.sd = None
        self.np = None
        self.sf = None
        self.device_index = None
        self.sample_rate = 16000
        self.min_volume = WAKE_MIN_VOLUME
        self.last_text = ""
        print("Wake word detector ready.")

    def _ensure_audio(self):
        if self.sd is None:
            self.sd = self._load_sounddevice()
            self.np = self._load_numpy()
            self.sf = self._load_soundfile()
            self.device_index = self._find_best_mic()
            self.sample_rate = self._get_device_samplerate(self.device_index)

    def _load_sounddevice(self):
        try:
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
        except ValueError:
            import sounddevice as sd
            return sd

    def _load_numpy(self):
        import numpy as np
        return np

    def _load_soundfile(self):
        import soundfile as sf
        return sf

    def _find_best_mic(self):
        try:
            old_handler = signal.signal(signal.SIGALRM, _raise_timeout)
            try:
                signal.alarm(5)
                devices = self.sd.query_devices()
                signal.alarm(0)
            finally:
                signal.signal(signal.SIGALRM, old_handler)
        except ValueError:
            devices = self.sd.query_devices()
            input_devices = [
                (i, d) for i, d in enumerate(devices)
                if d["max_input_channels"] > 0 and "monitor" not in d["name"].lower()
            ]

            preferred = MIC_DEVICE_NAME.strip().lower()
            if preferred:
                for i, d in input_devices:
                    if d["name"].lower() == preferred:
                        print(f"[MIC] Wake word using configured device: {d['name']}")
                        return i
                if preferred not in ["default", "pulse"]:
                    for i, d in input_devices:
                        if preferred in d["name"].lower():
                            print(f"[MIC] Wake word using configured device: {d['name']}")
                            return i

            default = self.sd.default.device[0]
            if isinstance(default, int) and default >= 0:
                default_name = self.sd.query_devices(default)["name"]
                if "monitor" not in default_name.lower():
                    print(f"[MIC] Wake word using system default: {default_name}")
                    return default

            for i, d in input_devices:
                name = d["name"].lower()
                if any(x in name for x in ["pulse", "pipewire", "default"]):
                    print(f"[MIC] Wake word using audio server device: {d['name']}")
                    return i

            for i, d in input_devices:
                name = d["name"].lower()
                if any(x in name for x in ["usb", "webcam", "headset", "micro", "built"]):
                        return i
            if input_devices:
                return input_devices[0][0]
            return None
        except:
            signal.alarm(0)
            return None
        finally:
            signal.signal(signal.SIGALRM, old_handler)

    def _get_device_samplerate(self, device_index):
        try:
            info = self.sd.query_devices(device_index, 'input')
            return int(info['default_samplerate'])
        except Exception:
            return 16000

    def _is_wake_word(self, text: str) -> bool:
        text = (text or "").lower().strip()
        if not text:
            return False
        # Do not self-trigger on "I am Jarvis"
        if re.search(r"\bi\s*(?:am|'m)\s+jarvis\b", text):
            return False
            
        variants = {
            self.keyword,
            "jarvis",
            "jarbi",
            "jarby",
            "jarvy",
            "jarves",
            "javis",
            "javi",
            "jarvice",
            "jarvish",
            "jervis",
            "charvis",
            "travis",
            "garvis",
            "arvis",
            "jar",
        }
        
        # 1. Match words starting with or equal to any variant
        words = re.findall(r"[a-z]+", text)
        for w in words:
            if w in variants or w.startswith(("jarv", "jarb", "jerv", "jav")):
                return True
                
        # 2. General substring fallback
        if any(v in text for v in variants):
            return True
            
        return False

    def extract_command(self, text: str) -> str:
        text = (text or "").lower().strip()
        if not text:
            return ""
        pattern = r"\b(?:jarvis|jarbi|jarby|jarvy|jarves|javis|javi|jarvice|jarvish|jervis|jar)\b"
        match = re.search(pattern, text)
        if not match:
            return ""
        command = text[match.end():].strip(" ,.:;")
        command = re.sub(r"^(?:wake\s+up|listen|please|can you|could you|and|then|to)\b", "", command).strip()
        command = re.sub(r"^(?:wake\s+up|listen|please|and|then|to)\b", "", command).strip()
        return command

    # Known Whisper hallucination phrases that fire on silence/ambient noise
    HALLUCINATIONS = {
        "thank you", "thank you.", "thanks.", "thank you for watching",
        "thank you for watching.", "thank you very much",
        "thank you very much.", "thank you very much for watching",
        "thank you very much for your support", "thank you so much",
        "thanks for watching", "thanks for watching.",
        "i don't know what to do", "i don't know what to say",
        "i don't know", "i'm here for dinner",
        "i'll leave you for a moment", "yes, yes", "yes, yes.",
        "hello", "hello.", "bye", "bye.", "goodbye", "goodbye.",
        "do you think they are now", "you have to get in there",
        "i don't know what to do.", "what are you doing",
        "what are you doing?", "so,", "so.", "i'm going to go.",
        "i'm not sure.", "subtitles by the amara.org community",
        "you", "the", "i", "a", "it", "is", "he", "she",
        "hmm", "hmm.", "mm.", "uh.", "oh.", "ah.",
    }

    def _is_hallucination(self, text: str) -> bool:
        """Reject known Whisper phantom transcriptions."""
        text = (text or "").lower().strip().rstrip(".")
        if not text:
            return True
        # Exact match against known hallucinations
        if text in self.HALLUCINATIONS or (text + ".") in self.HALLUCINATIONS:
            return True
        # Repetitive patterns like "thank you. thank you. thank you."
        words = text.split()
        if len(words) >= 4 and len(set(words)) <= 2:
            return True
        # ExecStart=/home/talha/Desktop/jartvis/start.sh --mode wake is likely noise
        if len(words) <= 2 and not any(v in text for v in ["jarv", "jarb", "jerv", "jav"]):
            return True
        return False

    def listen_for_wake_word(self, chunk_duration: float = 2.5):
        try:
            self._ensure_audio()
            audio = self.sd.rec(
                int(chunk_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                device=self.device_index
            )
            self.sd.wait()
            audio = audio.flatten()

            volume = float(self.np.abs(audio).mean())
            if volume < self.min_volume:
                return False

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                fname = f.name
            self.sf.write(fname, audio, self.sample_rate)

            segments, _ = self.model.transcribe(
                fname,
                language=None,
                vad_filter=True,
                vad_parameters=dict(threshold=0.1, min_silence_duration_ms=500),
                no_speech_threshold=0.6,
                temperature=0.0,
            )
            text = " ".join([s.text.strip() for s in segments]).lower().strip()
            self.last_text = text

            # Filter hallucinations before anything else
            if self._is_hallucination(text):
                return False

            if text:
                print(f"[WAKE] Heard: '{text}'")

            if self._is_wake_word(text):
                print("[WAKE] Wake word detected!")
                command = self.extract_command(text)
                return command or True
            return False

        except Exception as e:
            print(f"[WAKE] Error: {e}")
            return False
