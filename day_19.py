import asyncio
import os
from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.your_hosted import YourSTTService, YourLLMService, YourTTSService  # Your custom services
from pipecat.transports.services.daily import DailyTransport
from pipecat.aggregators.context import ConversationContextAggregator
from pipecat.vad.silero import SileroVADAnalyzer

# Initialize services (use your hosted configs)
transport = DailyTransport.from_room_url(os.getenv("DAILY_ROOM_URL"))
vad = SileroVADAnalyzer()
stt = YourSTTService(api_key="your-key", base_url="http://your-stt:port/v1")
user_context = ConversationContextAggregator.user()
llm = YourLLMService(api_key="your-key", base_url="http://your-llm:port/v1", model="your-llm-model")
tts = YourTTSService(api_key="your-key", base_url="http://your-tts:port/v1")
assistant_context = ConversationContextAggregator.assistant()

# Build pipeline
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

# Run
async def main():
    task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))
    # Greeting
    await task.queue_frames([TTSSpeakFrame("Hello! How can I help?")])
    runner = PipelineRunner()
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
