import sys
from random import randint

try:
    stake, target, bet, rate_of_return = sys.argv[1:]
except:
    stake = 400
    target = 600
    bet = 15
    rate_of_return = 0.98
    print("using defaults for stake: ${}, target ${} and bet ${} and game return = {}"
          .format(stake, target, bet, rate_of_return))

trials = 10000

def game(bet, rate_of_return=rate_of_return):
    return (bet + bet*rate_of_return) * randint(0,1)


def ruin(stake=stake, target=target, bet=bet):
    original_stake = stake
    wins = 0
    for t in range(trials):
        while ((stake - bet) > 0) and (stake < target):
            stake -= bet
            stake += game(bet)
        if stake > original_stake:
            wins += 1
        stake = original_stake
    print("{}/{} wins of greater than ${} (at {} payout ratio)".format(wins, trials, target, rate_of_return))


if __name__ == "__main__":
    ruin()
