import sys
import os
import asyncio
from sqlmodel import Session, select

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.engine import engine
from core.db.models import Chapter, StoryRelationship, Novel, NovelVersion, AnalysisRun
from backend.narrative_engine.core.store import StateStore
from backend.narrative_engine.core.engine import NarrativeEvolutionEngine
from backend.narrative_engine.plugins.relationship import RelationshipPlugin
from core.summarizer.llm_client import ClientFactory, LLMClient
from core.config import settings

class EngineLLMAdapter:
    """Adapts core.summarizer.LLMClient to the interface expected by NarrativeEngine"""
    def __init__(self, client: LLMClient):
        self.client = client
        
    def generate(self, prompt: str) -> str:
        # Synchronous wrapper for async client if needed, or direct call
        # The LLMClient has chat_completion (sync) and chat_completion_async
        # Our Engine currently expects .generate(prompt) -> str
        
        messages = [{"role": "user", "content": prompt}]
        return self.client.chat_completion(messages)

async def analyze_relationship_real(novel_name: str, file_hash: str, source_name: str, target_name: str, provider: str = "openrouter"):
    """
    Runs the NarrativeEvolutionEngine with REAL LLM calls.
    """
    # 1. Setup Infrastructure
    store = StateStore() 
    engine_core = NarrativeEvolutionEngine(store)
    plugin = RelationshipPlugin()
    engine_core.register_plugin(plugin)
    
    # 2. Setup LLM Client
    print(f"Initializing LLM Client ({provider})...")
    
    if provider == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            print("Error: OPENROUTER_API_KEY not found in settings/.env")
            return
        client = ClientFactory.create_client(
            "openrouter", 
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.OPENROUTER_MODEL
        )
    elif provider == "local":
        client = ClientFactory.create_client(
            "local",
            base_url=settings.LOCAL_LLM_BASE_URL,
            model=settings.LOCAL_LLM_MODEL
        )
    else:
        print(f"Unknown provider: {provider}")
        return

    llm_adapter = EngineLLMAdapter(client)
    
    # 3. Load Data from DB
    pair_id = "_".join(sorted([source_name, target_name]))
    print(f"Analyzing relationship for {pair_id} in {novel_name} ({file_hash})...")
    
    with Session(engine) as session:
        # Get novel, version, run
        novel = session.exec(select(Novel).where(Novel.name == novel_name)).first()
        if not novel:
            print(f"Novel '{novel_name}' not found. Trying first available...")
            novel = session.exec(select(Novel)).first()
            if not novel:
                print("No novel found in DB.")
                return
        
        print(f"Using Novel: {novel.name} (ID: {novel.id})")
            
        version = session.exec(select(NovelVersion).where(NovelVersion.novel_id == novel.id, NovelVersion.hash == file_hash)).first()
        if not version:
            print(f"Version '{file_hash}' not found. Falling back to first version.")
            version = session.exec(select(NovelVersion).where(NovelVersion.novel_id == novel.id)).first()
            if not version: return
            
        # Get latest run
        run = session.exec(select(AnalysisRun).where(AnalysisRun.version_id == version.id).order_by(AnalysisRun.timestamp.desc())).first()
        if not run:
            print("No run found.")
            return
            
        # Get chapters
        chapters = session.exec(select(Chapter).where(Chapter.run_id == run.id).order_by(Chapter.chapter_index)).all()
        
        print(f"Found {len(chapters)} chapters. Starting analysis loop...")
        
        # 4. Analysis Loop
        for chapter in chapters:
            # Construct 'new_events' from DB relationships
            # We need to find interactions in THIS chapter
            rels = session.exec(select(StoryRelationship).where(
                StoryRelationship.chapter_id == chapter.id,
                ((StoryRelationship.source == source_name) & (StoryRelationship.target == target_name)) |
                ((StoryRelationship.source == target_name) & (StoryRelationship.target == source_name))
            )).all()
            
            # Convert DB models to dicts for Engine
            events_data = []
            for r in rels:
                # Determine direction
                direction = "forward" if r.source == source_name else "backward"
                events_data.append({
                    "chapter_id": str(chapter.chapter_index),
                    "relation": r.relation,
                    "description": r.description or "",
                    "direction": direction
                })
            
            # Call Engine
            # Note: evolve_state handles the "check_trigger" logic internally.
            # If events_data is empty, it will likely skip LLM (Fast Path).
            
            print(f"Processing Ch {chapter.chapter_index} ({len(events_data)} interactions)... ", end="", flush=True)
            
            try:
                new_state = engine_core.evolve_state(
                    novel_hash=version.hash, # Use version hash as the novel_hash key
                    plugin_type="relationship",
                    entity_id=pair_id,
                    target_chapter_index=chapter.chapter_index,
                    new_events=events_data,
                    llm_client=llm_adapter
                )
                
                # Visual feedback
                if new_state.chapter_index == chapter.chapter_index and len(events_data) > 0:
                    print(f"✅ UPDATED -> Trust: {new_state.trust_level}, Stage: {new_state.current_stage}")
                else:
                    print("⏭️ Skipped/Cloned")
                    
            except Exception as e:
                print(f"❌ Error: {e}")

    print("\nAnalysis Complete! Check frontend for results.")

if __name__ == "__main__":
    # Default args
    NOVEL_NAME = "故障烏託邦"
    FILE_HASH = "8771c958"
    SOURCE = "孙杰克"
    TARGET = "宋6PUS"
    PROVIDER = "openrouter" # or "local"
    
    if len(sys.argv) > 4:
        NOVEL_NAME = sys.argv[1]
        FILE_HASH = sys.argv[2]
        SOURCE = sys.argv[3]
        TARGET = sys.argv[4]
    
    if len(sys.argv) > 5:
        PROVIDER = sys.argv[5]
        
    asyncio.run(analyze_relationship_real(NOVEL_NAME, FILE_HASH, SOURCE, TARGET, PROVIDER))
