"""VOX Game Functions — Games Studio voice control.

Existing (in vox_registry.py): start_feature_interview (workspace category)
New here: list_games, create_game, get_game_status, game_save_version,
game_list_versions, get_interview_questions
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="list_games",
    category="games",
    description="List all game projects in the Games Studio",
    parameters={"type": "object", "properties": {}},
)
async def list_games(args: dict) -> dict:
    from services.game_service import GameService
    svc = GameService()
    games = svc.list_projects()
    return {"success": True, "games": games, "count": len(games)}


@vox_registry.register(
    name="create_game",
    category="games",
    description="Create a new game project in the Games Studio",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Game project name"},
            "description": {"type": "string", "description": "Game concept description"},
        },
        "required": ["name"],
    },
)
async def create_game(args: dict) -> dict:
    from services.game_service import GameService
    svc = GameService()
    game = svc.create_project(args["name"], args.get("description", ""))
    return {"success": True, "game": game}


@vox_registry.register(
    name="get_game_status",
    category="games",
    description="Get status and details of a specific game project",
    parameters={
        "type": "object",
        "properties": {
            "game_id": {"type": "string", "description": "Game project ID"},
        },
        "required": ["game_id"],
    },
)
async def get_game_status(args: dict) -> dict:
    from services.game_service import GameService
    svc = GameService()
    game = svc.get_project(args["game_id"])
    if not game:
        return {"success": False, "error": "Game not found"}
    return {"success": True, "game": game}


@vox_registry.register(
    name="game_save_version",
    category="games",
    description="Save a version snapshot of a game project",
    parameters={
        "type": "object",
        "properties": {
            "game_id": {"type": "string", "description": "Game project ID"},
            "message": {"type": "string", "description": "Version message"},
        },
        "required": ["game_id"],
    },
)
async def game_save_version(args: dict) -> dict:
    from services.game_service import GameService
    svc = GameService()
    result = svc.save_version(args["game_id"], args.get("message", "Voice save"))
    if not result:
        return {"success": False, "error": "Game not found"}
    return {"success": True, "version": result}


@vox_registry.register(
    name="game_list_versions",
    category="games",
    description="List all saved versions of a game project",
    parameters={
        "type": "object",
        "properties": {
            "game_id": {"type": "string", "description": "Game project ID"},
        },
        "required": ["game_id"],
    },
)
async def game_list_versions(args: dict) -> dict:
    from services.game_service import GameService
    svc = GameService()
    versions = svc.list_versions(args["game_id"])
    return {"success": True, "versions": versions, "count": len(versions)}


@vox_registry.register(
    name="get_interview_questions",
    category="games",
    description="Get the 18 interview questions for creating a game design document",
    parameters={"type": "object", "properties": {}},
)
async def get_interview_questions(args: dict) -> dict:
    from services.game_service import GameService
    svc = GameService()
    questions = svc.get_interview_questions()
    return {"success": True, "questions": questions, "count": len(questions)}
