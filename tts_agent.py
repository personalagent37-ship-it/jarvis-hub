#!/usr/bin/env python3
import argparse

from tts import TextToSpeech


class TtsOnlyJarvis:
    def __init__(self):
        self.tts = TextToSpeech()

    def speak(self, text: str):
        self.tts.speak(text)

    def run(self):
        print("\nJARVIS TTS-only mode")
        print("Type text and press Enter. Type quit to exit.\n")
        while True:
            try:
                text = input("Say: ").strip()
            except KeyboardInterrupt:
                print("\nGoodbye.")
                break

            if text.lower() in {"quit", "exit", "bye"}:
                self.speak("Goodbye Talha.")
                break
            self.speak(text)


def main():
    parser = argparse.ArgumentParser(description="JARVIS TTS-only speaker agent")
    parser.add_argument("text", nargs="*", help="Text for JARVIS to speak once")
    args = parser.parse_args()

    agent = TtsOnlyJarvis()
    if args.text:
        agent.speak(" ".join(args.text))
    else:
        agent.run()


if __name__ == "__main__":
    main()
