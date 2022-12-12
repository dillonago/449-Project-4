user: hypercorn WordleUserApi --reload --debug --bind WordleUserApi.local.gd:$PORT --access-logfile - --error-logfile - --log-level DEBUG
primary: ./bin/litefs -config ./etc/primary.yml
secondary: ./bin/litefs -config ./etc/secondary.yml
secondary2: ./bin/litefs -config ./etc/secondary2.yml
leaderboard: hypercorn WordleLeaderboardApi --reload --debug --bind WordleLeaderboardApi.local.gd:$PORT --access-logfile - --error-logfile - --log-level DEBUG