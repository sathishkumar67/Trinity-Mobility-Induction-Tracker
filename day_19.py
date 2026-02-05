import asyncio
import os
from pipecat.frames.frames import TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.local_audio import LocalAudioTransport  
from pipecat.aggregators.context import ConversationContextAggregator
from pipecat.vad.silero import SileroVADAnalyzer
from pipecat.tasks import PipelineTask, PipelineParams
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.stt import OpenAIWhisperService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.pipeline import Pipeline




# Services (your hosted)
vad = SileroVADAnalyzer()
llm = OpenAILLMService(
    api_key="not-used",
    base_url="http://192.168.1.120:11434/v1",  # Your hosted LLM endpoint
    model="llama3.1:8b"
)

stt = OpenAIWhisperService(
    api_key="your-api-key",
    base_url="http://your-stt-host:port/v1"
)

tts = OpenAITTSService(
    api_key="your-api-key",
    base_url="http://your-tts-host:port/v1"
)


pipeline = Pipeline([transport.input(), stt, user_context, llm, tts, transport.output()])
task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))





user_context = ConversationContextAggregator.user()
assistant_context = ConversationContextAggregator.assistant()

# Local console transport
transport = LocalAudioTransport(sample_rate=16000, channels=1)

# Pipeline
pipeline = Pipeline([
    transport.input(),
    vad,
    stt,
    user_context,
    llm,
    tts,
    transport.output(),
    assistant_context
])

async def main():
    task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))
    await task.queue_frames([TTSSpeakFrame("Hello! Speak now...")])  # Initial greeting
    runner = PipelineRunner()
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
