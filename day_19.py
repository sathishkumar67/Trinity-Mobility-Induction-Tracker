from pipecat.services.openai import OpenAILLMService, OpenAITTSService, OpenAISTTService
import websockets

# 1. Custom LLM (e.g., hosted via Ollama or vLLM)
llm = OpenAILLMService(
    api_key="cant-be-empty",       # Placeholder if your local server doesn't check it
    base_url="http://localhost:11434/v1", # Your hosted LLM URL
    model="llama3-70b"             # Your specific model name
)

# 2. Custom STT (e.g., hosted Whisper)
stt = OpenAISTTService(
    api_key="cant-be-empty",
    base_url="http://localhost:8000/v1",
    model="whisper-1"
)

# 3. Custom TTS (e.g., hosted generic TTS with OpenAI wrapper)
tts = OpenAITTSService(
    api_key="cant-be-empty",
    base_url="http://localhost:5000/v1",
    model="tts-1",
    voice="alloy"
)

import aiohttp
from typing import AsyncGenerator
from pipecat.services.ai_service import AIService
from pipecat.frames.frames import Frame, LLMMessagesFrame, LLMTextFrame, LLMFullResponseEndFrame

class MyHostedLLMService(AIService):
    def __init__(self, api_url, **kwargs):
        super().__init__(**kwargs)
        self.api_url = api_url

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, LLMMessagesFrame):
            # 1. Extract chat history from the frame
            messages = frame.messages 
            
            # 2. Call your hosted API (streaming example)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json={"messages": messages, "stream": True}) as response:
                    async for line in response.content:
                        # Parse your API's specific streaming format
                        text_chunk = parse_my_custom_chunk(line) 
                        if text_chunk:
                            # 3. Yield text frames to the pipeline
                            await self.push_frame(LLMTextFrame(text_chunk))
            
            # 4. Signal end of response
            await self.push_frame(LLMFullResponseEndFrame())
            
            
from pipecat.services.stt_service import STTService
from pipecat.frames.frames import AudioRawFrame, TranscriptionFrame, InterimTranscriptionFrame

class MyHostedSTTService(STTService):
    def __init__(self, ws_url, **kwargs):
        super().__init__(**kwargs)
        self.ws_url = ws_url

    async def run_stt(self, audio_stream: AsyncGenerator[AudioRawFrame, None]):
        # Connect to your hosted WebSocket STT
        async with websockets.connect(self.ws_url) as websocket:
            async for frame in audio_stream:
                # 1. Send audio bytes to your API
                await websocket.send(frame.audio)
                
                # 2. Receive transcription (this logic depends on if your API is full-duplex)
                # You might need a separate task to listen for incoming messages
                result = await websocket.recv()
                text = parse_my_stt_result(result)
                
                if text["is_final"]:
                    await self.push_frame(TranscriptionFrame(text["content"], "", ""))
                else:
                    await self.push_frame(InterimTranscriptionFrame(text["content"], "", ""))
                    
                    
                    
from pipecat.services.tts_service import TTSService
from pipecat.frames.frames import TTSAudioRawFrame, TTSStartedFrame, TTSStoppedFrame

class MyHostedTTSService(TTSService):
    def __init__(self, api_url, **kwargs):
        super().__init__(**kwargs)
        self.api_url = api_url

    async def run_tts(self, text: str):
        # 1. Signal start
        await self.push_frame(TTSStartedFrame())

        # 2. Call your API
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json={"text": text}) as response:
                # 3. Stream audio bytes back to the pipeline
                async for chunk in response.content.iter_chunked(1024):
                     # Ensure sample rate matches your pipeline config (usually 16000 or 24000)
                    await self.push_frame(TTSAudioRawFrame(audio=chunk, sample_rate=24000, num_channels=1))

        # 4. Signal stop
        await self.push_frame(TTSStoppedFrame())