import asyncio

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.local.audio import LocalAudioTransport
from pipecat.vad.silero import SileroVADAnalyzer

# Import local services instead of cloud services
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.services.ollama import OllamaLLMService
from pipecat.services.piper import PiperTTSService

async def main():
    # 1. Voice Activity Detection (Runs locally)
    vad = SileroVADAnalyzer()
    
    # 2. Local Audio Transport (Your mic and speakers)
    transport = LocalAudioTransport(
        LocalAudioTransport.Params(
            vad_analyzer=vad,
        )
    )

    # 3. Initialize Free/Local AI Services
    # Whisper STT: Automatically downloads a small, fast model on first run
    stt = WhisperSTTService(model="tiny", device="cpu") 
    
    # Ollama LLM: Connects to your local Ollama instance
    llm = OllamaLLMService(model="llama3.2")
    
    # Piper TTS: Automatically downloads a fast, local voice model
    # "en_US-lessac-medium" is a standard free English voice
    tts = PiperTTSService(voice="en_US-lessac-medium")

    # 4. Orchestrate the Pipeline
    pipeline = Pipeline([
        transport.input(), 
        stt,               
        llm,               
        tts,               
        transport.output() 
    ])

    # 5. Run it
    task = PipelineTask(pipeline)
    runner = PipelineRunner()
    
    print("🤖 Downloading models and initializing (this may take a minute on the first run)...")
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())