import redis

leaderboard = redis.Redis()
leaderboard.flushdb()

def addgame(game):
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

def main():

    games = [
        {"user": "ashley", "result": "Won", "guesses": 5},
        {"user": "dillon", "result": "Won", "guesses": 3},
        {"user": "brent", "result": "Won", "guesses": 4},
        {"user": "jack", "result": "Lost", "guesses": 6},
        {"user": "john", "result": "Won", "guesses": 2},
        {"user": "jill", "result": "Won", "guesses": 1},
        {"user": "anthony", "result": "Lost", "guesses": 6},
        {"user": "mary", "result": "Won", "guesses": 4},
        {"user": "philip", "result": "Won", "guesses": 2},
        {"user": "sean", "result": "Won", "guesses": 1},
        {"user": "tim", "result": "Lost", "guesses": 6},
        {"user": "ava", "result": "Won", "guesses": 3},

        {"user": "dillon", "result": "Won", "guesses": 5},
        {"user": "ashley", "result": "Won", "guesses": 3},
        {"user": "jill", "result": "Won", "guesses": 4},
        {"user": "anthony", "result": "Lost", "guesses": 6},
        {"user": "sean", "result": "Won", "guesses": 2},
        {"user": "brent", "result": "Won", "guesses": 1},
        {"user": "jack", "result": "Lost", "guesses": 6},
        {"user": "philip", "result": "Won", "guesses": 4},
        {"user": "mary", "result": "Won", "guesses": 2},
        {"user": "john", "result": "Won", "guesses": 1},
        {"user": "ava", "result": "Lost", "guesses": 6},
        {"user": "tim", "result": "Won", "guesses": 3},

        {"user": "tim", "result": "Won", "guesses": 5},
        {"user": "ava", "result": "Won", "guesses": 3},
        {"user": "john", "result": "Won", "guesses": 4},
        {"user": "mary", "result": "Lost", "guesses": 6},
        {"user": "philip", "result": "Won", "guesses": 2},
        {"user": "jack", "result": "Won", "guesses": 1},
        {"user": "brent", "result": "Lost", "guesses": 6},
        {"user": "sean", "result": "Won", "guesses": 4},
        {"user": "anthony", "result": "Won", "guesses": 2},
        {"user": "jill", "result": "Won", "guesses": 1},
        {"user": "ashley", "result": "Lost", "guesses": 6},
        {"user": "dillon", "result": "Won", "guesses": 3},
    ]

    for game in games:
        addgame(game)

if __name__ == "__main__":
    main()
