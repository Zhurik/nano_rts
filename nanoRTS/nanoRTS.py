import json
import copy
import math
import random
import os

import pygame
from pygame.locals import *

from time import sleep


class nanoRTS:
    TILE_EMPTY = '_'
    TILE_ROCK = '#'

    TILE_SIZE = 40

    COLORS = {
        "A": (0, 0, 255),
        "W": (0, 0, 255),
        "K": (200, 200, 200),
        "_": (150, 150, 150),
        "#": (50, 50, 50)
    }

    TEXTURES = {
        "A": "archer.png",
        "K": "knight.png",
        "W": "warrior.png"
    }

    def __init__(self, json_path, visual=False, graphics=False, textures=""):
        self.field, self.width, self.height, self.player, self.enemy = self._parse_json(json_path)

        self.current_field = None
        self.current_player = None
        self.current_enemy = None
        self.current_end = None

        self.reset()

        self.visual = visual
        self.graphics = graphics

        self._display = None

        if self.visual:
            self._visualize(verbose=True)

        if self.graphics:
            if textures:
                self._textures_path = textures
                self._textures = dict()

            else:
                self._textures_path = False

            self._render(first=True)

    def _visualize(self, verbose=False):
        """Метод для визуализации игрового процесса"""
        for line in self.current_field:
            print(" ".join(str(x) for x in line))

        print()

        if verbose:
            print("Player stats:")
            for unit in self.current_player:
                print(unit)

            print()

            print("Enemy stats:")
            for unit in self.current_enemy:
                print(unit)

    def _render(self, first=False):
        if first:
            pygame.init()
            self._display = pygame.display.set_mode((
                self.width * (nanoRTS.TILE_SIZE + 1),
                self.height * (nanoRTS.TILE_SIZE + 1)
            ))

            if self._textures_path:
                for item in nanoRTS.TEXTURES:
                    self._textures[item] = pygame.image.load(os.path.join(self._textures_path, nanoRTS.TEXTURES[item]))
                    self._textures[item].convert()

        self._draw_field()
        pygame.display.flip()

    def _draw_field(self):
        for row, line in enumerate(self.current_field):
            for col, tile in enumerate(line):
                if self._textures_path:
                    if tile in self._textures:
                        self._display.blit(
                            self._textures[tile],
                            (
                                col * nanoRTS.TILE_SIZE + col,
                                row * nanoRTS.TILE_SIZE + row,
                                nanoRTS.TILE_SIZE,
                                nanoRTS.TILE_SIZE
                            )
                        )
                        continue

                pygame.draw.rect(
                    self._display,
                    nanoRTS.COLORS[tile],
                    (
                        col * nanoRTS.TILE_SIZE + col,
                        row * nanoRTS.TILE_SIZE + row,
                        nanoRTS.TILE_SIZE,
                        nanoRTS.TILE_SIZE
                    )
                )

    def reset(self):
        self.current_field = copy.deepcopy(self.field)
        self.current_player = copy.deepcopy(self.player)
        self.current_enemy = copy.deepcopy(self.enemy)
        self.current_end = False

    def update(self, actions):
        if self.current_end:
            return False

        reward = self._check_end()

        if reward != 0:
            print(reward)
            self.current_end = True
            return copy.deepcopy(self.current_field), reward, self.current_end, len(self.current_player)

        for i, action in enumerate(actions):
            if self.current_player[i] is not None:
                damage, kill = self._apply_action(action, self.current_player[i], self.current_enemy)

                if damage:
                    reward += 0.1

                if kill:
                    reward += 1

        enemy_actions = self._enemy_make_move()

        for i, action in enumerate(enemy_actions):
            if self.current_enemy[i] is not None:
                damage, kill = self._apply_action(action, self.current_enemy[i], self.current_player)

                if damage:
                    reward -= 0.1

                if kill:
                    reward -= 0.5

        result = self._check_end()

        if result != 0:
            self.current_end = True

        # Можно давать вознаграждения не только по окончанию эпизода
        reward += result

        if self.visual:
            self._visualize()

        if self.graphics:
            self._draw_field()
            pygame.display.flip()

        return copy.deepcopy(self.current_field), reward, self.current_end, len(self.current_player)

    def _apply_action(self, action, agent, enemies):
        damaged = False
        killed = False

        if action == 'Attack':
            for i, enemy in enumerate(enemies):
                if enemy is not None:
                    if self._calc_dist(
                            agent['location']['x'],
                            agent['location']['y'],
                            enemy['location']['x'],
                            enemy['location']['y']
                    ) <= agent['distance']:
                        enemy['health'] -= agent['damage']
                        damaged = True

                        if enemy['health'] <= 0:
                            self.current_field[enemy['location']['y']][enemy['location']['x']] = nanoRTS.TILE_EMPTY
                            del(enemies[i])
                            killed = True
                        break
        else:
            if self._check_direction(action, agent):

                self.current_field[agent['location']['y']][agent['location']['x']],\
                    self.current_field[agent['location']['y'] + action[1]][agent['location']['x'] + action[0]] = \
                    self.current_field[agent['location']['y'] + action[1]][agent['location']['x'] + action[0]],\
                    self.current_field[agent['location']['y']][agent['location']['x']]

                agent['location']['x'],\
                    agent['location']['y'] =\
                    agent['location']['x'] + action[0],\
                    agent['location']['y'] + action[1]

        return damaged, killed

    def _check_direction(self, direction, agent):
        if 0 > agent['location']['x'] + direction[0] or agent['location']['x'] + direction[0] >= self.width:
            return False

        if 0 > agent['location']['y'] + direction[1] or agent['location']['y'] + direction[1] >= self.height:
            return False

        if self.current_field[agent['location']['y'] + direction[1]][agent['location']['x'] + direction[0]]\
                != nanoRTS.TILE_EMPTY:
            return False

        return True

    def _enemy_make_move(self):
        actions = list()

        for agent in self.current_enemy:
            ind, dist = self._find_closest_enemy(agent, self.current_player)

            if dist <= agent['distance']:
                actions.append('Attack')
                continue

            direction = []
            x_dir = agent['location']['x'] - self.current_player[ind]['location']['x']
            y_dir = agent['location']['y'] - self.current_player[ind]['location']['y']

            # Для разных типов юнитов можно добавлять разные ходы,
            # для последующего случайного выбора одного из них
            if x_dir > 0:
                direction.append(agent['actions'][3])  # [-1, 0]
            elif x_dir < 0:
                direction.append(agent['actions'][1])  # [1, 0]

            if y_dir > 0:
                direction.append(agent['actions'][4])  # [0, -1]
            elif y_dir < 0:
                direction.append(agent['actions'][2])  # [0, 1]

            actions.append(random.choice(direction))
        return actions

    @staticmethod
    def _calc_dist(x1, y1, x2, y2):
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def _find_closest_enemy(self, agent, enemies):
        min_dist = self._calc_dist(
            agent['location']['x'],
            agent['location']['y'],
            enemies[0]['location']['x'],
            enemies[0]['location']['y']
        )
        min_ind = 0

        for num, enemy in enumerate(enemies):
            if self._calc_dist(
                    agent['location']['x'],
                    agent['location']['y'],
                    enemy['location']['x'],
                    enemy['location']['y']
            ) < min_dist:
                min_ind = num
                min_dist = self._calc_dist(
                    agent['location']['x'],
                    agent['location']['y'],
                    enemy['location']['x'],
                    enemy['location']['y']
                )

        return min_ind, min_dist

    def _check_end(self):
        result = 0

        if not self.current_player:
            result = -10
        elif not self.current_enemy:
            result = 10
        return result

    @staticmethod
    def _parse_json(path):
        player = list()
        enemy = list()

        with open(path, "r") as setting_file:
            settings = json.load(setting_file)

        field = list(list(nanoRTS.TILE_EMPTY for _ in range(settings['width'])) for _ in range(settings['height']))

        for rock in settings['rocks']:
            field[rock['x']][rock['y']] = nanoRTS.TILE_ROCK

        for unit in settings['player']:
            field[unit['location']['y']][unit['location']['x']] = unit['type'][0]
            player.append(unit)

        for unit in settings['enemy']:
            field[unit['location']['y']][unit['location']['x']] = unit['type'][0]
            enemy.append(unit)
        return field, settings['width'], settings['height'], player, enemy


class nanoROOMS:
    TILE_EMPTY = '_'
    TILE_ROCK = '#'

    TILE_SIZE = 40

    COLORS = {
        "A": (0, 0, 255),
        "W": (0, 0, 255),
        "K": (200, 200, 200),
        "_": (150, 150, 150),
        "#": (50, 50, 50)
    }

    TEXTURES = {
        "A": "archer.png",
        "K": "knight.png",
        "W": "warrior.png"
    }

    def __init__(self, json_path, visual=False, graphics=False, textures=""):
        self.field, self.width, self.height, self.player = self._parse_json(json_path)

        self.current_field = None
        self.current_player = None
        self.current_end = None

        self.reset()

        self.visual = visual
        self.graphics = graphics

        self._display = None

        if self.visual:
            self._visualize(verbose=True)

        if self.graphics:
            if textures:
                self._textures_path = textures
                self._textures = dict()

            else:
                self._textures_path = False

            self._render(first=True)

    def _visualize(self, verbose=False):
        """Метод для визуализации игрового процесса"""
        for line in self.current_field:
            print(" ".join(str(x) for x in line))

        print()

        if verbose:
            print("Player stats:")
            for unit in self.current_player:
                print(unit)

    def _render(self, first=False):
        if first:
            pygame.init()
            self._display = pygame.display.set_mode(
                (
                    self.width * (nanoRTS.TILE_SIZE + 1),
                    self.height * (nanoRTS.TILE_SIZE + 1)
                )
            )

            if self._textures_path:
                for item in nanoRTS.TEXTURES:
                    self._textures[item] = pygame.image.load(os.path.join(self._textures_path, nanoRTS.TEXTURES[item]))
                    self._textures[item].convert()

        self._draw_field()
        pygame.display.flip()

    def _draw_field(self):
        for row, line in enumerate(self.current_field):
            for col, tile in enumerate(line):
                if self._textures_path:
                    if tile in self._textures:
                        self._display.blit(
                            self._textures[tile],
                            (
                                col * nanoRTS.TILE_SIZE + col,
                                row * nanoRTS.TILE_SIZE + row,
                                nanoRTS.TILE_SIZE,
                                nanoRTS.TILE_SIZE
                            )
                        )
                        continue

                pygame.draw.rect(
                    self._display,
                    nanoRTS.COLORS[tile],
                    (
                        col * nanoRTS.TILE_SIZE + col,
                        row * nanoRTS.TILE_SIZE + row,
                        nanoRTS.TILE_SIZE,
                        nanoRTS.TILE_SIZE
                    )
                )

    def reset(self):
        self.current_field = copy.deepcopy(self.field)
        self.current_player = copy.deepcopy(self.player)
        self.current_end = False

    def update(self, actions):
        if self.current_end:
            return False

        reward = self._check_end()

        if reward != 0:
            self.current_end = True
            return copy.deepcopy(self.current_field), reward, self.current_end, len(self.current_player)

        for i, action in enumerate(actions):
            if self.current_player[i] is not None:
                door, end = self._apply_action(action, self.current_player[i])

                if door:
                    reward += 0.5

                if end:
                    self.current_player[i] = None
                    reward += 10

        self.current_player = list(filter(None, self.current_player))

        result = self._check_end()

        if result != 0:
            self.current_end = True

        # Можно давать вознаграждения не только по окончанию эпизода
        reward += result

        if reward == 0:
            reward = -0.1

        if self.visual:
            self._visualize(verbose=True)

        if self.graphics:
            self._draw_field()
            pygame.display.flip()

        return copy.deepcopy(self.current_field), reward, self.current_end, len(self.current_player)

    def _apply_action(self, action, agent):
        door = False
        end = False

        if self._check_direction(action, agent):
            self.current_field[agent['location']['y']][agent['location']['x']],\
                self.current_field[agent['location']['y'] + action[1]][agent['location']['x'] + action[0]] = \
                self.current_field[agent['location']['y'] + action[1]][agent['location']['x'] + action[0]],\
                self.current_field[agent['location']['y']][agent['location']['x']]

            agent['location']['x'],\
                agent['location']['y'] =\
                agent['location']['x'] + action[0],\
                agent['location']['y'] + action[1]

            if agent['location']['x'] == self.finish['x'] and agent['location']['y'] == self.finish['y']:
                self.current_field[agent['location']['y']][agent['location']['x']] = nanoROOMS.TILE_EMPTY
                end = True

            if {"x": agent['location']['x'], "y": agent['location']['y']} in self.doors:
                if self.get_room_number(agent) not in agent['visited']:
                    agent['visited'].append(self.get_room_number(agent))
                    door = True

                self.current_field[agent['location']['y']][agent['location']['x']],\
                    self.current_field[agent['location']['y'] + action[1]][agent['location']['x'] + action[0]] = \
                    self.current_field[agent['location']['y'] + action[1]][agent['location']['x'] + action[0]],\
                    self.current_field[agent['location']['y']][agent['location']['x']]

                agent['location']['x'],\
                    agent['location']['y'] =\
                    agent['location']['x'] + action[0],\
                    agent['location']['y'] + action[1]

        return door, end

    @staticmethod
    def get_room_number(agent):
        if 0 < agent['location']['x'] < 6:
            if 0 < agent['location']['y'] < 7:
                return 0
            else:
                return 2
        else:
            if 0 < agent['location']['y'] < 7:
                return 1
            else:
                return 3

    def _check_direction(self, direction, agent):
        if 0 > agent['location']['x'] + direction[0] or agent['location']['x'] + direction[0] >= self.width:
            return False

        if 0 > agent['location']['y'] + direction[1] or agent['location']['y'] + direction[1] >= self.height:
            return False

        if self.current_field[agent['location']['y'] + direction[1]][agent['location']['x'] + direction[0]]\
                != nanoRTS.TILE_EMPTY:
            return False

        return True

    def _check_end(self):
        result = 0

        if not self.current_player:
            result = 10
        return result

    def _parse_json(self, path):
        player = list()

        with open(path, "r") as setting_file:
            settings = json.load(setting_file)

        field = list(list(nanoRTS.TILE_EMPTY for _ in range(settings['width'])) for _ in range(settings['height']))

        for rock in settings['rocks']:
            field[rock['x']][rock['y']] = nanoRTS.TILE_ROCK

        for unit in settings['player']:
            field[unit['location']['y']][unit['location']['x']] = unit['type'][0]
            player.append(unit)

        self.finish = settings['finish']

        self.doors = settings['doors']

        return field, settings['width'], settings['height'], player


def main():
    nanoRTS("./scenarios/2_forts_2Av3K.json", visual=True, graphics=True, textures="./textures")
    sleep(5)


if __name__ == "__main__":
    main()
