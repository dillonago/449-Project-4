from cmath import e
import dataclasses
import textwrap
import sqlite3
import databases
import toml
import redis
import json
import sys
from quart import Quart, g, request, abort, jsonify
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request, tag

app = Quart(__name__)
QuartSchema(app, tags=[
    {"name": "Root", "description": "Root path."},
    {"name": "Leaderboard", "description": "APIs for leaderboard."}])

leaderboard = redis.Redis()

@dataclasses.dataclass
class game:
    user: str
    result: str
    guesses: int

# route endpoint.
@app.route("/")
@tag(["Root"])
def index():
    """ Returns HTML content. """
    return textwrap.dedent(
        """
        <h1>Welcome to the Wordle</h1>

        """
    )

# status codes
@app.errorhandler(RequestSchemaValidationError)
def bad_request(e):
    return {"error": str(e.validation_error)}, 400

@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409

@app.errorhandler(401)
def not_found(e):
    return {"error": "Unauthorized"}, 401

@app.errorhandler(404)
def not_found(e):
    return {"error": str(e)}, 404

# New Game API
@app.route("/leaderboard", methods=["POST"])
@tag(["Leaderboard"])
@validate_request(game)
async def postgame(data):
    """ Save game result into database. """
    auth=request.authorization
    game = dataclasses.asdict(data)
    user = game["user"]

    #calculate score
    if game["result"] == "Lost":
        score = 0
    else:
        score = 7 - game["guesses"]

    #retrieve current user's stats
    try:
        games_played = leaderboard.hget("games_played", user)
        games_played = int(games_played) + 1
        total_score = leaderboard.hget("total_scores", user)
        total_score = int(total_score) + score
    except:
        games_played = 1
        total_score = score

    #increment games_played and total_score in hash at user key
    leaderboard.hset("games_played", user, games_played)
    leaderboard.hset("total_scores", user, total_score)
    
    #process input and calculate average score
    avg_score = total_score/games_played
    
    #update avg_score in sorted set "avg_scores" at user key
    leaderboard.zadd("avg_scores", {user: avg_score})

    app.logger.info("Games played for " + str(game["user"]) + ": " + str(leaderboard.hget("games_played", user)))
    app.logger.info("Total score for " + str(game["user"]) + ": " + str(leaderboard.hget("total_scores", user)))
    app.logger.info("Average score for " + str(game["user"]) + ": " + str(leaderboard.zscore("avg_scores", user)))
    return game, 200


# status code
@app.errorhandler(417)
def not_found(e):
    return {"error": str(e)}, 417

# leaderboard top 10 endpoint.
@app.route("/leaderboard/top10", methods=["GET"])
@tag(["Leaderboard"])
async def get_scores():
    """ Return top 10 users by score. """
    # returns bytes sorted by low to high score.
    scoreboard = leaderboard.zrange("avg_scores", 0, -1)
    # convert bytes to string.
    convert = [i.decode() for i in scoreboard]
    # sort top 10.
    convert.reverse()
    # return top 10.
    return convert[:10], 200
