import sys
from random import randint
from datetime import timedelta
from collections import OrderedDict

""" the real purpose of this is to explore some data visualization and practice.
    A nice side-effect is exploring the reality of playing video poker."""

try:
    stake, target, bet, rate_of_return = sys.argv[1:]
except:
    stake = 400
    target = 600
    bet = 15
    rate_of_return = 0.98

trials = 2000
seconds_per_hand = 8

def game1(bet, rate_of_return=rate_of_return):
    """ a generic fictional game that can approximate the long-term rate of return for any casino game """
    return (bet + bet*rate_of_return) * randint(0,1)

""" paytable and odds from https://wizardofodds.com/games/video-poker/tables/jacks-or-better/
    Jacks or better, '9-5' style """

paytable = OrderedDict([(10862898027756, 0), (4288342040640, 1), (2577431192796, 2),(1484332642620, 3),
                        (223861063908, 4), (217120426644, 5),(229510637676, 9),(47100799404, 25),  (2137447980, 50),
                        (496237776, 800)])

possibles = sum(paytable.keys())

def game(bet, possibles=possibles, paytable=paytable):
    """ play video poker or some other game according to a pre-determined paytable odds chart
        that is ordered from the most-to-least likely outcomes"""
    spin = randint(0, possibles)
    cumulate = 0
    for k in paytable:
        cumulate += k
        if spin < cumulate: break
    return bet * paytable[k], 1 if paytable[k] >= 800 else 0


def ruin(stake=stake, target=target, bet=bet, trials=trials):
    """ play the game starting with a 'stake' and quitting when reaching the 'target' or losing so much that
     another full bet cannot be made. 'bet' the same amount during all 'trial'
     Report the dollar turnover and win percentage"""
    original_stake = stake
    wins = 0
    promo_history = []
    jackpots = 0
    for t in range(trials):
        promo = 0
        while ((stake - bet) > 0) and (stake < target):
            winnings, jackpot = game(bet)
            promo += bet
            stake += (winnings - bet)
            jackpots += jackpot
        if stake > original_stake: # if above ended ahead, its a win!
            wins += 1
        promo_history.append(promo)
        stake = original_stake
    promo_avg = sum(promo_history) / float(trials)
    promo_max = max(promo_history)
    promo_min = min(promo_history)
    hands_played = int(promo_avg / bet)
    time_spent = str(timedelta(seconds=(hands_played * seconds_per_hand)))
    print("win {:.2f}%  risk ${} to get ${} @ ${} / bet, avg rollover: ${:.2f} in {}  min:${:.2f}, max ${:.2f} jackpots: {}"
          .format(100*(wins/float(trials)), stake, target, bet, promo_avg, time_spent, promo_min, promo_max, jackpots))


stakes = [260, 350, 500]
targets = [450, 550, 750, 1000, 5000]
bets = [5, 15, 25, 50]

def bigone():
    for bet in bets:
        for stake in stakes:
            for target in targets:
                ruin(stake=stake, target=target, bet=bet, trials=trials)


if __name__ == "__main__":
    print(" *** If playing perfect video poker until ruination or a target goal ({} trials): ***".format(trials))
    bigone()
