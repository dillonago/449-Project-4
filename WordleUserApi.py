from cmath import e
import collections
import dataclasses
import textwrap
import sqlite3
import databases
import toml
import random

from quart import Quart, g, request, abort
# from quart_auth import basic_auth_required

from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)


@dataclasses.dataclass
class user:
    username: str
    userpassword: str


@dataclasses.dataclass
class guess:
    game_id: int
    guess_word: str


async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["URL"])
        await db.connect()
    return db


@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()


@app.route("/")
def index():
    return textwrap.dedent(
        """
        <h1>Welcome to the Wordle</h1>

        """
    )

# Start of User API
@app.route("/user/registration", methods=["POST"])
@validate_request(user)
async def register_user(data):
    db = await _get_db()
    user = dataclasses.asdict(data)
    try:
        id = await db.execute(
            """
            INSERT INTO User(username, password)
            VALUES(:username, :userpassword)
            """,
            user,
        )
    except sqlite3.IntegrityError as e:
        abort(409, e)

    user["user_id"] = id
    return user, 201, {"Location": f"/user/registeration/{id}"}


@app.errorhandler(RequestSchemaValidationError)
def bad_request(e):
    return {"error": str(e.validation_error)}, 400


@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409


# user authentication from db
async def authenticate_user(username, password):
    db = await _get_db()
    user = await db.fetch_one("SELECT * FROM User WHERE username =:username AND password =:password", values={"username": username, "password": password})

    return user

# authentication API
@app.route("/auth")
async def authentication():
    if not request.authorization:
        return {"error": "Could not verify user"}, 401, {'WWW-Authenticate': 'Basic realm="MyApp"'}
    else:
        auth = request.authorization
        user = await authenticate_user(auth.username, auth.password)
        if user:
            return {"authenticated": "true"}, 200
        else:
            abort(401)


@app.errorhandler(401)
def not_found(e):
    return {"error": "Unauthorized"}, 401

# End of User API


# check if user_id present in db
async def validate_username(username):
    db = await _get_db()
    user_id = await db.fetch_one("SELECT * FROM User WHERE username =:username", values={"username": username})

    if user_id:
        return user_id
    else:
        abort(404, "User does not exist")


@app.errorhandler(404)
def not_found(e):
    return {"error": str(e)}, 404

@app.errorhandler(417)
def not_found(e):
    return {"error": str(e)}, 417
