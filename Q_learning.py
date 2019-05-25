import numpy as np
import copy
import sys
import pickle
import datetime
import argparse

from nanoRTS.nanoRTS import nanoRTS, nanoROOMS


LEARNING_RATE = 0.3
GAMMA = 0.9
EPISODES = 5000000
MAX_TICKS = 500
TEST_EPISODES = 100
TEST_AMOUNT = 5000

MU = 0
SIGMA = 0.1

MAX_DIGITS = 4

DEFAULT_FILE = "./scenarios/simple_2Av3K.json"


def epsilon_greedy(Q, s, na, epsil):
    p = np.random.uniform(low=0, high=1)
    if p > epsil:
        return np.argmax(Q[s])
    else:
        return np.random.randint(na)


def main():
    if len(sys.argv) == 1:
        scenario = DEFAULT_FILE
    else:
        scenario = sys.argv[1]

    epsilon = 0.4

    if "room" in scenario:
        env = nanoROOMS(scenario)
    else:
        env = nanoRTS(scenario)

    result_name = scenario.split("/")[-1].split(".")[0]

    actions = copy.deepcopy(env.current_player[0]["actions"])

    actions_num = len(actions)

    Q = dict()

    s = env.current_field

    # Прячем всех агентов
    for player in env.current_player:
        s[player['location']['y']][player['location']['x']] = nanoRTS.TILE_EMPTY
    
    for player in env.current_player:
        s[player['location']['y']][player['location']['x']] = player['type'][0]

        Q[str(s)] = np.round(np.random.normal(MU, SIGMA, actions_num), MAX_DIGITS)

        s[player['location']['y']][player['location']['x']] = nanoRTS.TILE_EMPTY

    for i in range(EPISODES):
        env.reset()
        t = False
        r = 0
        total = 0
        s = copy.deepcopy(env.current_field)

        # Прячем всех агентов
        for player in env.current_player:
            s[player['location']['y']][player['location']['x']] = nanoRTS.TILE_EMPTY

        for tick in range(MAX_TICKS):
            a = []  # Действия, которые выполнят наши агенты
            nums = []  #  Коды действий агентов

            prev_players = copy.deepcopy(env.current_player)

            # Отображаем только текущего агента
            for player in env.current_player:
                s[player['location']['y']][player['location']['x']] = player['type'][0]

                if str(s) not in Q:
                    Q[str(s)] = np.round(np.random.normal(MU, SIGMA, actions_num), MAX_DIGITS)

                nums.append(epsilon_greedy(Q, str(s), actions_num, epsilon))
                a.append(actions[nums[-1]])

                s[player['location']['y']][player['location']['x']] = nanoRTS.TILE_EMPTY

            s_, r, t, _ = env.update(a)
            s_ = copy.deepcopy(s_)
			
            if tick == MAX_TICKS - 1 and not t:
                r -= 5

            for player in env.current_player:
                s_[player['location']['y']][player['location']['x']] = nanoRTS.TILE_EMPTY

            total += r

            for j, player in enumerate(prev_players):
                s[player['location']['y']][player['location']['x']] = player['type'][0]

                if str(s) not in Q:
                    Q[str(s)] = np.round(np.random.normal(MU, SIGMA, actions_num), MAX_DIGITS)

                clean = False

                for next_player in env.current_player:
                    if next_player['number'] == player['number']:
                        x = next_player['location']['y']
                        y = next_player['location']['x']
                        s_[x][y] = player['type'][0]

                        clean = True
                        break

                if str(s_) not in Q:
                    Q[str(s_)] = np.round(np.random.normal(MU, SIGMA, actions_num), MAX_DIGITS)

                Q[str(s)][nums[j]] = np.round(
                    (1 - LEARNING_RATE) * Q[str(s)][nums[j]] + LEARNING_RATE * (r + GAMMA * (max(Q[str(s_)]))),
                    MAX_DIGITS
                )

                s[player['location']['y']][player['location']['x']] = nanoRTS.TILE_EMPTY

                if clean:
                    s_[x][y] = nanoRTS.TILE_EMPTY

            s = s_

            if t:
                break

        if i % TEST_AMOUNT == 0:
            print("{} episodes done! Counting winrate...".format(i))

            if epsilon > 0.01:
                epsilon -= 0.001

            win = 0
            ticks_win = 0
            ticks_lost = 0
            rew_win = 0
            rew_lost = 0
            for _ in range(TEST_EPISODES):
                env.reset()
                end = False
                r = 0
                total = 0
                s = copy.deepcopy(env.current_field)
                ticks_test = 0

                # Прячем всех агентов
                for player in env.current_player:
                    s[player['location']['y']][player['location']['x']] = nanoRTS.TILE_EMPTY

                for tick in range(MAX_TICKS):
                    a = []  # Действия, которые выполнят наши агенты
                    nums = []  #  Коды действий агентов

                    # Отображаем только текущего агента
                    for player in env.current_player:
                        s[player['location']['y']][player['location']['x']] = player['type'][0]

                        if str(s) not in Q:
                            Q[str(s)] = np.round(np.random.normal(MU, SIGMA, actions_num), MAX_DIGITS)

                        nums.append(np.argmax(Q[str(s)]))
                        a.append(actions[nums[-1]])

                        s[player['location']['y']][player['location']['x']] = nanoRTS.TILE_EMPTY

                    s_, r, end, _ = env.update(a)
                    s_ = copy.deepcopy(s_)

                    total += r

                    s = s_

                    if end:
                        ticks_test = tick
                        break

                else:
                    total -= 5
                    ticks_test = MAX_TICKS - 1

                if total > 0:
                    win += 1
                    ticks_win += ticks_test
                    rew_win += total
                else:
                    ticks_lost += ticks_test
                    rew_lost += total
            
            print("Winrate: {}%".format(win))
            with open(result_name + ".txt", "a") as logs:
                logs.write("{}\t\t{}\t\t{}\t\t{}\t\t{}\t\t{}\t\t{}\n".format(i, win, ticks_win, ticks_lost, rew_win, rew_lost, datetime.datetime.now()))

            with open(result_name + ".pickle", "wb") as pickle_file:
                pickle.dump(Q, pickle_file)


if __name__ == "__main__":
    main()
