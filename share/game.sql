-- $ sqlite3 ./var/primary/mount/game.db < ./share/game.sql


PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;

DROP TABLE IF EXISTS Game;
CREATE TABLE Game(game_id VARCHAR PRIMARY KEY, username VARCHAR, secretword VARCHAR, guess_num INTEGER);

DROP TABLE IF EXISTS In_Progress;
CREATE TABLE In_Progress(game_id VARCHAR, username VARCHAR, FOREIGN KEY(game_id) REFERENCES Game(game_id));

DROP TABLE IF EXISTS Completed;
CREATE TABLE Completed(game_id VARCHAR, username VARCHAR, guess_num INTEGER, outcome VARCHAR, FOREIGN KEY(game_id) REFERENCES Game(game_id)); 

DROP TABLE IF EXISTS Guesses;
CREATE TABLE Guesses(game_id VARCHAR, guess_num INTEGER, guess_word VARCHAR, FOREIGN KEY(game_id) REFERENCES Game(game_id));

DROP TABLE IF EXISTS Correct_Words;
CREATE TABLE Correct_Words(correct_word_id INTEGER PRIMARY KEY, correct_word VARCHAR);

DROP TABLE IF EXISTS Valid_Words;
CREATE TABLE Valid_Words(valid_word_id INTEGER PRIMARY KEY, valid_word VARCHAR);

CREATE INDEX In_Progress_idx_03a6cf4e ON In_Progress(game_id);
CREATE INDEX Valid_Words_idx_c0412b53 ON Valid_Words(valid_word);
CREATE INDEX Correct_Words_idx_0193f9a5 ON Correct_Words(correct_word);
CREATE INDEX Guesses_idx_d2617697 ON Guesses(game_id, guess_num DESC);
CREATE INDEX In_Progress_idx_25674218 ON In_Progress(username);
CREATE INDEX Completed_idx_03a6cf4e ON Completed(game_id);

COMMIT;

