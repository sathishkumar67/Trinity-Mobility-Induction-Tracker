import asyncio

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.local.audio import LocalAudioTransport
from pipecat.vad.silero import SileroVADAnalyzer

from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.services.ollama import OllamaLLMService
from pipecat.services.piper import PiperTTSService

async def main():

    vad = SileroVADAnalyzer()

    transport = LocalAudioTransport(
        LocalAudioTransport.Params(
            vad_analyzer=vad,
        )
    )

    stt = WhisperSTTService(model="tiny", device="cpu") 

    llm = OllamaLLMService(model="llama3.2")

    tts = PiperTTSService(voice="en_US-lessac-medium")

    pipeline = Pipeline([
        transport.input(), 
        stt,               
        llm,               
        tts,               
        transport.output() 
    ])

    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    print("🤖 Downloading models and initializing (this may take a minute on the first run)...")
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())