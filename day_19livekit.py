import spacy
import datetime
import json
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, JobContext, WorkerOptions, cli, function_tool, room_io
from livekit.plugins import silero, noise_cancellation

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: Spacy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

JSON_DIR = Path("conversation_json")
DB_FILE = Path("emergency_data.db")

JSON_DIR.mkdir(exist_ok=True)

load_dotenv()

class SQLiteManager:

    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT UNIQUE,
                    timestamp TEXT,
                    caller_name TEXT,
                    location TEXT,
                    incident_type TEXT,
                    classification TEXT,
                    confidence REAL,
                    priority TEXT,
                    sentiment TEXT,
                    description TEXT,
                    language TEXT,
                    json_file_path TEXT
                )
            """)
            conn.commit()
            conn.close()
            print(f"[SYSTEM] Database initialized at {self.db_path}")
        except Exception as e:
            print(f"[ERROR] Database initialization failed: {e}")

    def insert_incident(self, data: dict, json_path: str):
        print(f"[DB] Attempting to write ticket {data.get('ticket_id')} to database...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = """
                INSERT INTO incidents 
                (ticket_id, timestamp, caller_name, location, incident_type, classification, confidence, priority, sentiment, description, language, json_file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                data['ticket_id'],
                data['timestamp'],
                data['name'],          
                data['location'],
                data['type'],          
                data['classification'],
                data['confidence'],
                data['priority'],
                data['sentiment'],
                data['description'],
                data['language'],
                json_path
            ))
            conn.commit()
            conn.close()
            print(f"[DB] Successfully written ticket {data['ticket_id']}")
            return "Success: Written to SQLite"
        except Exception as e:
            print(f"[DB ERROR] Failed to write ticket: {e}")
            return f"DB Error: {str(e)}"

db_manager = SQLiteManager(DB_FILE)

class IndicAssistant(agents.Agent):
    def __init__(self):

        super().__init__(
            instructions=f"""
            ROLE:
            You are a Senior Emergency Control Officer for the Indian National Emergency Helpline (112). 

            CORE OPERATING PRINCIPLES:
            1. TIME IS LIFE: Be concise.
            2. CALMNESS: Speak slowly if user is panicked.
            3. CLARITY: Short sentences (Max 12 words).
            4. ONE THING AT A TIME.

            STRICT WORKFLOW:

            STEP 1: INTENT ASSESSMENT
            - Ask "What is your emergency?"
            - Call 'detect_call_intent'.

            STEP 2: CRITICAL TRIAGE
            - Collect: Location, Incident Type, Caller Name, Phone Number, Status.
            - Ask one question at a time.

            STEP 3: SUBMISSION (CRITICAL)
            - Once info is gathered, STOP asking.
            - Call 'submit_emergency_report'.
            - YOU MUST PROVIDE THESE EXACT ARGUMENTS:
                1. caller_name (str)
                2. location (str)
                3. incident_type (str)
                4. call_classification (str: "EMERGENCY", "INQUIRY", or "REPORT")
                5. confidence_score (float: 0.0 to 1.0)
                6. priority (str: "HIGH", "MEDIUM", or "LOW")
                7. sentiment (str: "PANICKED", "CALM", or "AGGRESSIVE")
                8. description (str)
            - Call this tool ONLY ONCE.

            STEP 4: DISCONNECT
            - Read Ticket ID.
            - Call 'disconnect_call'.
            """
        )
        self._report_submitted = False
        self.conversation_history = []

    @function_tool()
    async def detect_call_intent(self, context: agents.RunContext, user_statement: str):
        return "Intent analyzed."

    @function_tool()
    async def submit_emergency_report(
        self, 
        context: agents.RunContext, 
        caller_name: str, 
        location: str, 
        incident_type: str, 
        call_classification: str,
        confidence_score: float, 
        priority: str,
        sentiment: str,
        description: str
    ):
        if self._report_submitted:
            return "Report already submitted."

        ticket_id = f"INC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        timestamp = datetime.datetime.now().isoformat()

        print(f"[TOOL] submit_emergency_report called for {ticket_id}")

        db_data = {
            : ticket_id,
            : timestamp,
            : caller_name,
            : location,
            : incident_type,
            : call_classification,
            : confidence_score,
            : priority,
            : sentiment,
            : description,
            : self.current_language
        }

        json_filename = JSON_DIR / f"incident_{ticket_id}.json"
        conversation_data = {
            : db_data,
            : self.conversation_history
        }

        try:
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=4)
            print(f"[FILE] JSON saved to {json_filename}")
        except Exception as e:
            print(f"[ERROR] Failed to save JSON: {e}")

        extracted_metadata = {}
        try:
            with open(json_filename, "r", encoding="utf-8") as f:
                loaded_json = json.load(f)
                extracted_metadata = loaded_json.get("metadata")
                print(f"[FILE] Metadata extracted from JSON successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to read JSON for metadata extraction: {e}")

            extracted_metadata = db_data

        db_result = db_manager.insert_incident(extracted_metadata, str(json_filename))

        self._report_submitted = True

        if "Success" in db_result:
            return f"Report {ticket_id} submitted successfully. Help is on the way to {location}."
        else:
            return f"System error: {db_result}"

    @function_tool()
    async def disconnect_call(self, context: agents.RunContext):
        print("[SYSTEM] Disconnecting call...")
        try:
            await context.room.disconnect()
        except Exception:
            pass
        return "Disconnecting call. Stay safe."

async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt="deepgram/nova-3:multi",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=silero.VAD.load(),
        turn_detection="vad",
    )

    assistant = IndicAssistant()

    @session.on("user_input_transcribed")
    def on_user(evt):
        if evt.is_final:
            assistant.conversation_history.append({
                : "user",
                : evt.transcript,
                : datetime.datetime.now().isoformat()
            })
            print(f"[USER] {evt.transcript}")

    @session.on("conversation_item_added")
    def on_agent(evt):
        if hasattr(evt, 'item'):
            if evt.item.role == 'assistant' and evt.item.text_content:
                assistant.conversation_history.append({
                    : "assistant",
                    : evt.item.text_content,
                    : datetime.datetime.now().isoformat()
                })
                print(f"[AGENT] {evt.item.text_content}")

            if evt.item.type == "function_call":
                print(f"[TOOL CALL] {evt.item.name}")

    await session.start(
        room=ctx.room,
        agent=assistant,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda p: noise_cancellation.BVC()
            ),
        ),
    )

    await ctx.connect()
    await session.say("Emergency Helpline. What is your emergency?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))