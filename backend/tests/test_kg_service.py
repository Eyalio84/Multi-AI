"""Tests for the KG service — schema detection, CRUD, batch ops."""
import sqlite3
import tempfile
import os
import pytest
from pathlib import Path


@pytest.fixture
def kg_svc(tmp_path):
    """Create a KGService pointed at a temp directory with a test DB."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    # Patch config before importing
    import config
    config.KGS_DIR = tmp_path

    from services.kg_service import KGService

    svc = KGService(kgs_dir=tmp_path)

    # Create a standard test database
    db_path = tmp_path / "test-kg.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE nodes (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL DEFAULT 'entity',
            properties TEXT DEFAULT '{}', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE edges (
            id TEXT PRIMARY KEY, source TEXT NOT NULL, target TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'relates_to', properties TEXT DEFAULT '{}',
            weight REAL DEFAULT 1.0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO nodes (id, name, type) VALUES ('n1', 'Alpha', 'concept');
        INSERT INTO nodes (id, name, type) VALUES ('n2', 'Beta', 'tool');
        INSERT INTO nodes (id, name, type) VALUES ('n3', 'Gamma', 'concept');
        INSERT INTO edges (id, source, target, type) VALUES ('e1', 'n1', 'n2', 'uses');
        INSERT INTO edges (id, source, target, type) VALUES ('e2', 'n2', 'n3', 'enables');
    """)
    conn.close()

    yield svc
    svc.close_all()


def test_list_databases(kg_svc):
    dbs = kg_svc.list_databases()
    assert len(dbs) == 1
    assert dbs[0]["id"] == "test-kg"


def test_detect_profile(kg_svc):
    p = kg_svc._detect_profile("test-kg")
    assert p["profile_name"] == "standard"
    assert p["node_table"] == "nodes"


def test_get_stats(kg_svc):
    stats = kg_svc.get_database_stats("test-kg")
    assert stats["node_count"] == 3
    assert stats["edge_count"] == 2


def test_get_nodes(kg_svc):
    result = kg_svc.get_nodes("test-kg")
    assert result["total"] == 3
    assert len(result["nodes"]) == 3


def test_get_nodes_filter(kg_svc):
    result = kg_svc.get_nodes("test-kg", node_type="concept")
    assert result["total"] == 2


def test_get_node(kg_svc):
    node = kg_svc.get_node("test-kg", "n1")
    assert node["name"] == "Alpha"
    assert node["type"] == "concept"


def test_get_neighbors(kg_svc):
    sg = kg_svc.get_neighbors("test-kg", "n2", depth=1)
    assert len(sg["nodes"]) >= 2
    assert len(sg["edges"]) >= 1


def test_create_node(kg_svc):
    node = kg_svc.create_node("test-kg", "Delta", "pattern", {"x": 1})
    assert node["name"] == "Delta"
    assert node["type"] == "pattern"
    assert kg_svc.get_database_stats("test-kg")["node_count"] == 4


def test_update_node(kg_svc):
    result = kg_svc.update_node("test-kg", "n1", name="Alpha-Updated")
    assert result["name"] == "Alpha-Updated"


def test_delete_node(kg_svc):
    assert kg_svc.delete_node("test-kg", "n3")
    assert kg_svc.get_node("test-kg", "n3") is None


def test_create_edge(kg_svc):
    edge = kg_svc.create_edge("test-kg", "n1", "n3", "linked_to")
    assert edge["type"] == "linked_to"


def test_delete_edge(kg_svc):
    assert kg_svc.delete_edge("test-kg", "e1")


def test_create_database(kg_svc, tmp_path):
    result = kg_svc.create_database("new-test-db")
    assert result["id"] == "new-test-db"
    assert (tmp_path / "new-test-db.db").exists()


def test_bulk_create(kg_svc):
    result = kg_svc.bulk_create("test-kg",
        [{"name": "X", "type": "x"}, {"name": "Y", "type": "y"}],
        [{"source": "n1", "target": "n2", "type": "test"}],
    )
    assert result["nodes_created"] == 2
    assert result["edges_created"] == 1


def test_batch_retype(kg_svc):
    count = kg_svc.batch_retype("test-kg", "concept", "idea")
    assert count == 2


def test_get_types(kg_svc):
    types = kg_svc.get_types("test-kg")
    assert len(types["node_types"]) > 0
    assert len(types["edge_types"]) > 0
