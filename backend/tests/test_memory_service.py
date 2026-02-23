"""Tests for memory_service."""
import os
import sys
import tempfile

# Ensure backend is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_memory_service():
    """Test conversation CRUD and memory extraction."""
    # Use temp DB
    import services.memory_service as ms
    original_path = ms.MEMORY_DB_PATH
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        ms.MEMORY_DB_PATH = f.name

    try:
        svc = ms.MemoryService()

        # Create conversation
        cid = svc.create_conversation("chat", "web")
        assert cid, "Should return conversation ID"

        # Log messages
        mid1 = svc.log_message(cid, "user", "I decided to use FastAPI for the backend")
        mid2 = svc.log_message(cid, "assistant", "Great choice! FastAPI is fast and modern.", "gemini", "gemini-2.5-flash")
        assert mid1 and mid2

        # List conversations
        convs = svc.list_conversations()
        assert len(convs) == 1
        assert convs[0]["message_count"] == 2

        # Get messages
        msgs = svc.get_conversation_messages(cid)
        assert len(msgs) == 2
        assert msgs[0]["author"] == "user"

        # Extract memories (regex mode)
        stored = svc.extract_and_store(cid, "I decided to use FastAPI for the backend", "Great choice!")
        assert len(stored) > 0, f"Should extract at least one memory, got {stored}"

        # Check types
        types = {m["type"] for m in stored}
        assert "decision" in types or "entity" in types, f"Expected decision or entity in {types}"

        # Stats
        stats = svc.get_stats()
        assert stats["conversations"] == 1
        assert stats["memory_nodes"] > 0

        # Get full conversation
        full = svc.get_conversation(cid)
        assert full is not None
        assert len(full["messages"]) == 2

        # Delete
        assert svc.delete_conversation(cid)
        assert svc.list_conversations() == []

        print("All memory_service tests passed!")

    finally:
        ms.MEMORY_DB_PATH = original_path
        try:
            os.unlink(f.name)
        except OSError:
            pass


if __name__ == "__main__":
    test_memory_service()
