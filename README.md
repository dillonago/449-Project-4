# CPSC449Project2

## Members of Team: 
Ashley Thorlin, Brent Pfefferle, Dillon Go

## Introduction:
Previously, we split the monolith service created in Project 1(Wordle) into two seperate services User and Games and authenticating endpoints. In previous version we used HTTP basic authentication for signin endpoint but rest of the endpoints of games remained unauthenticated.

For this project, we added replicas of the game database and distributed reads. We also implemented a leaderboard service that takes the average score for each user and places them in a leaderboard where you can see the top 10. 

## Steps to run our program:
1. Navigate to the correct directory of the project file and make sure you have redis installed.  
2. Configure Nginx:
```
cd /etc/nginx/sites-enabled
sudo "${EDITOR:-vi}" tutorial
```
Then paste code in the "Nginx Configuration section, then run:
```
sudo service nginx restart
```
3. For logging, create a .env file with this inside:
```
QUART_ENV=development
```
4. To start the service, run this line of code:
```
foreman start
```
5. To initialize the databases and redis server, we will run it by running these lines of code:
```
./bin/init.sh
```

## Leaderboard Endpoints
To add a game to the leaderboard database, send a request using the following format:
```
http POST http://tuffix-vm/leaderboard user="newestuser" result="Won" guesses=3
```
To view the top 10, run this command:
```
http GET http://tuffix-vm/leaderboard/top10
```

## Database:
 The var folder holds two Databases:
 1. game.db
 2. user.db


1. game.db contains following tables:
Game,in_progress,Completed,Guessses,Correct_words,valid_words

2. user.db contains following tables:
 User table(containing username & password)

## Nginx Configuration:
-configuring nginx to load balance between three games service
-setting up the server_name pointing to tuffix-vm(in case of Tuffix 2020 VM) 
-authenticating based on subrequest
```
upstream gameLoad {
       server 127.0.0.1:5100;
       server 127.0.0.1:5200;
       server 127.0.0.1:5300;
}

server {
       listen 80;
       listen [::]:80;

       server_name tuffix-vm;

       location / {
               proxy_pass http://gameLoad;
               auth_request /auth;
               auth_request_set $auth_status $upstream_status;
       }

       location /user{
               proxy_pass http://127.0.0.1:5000;
       }

       location /leaderboard{
               proxy_pass http://127.0.0.1:5400;
       }

       location = /auth {
                internal;
                proxy_pass http://127.0.0.1:5000;
                proxy_pass_request_body off;
                proxy_set_header Content-Length "";
                proxy_set_header X-Original-URI $request_uri;
       }
}
```



