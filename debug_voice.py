import os, sys

# Ensure we are using the same virtual environment
venv_path = os.path.join(os.path.dirname(__file__), 'jarvis-env')
activate_this = os.path.join(venv_path, 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

from stt import SpeechToText
from brain import JarvisBrain
from tts import TextToSpeech

def test_microphone():
    print('--- Generating synthetic silent audio (1 sec) ---')
    import numpy as np
    stt = SpeechToText()
    # Whisper expects int16 PCM; generate zeros
    sample_rate = stt.sample_rate
    duration_sec = 1
    audio = np.zeros(int(sample_rate * duration_sec), dtype=np.int16)
    print('Synthetic audio length (samples):', len(audio))
    return audio

def test_stt(audio):
    print('--- Testing STT transcription ---')
    stt = SpeechToText()
    # Directly transcribe the captured audio
    try:
        text = stt.transcribe(audio)
        print('Transcribed text:', text)
    except Exception as e:
        print('STT error:', e)
        text = None
    return text

def test_brain(command):
    print('--- Testing Brain processing ---')
    brain = JarvisBrain()
    result = brain.process(command)
    print('Brain result JSON:', result)
    return result

def test_tts(message):
    print('--- Testing TTS output ---')
    tts = TextToSpeech()
    try:
        tts.speak(message)
        print('TTS playback attempted')
    except Exception as e:
        print('TTS error:', e)

if __name__ == '__main__':
    # 1. Microphone capture
    audio = test_microphone()
    # 2. STT transcription (if audio captured)
    if audio is not None:
        text = test_stt(audio)
    else:
        text = None
    # 3. Brain processing (fallback to a known command if STT failed)
    cmd = text if text else 'what time is it?'
    brain_result = test_brain(cmd)
    # 4. TTS playback of the brain's speak field
    if isinstance(brain_result, dict) and brain_result.get('speak'):
        test_tts(brain_result['speak'])
    else:
        print('No speak field in brain result; skipping TTS')
