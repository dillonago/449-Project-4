
from cmath import e
import collections
import dataclasses
import textwrap
import sqlite3
import databases
import toml
import random
import uuid
import itertools


from quart import Quart, g, request, abort
# from quart_auth import basic_auth_required

from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)

@dataclasses.dataclass
class guess:
    game_id: str
    guess_word: str

cycleObj = itertools.cycle(["URL1", "URL2", "URL3"])


async def _get_writedb():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["URL1"])
        await db.connect()
    return db

async def _get_db(url):
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"][url])
        await db.connect()
    return db

@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()
        g._sqlite_db = None


@app.route("/")
def index():
    return textwrap.dedent(
        """
        <h1>Welcome to the Wordle</h1>

        """
    )


@app.errorhandler(RequestSchemaValidationError)
def bad_request(e):
    return {"error": str(e.validation_error)}, 400


@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409


@app.errorhandler(401)
def not_found(e):
    return {"error": "Unauthorized"}, 401

# End of User API



# Start of Game API

@app.errorhandler(404)
def not_found(e):
    return {"error": str(e)}, 404

# Check if game_id present in db 
async def validate_game_id(game_id, url):
    db = await _get_db(url)
    app.logger.info("SELECT game_id FROM Game WHERE game_id = "+str(game_id))
    query = "SELECT game_id FROM Game WHERE game_id = :game_id"
    game_id = await db.fetch_one(query=query, values={"game_id": game_id})
    db = await close_connection(None)
    if game_id is None:
        abort(404, "game  does not exist")
    else:
         return game_id

# function to update In_progress table
async def update_inprogress(game_id):
    db = await _get_writedb()
    auth=request.authorization
    inprogressEntry = await db.execute("INSERT INTO In_Progress(game_id, username) VALUES (:game_id, :username)", values={"game_id": game_id, "username": auth.username})
    db = await close_connection(None)
    if inprogressEntry:
        return inprogressEntry
    else:
        abort(417, "Failed to create entry in In_Progress table")


# New Game API
@app.route("/newgame", methods=["POST"])
async def newgame():
    url = next(cycleObj)
    db = await _get_db(url)
    auth=request.authorization
    app.logger.info("SELECT correct_word FROM Correct_Words")
    secret_word = await db.fetch_all("SELECT correct_word FROM Correct_Words")
    db = await close_connection(None)
    secret_word = random.choice(secret_word)
    gameid = str(uuid.uuid4())
    db = await _get_writedb()
    game_id = await db.execute("INSERT INTO Game(game_id, username, secretword) VALUES (:game_id, :username, :secretword)", values={"game_id": gameid, "username": auth.username, "secretword": secret_word[0]})
    if game_id:
        inprogressEntry = await update_inprogress(gameid)
        if inprogressEntry:
            return {"success": f"Your new game id is {gameid}"}, 201
        else:
            abort(417, "Failed to create entry in In_Progress table")

    else:
         abort(417, "New game creation failed")


@app.errorhandler(417)
def not_found(e):
    return {"error": str(e)}, 417


#Guess API
@app.route("/guess", methods=["POST"])
@validate_request(guess)
async def guess(data):
    auth=request.authorization
    payload = dataclasses.asdict(data) 
    game_id = await validate_game_id(payload["game_id"], next(cycleObj))
    guessObject = {}

    #Check if game is playable or complete. 
    url = next(cycleObj)
    db = await _get_db(url) 
    query = "SELECT * FROM In_Progress where game_id = :game_id"
    app.logger.info("SELECT * FROM In_Progress where game_id = " + str(payload["game_id"]))
    in_progress = await db.fetch_all(query=query, values={"game_id": str(payload["game_id"])})
    if not in_progress:
        return {"message": "Game has been completed already."}
    db = await close_connection(None)

    #Get secret word, format guess word, check if guess word is a valid word. 
    url = next(cycleObj)
    db = await _get_db(url) 
    app.logger.info("SELECT secretword FROM Game where game_id = " + str(payload["game_id"]))
    query = "SELECT secretword FROM Game where game_id = :game_id"
    secret_word = await db.fetch_one(query=query, values={"game_id": str(payload["game_id"])})
    db = await close_connection(None)
    secret_word = secret_word[0]
    guess_word = str(payload["guess_word"]).lower()

    url = next(cycleObj)
    db = await _get_db(url) 
    app.logger.info('SELECT * FROM Valid_Words where valid_word = "' + guess_word + '";')
    query = "SELECT * FROM Valid_Words where valid_word = :guess_word"
    is_valid_word_v = await db.fetch_all(query=query, values={"guess_word": guess_word})
    db = await close_connection(None)

    url = next(cycleObj)
    db = await _get_db(url) 
    app.logger.info('SELECT * FROM Correct_Words where correct_word = "' + guess_word + '";')
    query = "SELECT * FROM Correct_Words where correct_word = :guess_word"
    is_valid_word_c = await db.fetch_all(query=query, values={"guess_word": guess_word})
    db = await close_connection(None)
    if len(is_valid_word_v)==0 and len(is_valid_word_c)==0:
        return abort(404, "Not a Valid Word!")

    #Check guess count.
    url = next(cycleObj)
    db = await _get_db(url) 
    app.logger.info("SELECT Max(guess_num) FROM Guesses where game_id = " + str(payload["game_id"]))
    query = "SELECT Max(guess_num) FROM Guesses where game_id = :game_id"
    guessEntry = await db.fetch_one(query=query, values={"game_id": str(payload["game_id"])})
    db = await close_connection(None)
    guessCount = guessEntry[0]
    if guessCount == None:
        guessCount=0
    guessCount+=1
    guessObject["count"] = guessCount 

    #Check if guess is the secret word.
    if guess_word==secret_word:
        url = next(cycleObj)
        db = await _get_db(url) 
        app.logger.info("SELECT guess_word FROM Guesses WHERE game_id = " + str(payload["game_id"]) + " ORDER BY guess_num ASC")
        query = "SELECT guess_word FROM Guesses WHERE game_id = :game_id ORDER BY guess_num ASC"
        guesses_word = await db.fetch_all(query=query, values={"game_id": str(payload["game_id"])})
        db = await close_connection(None)

        loopCount=guessCount-1
        for i in range(loopCount):
            secret_wordcopy = secret_word     
            guess_wordloop = guesses_word[i][0]

            positionList = await guess_compute(guess_wordloop, secret_wordcopy, positionList=[])
            guessObject["guess"+str(i+1)] = positionList

        positionList = await guess_compute(guess_word, secret_word, positionList=[])
        guessObject["guess"+str(guessCount)] = positionList
        guessObject["message"]="You guessed the secret word!"
        db = await _get_writedb()
        insert_completed = await db.execute("INSERT INTO Completed(game_id, username, guess_num, outcome) VALUES(:game_id, :username, :guess_num, :outcome)", values={"game_id": str(payload["game_id"]), "username": auth.username, "guess_num":guessCount, "outcome":"Win"})
        delete_inprogress = await db.execute("DELETE FROM In_Progress WHERE game_id= :game_id", values={"game_id": str(payload["game_id"])})
        delete_guesses = await db.execute("DELETE FROM Guesses WHERE game_id=:game_id", values={"game_id": str(payload["game_id"])})
        db = await close_connection(None)
        return guessObject,200

    #Guess when the guess is not the secret word.  
    if guessCount<6:
        db = await _get_writedb()
        insert_guess = await db.execute("INSERT INTO Guesses(game_id, guess_num, guess_word) VALUES(:game_id, :guess_num, :guess_word)", values={"game_id": str(payload["game_id"]), "guess_num": guessCount, "guess_word": guess_word})
        db = await close_connection(None)
        url = next(cycleObj)
        db = await _get_db(url) 
        app.logger.info("SELECT guess_word FROM Guesses WHERE game_id = " + str(payload["game_id"]) + "ORDER BY guess_num ASC")
        guesses_word = await db.fetch_all("SELECT guess_word FROM Guesses WHERE game_id = :game_id ORDER BY guess_num ASC", values={"game_id": str(payload["game_id"])})
        db = await close_connection(None)
        loopCount=guessCount-1
        for i in range(loopCount):
            secret_wordcopy = secret_word     
            guess_wordloop = guesses_word[i][0]

            positionList = await guess_compute(guess_wordloop, secret_wordcopy, positionList=[])
            guessObject["guess"+str(i+1)] = positionList

        positionList = await guess_compute(guess_word, secret_word, positionList=[])
        guessObject["guess"+str(guessCount)] = positionList
        guessObject["message"] = "Guess again!"
        return guessObject, 200

    #If this is 6th guess
    else:
        url = next(cycleObj)
        db = await _get_db(url) 
        app.logger.info("SELECT guess_word FROM Guesses WHERE game_id = " + str(payload["game_id"]) + "ORDER BY guess_num ASC")
        guesses_word = await db.fetch_all("SELECT guess_word FROM Guesses WHERE game_id = :game_id ORDER BY guess_num ASC", values={"game_id": str(payload["game_id"])})
        db = await close_connection(None)
        loopCount=guessCount-1
        for i in range(loopCount):
            secret_wordcopy = secret_word     
            guess_wordloop = guesses_word[i][0]

            positionList = await guess_compute(guess_wordloop, secret_wordcopy, positionList=[])
            guessObject["guess"+str(i+1)] = positionList

        positionList = await guess_compute(guess_word, secret_word, positionList=[])
        guessObject["guess"+str(guessCount)] = positionList
        
        guessObject["message"]="Out of guesses! Make a new game to play again. "
        db = await _get_writedb()
        complete_game = await db.execute("INSERT INTO Completed(game_id, username, guess_num, outcome) VALUES(:game_id, :username, :guess_num, :outcome)", values={"game_id":str(payload["game_id"]), "username": auth.username, "guess_num":guessCount, "outcome": "Lose"})
        delete_inprogress = await db.execute("DELETE FROM In_Progress WHERE game_id=:game_id", values={"game_id": str(payload["game_id"])})
        delete_guesses = await db.execute("DELETE FROM Guesses WHERE game_id=:game_id", values={"game_id": str(payload["game_id"])})
        db = await close_connection(None)
        return guessObject, 200
    

# In progress game API
@app.route("/inprogressgame", methods=["GET"])
async def get_inprogressgame():
    url = next(cycleObj)
    db = await _get_db(url) 
    auth=request.authorization
    app.logger.info("SELECT game_id FROM In_Progress WHERE username = " + str(auth.username))
    inprogressgames = await db.fetch_all("SELECT game_id FROM In_Progress WHERE username = :username", values={"username": auth.username})
    db = await close_connection(None)
    if inprogressgames:
        if len(inprogressgames) >= 1:
            inprogressstring = str(inprogressgames[0][0])
            if len(inprogressgames) > 1:
                for i in range(1, len(inprogressgames)):
                    inprogressstring += ", " + str(inprogressgames[i][0])
                return {"message": f"Your in progress games are {inprogressstring}"}, 201
            return {"message": f"Your in progress game is {inprogressstring}"}, 201
    else:
        return {"message": f"There are no in progress games."}


# Game Status API
@app.route("/gamestatus/<string:game_id>", methods=["GET"])
async def game_status(game_id):
    game_id = await validate_game_id(game_id, next(cycleObj))

    #Check if in completed:
    url = next(cycleObj)
    db = await _get_db(url) 
    app.logger.info("SELECT * FROM Completed WHERE game_id = " + str(game_id[0]))
    game_id_completed = await db.fetch_one("SELECT * FROM Completed WHERE game_id = :game_id", values={"game_id": str(game_id[0])})
    db = await close_connection(None)

    #If not completed:
    if game_id_completed == None:
        url = next(cycleObj)
        db = await _get_db(url) 
        app.logger.info("SELECT secretword FROM Game WHERE game_id = " + str(game_id[0]))
        secret_word1 = await db.fetch_one("SELECT secretword FROM Game WHERE game_id = :game_id", values={"game_id": str(game_id[0])})
        db = await close_connection(None)
        url = next(cycleObj)
        db = await _get_db(url) 
        app.logger.info("SELECT max(guess_num) FROM Guesses WHERE game_id = " + str(game_id[0]))
        guesses_num = await db.fetch_all("SELECT max(guess_num) FROM Guesses WHERE game_id = :game_id", values={"game_id": str(game_id[0])})
        db = await close_connection(None)
        guessObject = {}
        if guesses_num[0][0] == None:
            guessObject["message"]="Game is currently in progress with no guesses."
            return guessObject, 200
        else:
            guessObject["message"]="Game is in progress with "+str(guesses_num[0][0])+" guesses."
            url = next(cycleObj)
            db = await _get_db(url) 
            app.logger.info("SELECT guess_word FROM Guesses WHERE game_id = " + str(game_id[0]) + "ORDER BY guess_num ASC")
            guesses_word = await db.fetch_all("SELECT guess_word, guess_num FROM Guesses WHERE game_id = :game_id ORDER BY guess_num ASC", values={"game_id": str(game_id[0])})
            db = await close_connection(None)
            for i in range(guesses_num[0][0]):
                loopNum=i+1
                secret_word = secret_word1[0]      
                guess_word = guesses_word[i][0]

                positionList = await guess_compute(guess_word, secret_word, positionList=[])
                guessObject["guess"+str(loopNum)] = positionList

    else:
        guessObject = {}
        if(game_id_completed[2]==6 and game_id_completed[3]=="Win"):
            guessObject["message"]="Game is completed and you have won with 6 guesses."
        elif (game_id_completed[2]==6 and game_id_completed[3]=="Lose"):
            guessObject["message"]="Game is completed and you have lost with 6 guesses."
        else:
            guessObject["message"]="Game is completed and you have won with "+str(game_id_completed[2])+ " guesses."
    
    return guessObject, 200
        


# function to compute Guess API and Game status Logic
async def guess_compute(guess_word, secret_word,positionList):
    for j in guess_word:
        response = {}
        response[j] = "red"
        positionList.append(response)


    for i in range(5):
        if secret_word[i] in positionList[i].keys():
            positionList[i][list(positionList[i].keys())[0]] = "green"
            secret_word = secret_word[:i] + "_" + secret_word[i+1:]
                                

    for i,j in enumerate(guess_word):
        if j in secret_word and positionList[i][list(positionList[i].keys())[0]] != "green":
            positionList[i][list(positionList[i].keys())[0]] = "yellow"
            secret_word=secret_word.replace(j, "_")

    return positionList