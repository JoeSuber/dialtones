import sys
from random import randint

try:
    stake, target, bet, rate_of_return = sys.argv[1:]
except:
    stake = 400
    target = 600
    bet = 15
    rate_of_return = 0.98


trials = 10000


def game(bet, rate_of_return=rate_of_return):
    return (bet + bet*rate_of_return) * randint(0,1)


def ruin(stake=stake, target=target, bet=bet, trials=trials, payout=rate_of_return):
    original_stake = stake
    wins = 0
    promo = 0
    for t in range(trials):
        while ((stake - bet) > 0) and (stake < target):
            promo += bet
            stake -= bet
            stake += game(bet)
        if stake > original_stake:
            wins += 1
        stake = original_stake
    promo = promo / float(trials)
    print("{:.2f}%  wins going from ${} to ${} with bets of {}   ({:.3f} payout, ${:.2f} avg. promo bucks)"
          .format(100*(wins/float(trials)), stake, target, bet, payout, promo))

stakes = [300, 500]
targets = [550, 650, 750, 1000, 2000]
bets = [5, 15, 25, 75]
payouts = [0.985, 0.995]


def bigone():
    for stake in stakes:
        for target in targets:
            for bet in bets:
                for payout in payouts:
                    ruin(stake=stake, target=target, bet=bet, trials=trials, payout=payout)


if __name__ == "__main__":
    bigone()
