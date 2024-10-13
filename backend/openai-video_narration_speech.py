import asyncio
import websockets
import json
import pyaudio
import wave
import base64
import logging
import os

from IPython.display import display, Image, Audio

import cv2  # We're using OpenCV to read video, to install !pip install opencv-python
import base64
import time
from openai import OpenAI
import requests

FILEPATH = "input.mp4"
FRAMERATE = 30
SHORTENSTART = 12
SKIPFRAMESFORSHORTENSTART = 59
SKIPFRAMES = 2
OpenAIClient = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "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"))

# Script Configuration
VOICE = "alloy" # Open AI Text to Speech Voice Options: alloy | echo | shimmer
INSTRUCTIONS = "You are commentator for a big championship kickboxing fight in a packed arena. Lean into the style of Joe Rogan & his mannerisms with extreme excitement & enthusiasm and use a yelling voice. I will provide you with a script. Yell out all words I provide you and only those words. Make the transcript for only 40 seconds."
AUDIO_FILENAME = "./output.wav"

# Configure logging
logging.basicConfig(level=logging.FATAL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

# WebSocket configuration
WS_URL = "wss://api.openai.com/v1/realtime"
MODEL = "gpt-4o-realtime-preview-2024-10-01"
OPENAI_API_KEY = "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"

class RealtimeClient:
    def __init__(self):
        logger.info("Initializing RealtimeClient")
        self.ws = None
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.audio_buffer = b''

    async def connect(self):
        logger.info(f"Connecting to WebSocket: {WS_URL}")
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
        self.ws = await websockets.connect(f"{WS_URL}?model={MODEL}", extra_headers=headers)
        logger.info("Successfully connected to OpenAI Realtime API")

    async def send_event(self, event):
        logger.debug(f"Sending event: {event}")
        await self.ws.send(json.dumps(event))
        logger.debug("Event sent successfully")

    async def receive_events(self):
        logger.info("Starting to receive events")
        async for message in self.ws:
            logger.debug(f"Received raw message: {message}")
            event = json.loads(message)
            await self.handle_event(event)

    async def handle_event(self, event):
        event_type = event.get("type")
        logger.info(f"Handling event of type: {event_type}")

        if event_type == "error":
            logger.error(f"Error event received: {event['error']['message']}")

        elif event_type == "response.text.delta":
            logger.debug(f"Text delta received: {event['delta']}")
            # print(event["delta"], end="", flush=True)

        elif event_type == "response.audio.delta":
            logger.debug(f"Audio delta received, length: {len(event['delta'])}")
            audio_data = base64.b64decode(event["delta"])
            self.audio_buffer += audio_data

        elif event_type == "response.audio.done":
            logger.info("Audio response complete, playing audio")
            # self.play_audio(self.audio_buffer)
            self.write_audio(self.audio_buffer)
            self.audio_buffer = b''
        else:
            logger.info(f"Received other event type: {event_type}")

    def start_audio_stream(self):
        logger.info("Starting audio input stream")
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)
        logger.debug("Audio input stream started successfully")

    def stop_audio_stream(self):
        logger.info("Stopping audio input stream")
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        logger.debug("Audio input stream stopped successfully")

    def record_audio(self, duration):
        logger.info(f"Recording audio for {duration} seconds")
        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = self.stream.read(CHUNK)
            frames.append(data)
            if i % 10 == 0:  # Log every 10th frame
                logger.debug(f"Recorded frame {i}")
        audio_data = b''.join(frames)
        logger.info(f"Audio recording complete, total size: {len(audio_data)} bytes")
        return audio_data

    def play_audio(self, audio_data):
        logger.info(f"Playing audio, size: {len(audio_data)} bytes")
        stream = self.p.open(format=FORMAT,
                             channels=CHANNELS,
                             rate=RATE,
                             output=True)
        stream.write(audio_data)
        stream.stop_stream()
        stream.close()
        logger.debug("Audio playback complete")

    def write_audio(self, audio_data):
        with wave.open(AUDIO_FILENAME, 'wb') as wf:
            wf.setnchannels(1)  # mono
            wf.setsampwidth(2)  # 2 bytes per sample
            wf.setframerate(26000)  # 16kHz sample rate
            wf.writeframes(audio_data)
        
        print("Audio file write complete!")

    async def send_text(self, text):
        logger.info(f"Sending text message: {text}")
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": text
                }]
            }
        }
        await self.send_event(event)
        logger.debug("Text message sent, creating response")
        await self.send_event({"type": "response.create"})

    async def send_audio(self, duration):
        logger.info(f"Preparing to send audio of duration: {duration} seconds")
        self.start_audio_stream()
        audio_data = self.record_audio(duration)
        self.stop_audio_stream()

        base64_audio = base64.b64encode(audio_data).decode('utf-8')
        logger.debug(f"Audio encoded to base64, length: {len(base64_audio)}")
        
        event = {
            "type": "input_audio_buffer.append",
            "audio": base64_audio
        }
        await self.send_event(event)
        logger.debug("Audio buffer appended, committing buffer")
        await self.send_event({"type": "input_audio_buffer.commit"})
        logger.debug("Audio buffer committed, creating response")
        await self.send_event({"type": "response.create"})

    async def run(self, narration):
        logger.info("Starting RealtimeClient run")
        await self.connect()
        
        # Create a task for receiving events
        receive_task = asyncio.create_task(self.receive_events())
        
        logger.info("Sending initial message to start the conversation")
        await self.send_event({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": VOICE,
                "instructions": INSTRUCTIONS
            }
        })

        await self.send_text(narration)

        try:
            while True:
                '''
                # Enter 't' for text, 'a' for audio, or 'q' to quit:
                command = await asyncio.get_event_loop().run_in_executor(None, input, "Enter 't' for text, 'a' for audio, or 'q' to quit: ")
                if command == 't':
                    text = await asyncio.get_event_loop().run_in_executor(None, input, "Enter your message: ")
                    await self.send_text(text)
                elif command == 'a':
                    logger.info("Audio input selected")
                    print("Recording for 5 seconds...")
                    await self.send_audio(5)
                elif command == 'q':
                    logger.info("Quit command received")
                    break
                else:
                    logger.warning(f"Invalid command received: {command}")
                '''

                command = await asyncio.get_event_loop().run_in_executor(None, input, "Enter the message to read out, or just 'q' to quit: /n")
                if command == 'q':
                    logger.info("Quit command received")
                    break
                else:
                    await self.send_text(command)

                # Give some time for the response to be processed
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            logger.info("Ending conversation and closing connection")
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            await self.ws.close()

async def main():

    print("file exists?", os.path.exists(FILEPATH))
    video = cv2.VideoCapture(FILEPATH)

    base64Frames = []
    frameCounter = 0
    frameCountDown = SKIPFRAMES

    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)

        frameCounter += 1
        # print(frameCounter)

        # Skip Frames
        if frameCountDown == 0:
            base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
            # print("frame")

            if frameCounter >= (FRAMERATE * SHORTENSTART):
                frameCountDown = SKIPFRAMES
            else:
                frameCountDown = SKIPFRAMESFORSHORTENSTART

        else:
            frameCountDown -= 1
            # print("skip")

    video.release()
    print(len(base64Frames), "frames read.")

    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                "These are frames of a kick-boxing video. Create a play-by-play voiceover script in the style of a professional boxer. Include the boxer's name and the opponent's name. Only include the narration, do not include any other text. Limit to 225 words",
                *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::50]),
            ],
        },
    ]
    params = {
        "model": "gpt-4o",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 1000,
    }

    result = OpenAIClient.chat.completions.create(**params)
    narration = result.choices[0].message.content
    print(narration)

    logger.info("Starting Text to Speech function")
    client = RealtimeClient()
    try:
        await client.run(narration)
    except Exception as e:
        logger.error(f"An error occurred in main: {e}")
    finally:
        logger.info("Main function completed")

if __name__ == "__main__":
    logger.info("Script started")
    asyncio.run(main())
    logger.info("Script completed")