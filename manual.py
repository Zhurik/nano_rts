import numpy as np
import copy
import sys

from nanoRTS.nanoRTS import nanoRTS, nanoROOMS

import pygame
from pygame.locals import *


DEFAULT_FILE = "./scenarios/2_forts_2Av3K.json"


def main():
    if len(sys.argv) == 1:
        scenario = DEFAULT_FILE
    else:
        scenario = sys.argv[1]

    if "room" in scenario:
        env = nanoROOMS(scenario, visual=True, graphics=True, textures="./textures")
        actions = {
            "U": [0, -1],
            "R": [1, 0],
            "D": [0, 1],
            "L": [-1, 0]
        }

    elif "simple" in scenario:
        env = nanoRTS(scenario, visual=True, graphics=True, textures="./textures")
        if "W" in scenario:
            actions = {
                "U": [0, -1],
                "R": [1, 0],
                "D": [0, 1],
                "L": [-1, 0],
                "A": "Attack"
            }
        else:
            actions = {
                "DR": [1, 1],
                "R": [1, 0],
                "RR": [2, 0],
                "UR": [1, -1],
                "D": [0, 1],
                "DD": [0, 2],
                "DL": [-1, 1],
                "L": [-1, 0],
                "LL": [-2, 0],
                "UL": [-1, -1],
                "U": [0, -1],
                "UU": [0, -2],
                "A": "Attack"
            }

    elif "2_forts" in scenario:
        env = nanoRTS(scenario, visual=True, graphics=True, textures="./textures")
        actions = {
            "DR": [1, 1],
            "R": [1, 0],
            "RR": [2, 0],
            "UR": [1, -1],
            "D": [0, 1],
            "DD": [0, 2],
            "DL": [-1, 1],
            "L": [-1, 0],
            "LL": [-2, 0],
            "UL": [-1, -1],
            "U": [0, -1],
            "UU": [0, -2],
            "A": "Attack"
        }

    # elif "custom_map" in scenario:
    #     env = nanoCUSTOM(scenario, visual=True, graphics=True, textures="./textures")
    #     actions = {}
    # так можно тестировать новые кастомные сценарии

    else:
        print("Проблема со сценарием", scenario)
        return

    env.reset()

    total = 0

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
        a = input("Введите действия: ").split()
        acts = list()
        for act in a:
            if act in actions:
                acts.append(actions[act])
                continue

            if act.upper() in actions:
                acts.append(actions[act.upper()])
                continue

        _, r, t, _ = env.update(acts)
        print("Награда за ход", r)

        total += r

        if t:
            break

    print("Игра закончена!")
    print("Ваш счет: {}".format(total))


if __name__ == "__main__":
    main()
