import pygame
import os
import sys
import copy
from pathlib import Path

def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key is -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


def count_lvs():
    result = 0

    for currentdir, dirs, files in os.walk('data'):
        for file in files:
            if '.map' in file:
                result += 1

    return result


pygame.init()
screen_size = (950, 550)
screen = pygame.display.set_mode(screen_size)
FPS = 50
Boxes = 0
num_level = 0
count_levels = count_lvs()

tile_images = {
    'wall': load_image('wall.png'),
    'empty': load_image('grass.png'),
    'box': load_image('box.png'),
    'place': load_image('place.png'),
    'solved': load_image('solved.png')
}
player_image = load_image('mar.png')

tile_width = tile_height = 50


class ScreenFrame(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.rect = (0, 0, 950, 550)


class SpriteGroup(pygame.sprite.Group):

    def __init__(self):
        super().__init__()

    def get_event(self, event):
        for sprite in self:
            sprite.get_event(event)


class Sprite(pygame.sprite.Sprite):

    def __init__(self, group):
        super().__init__(group)
        self.rect = None

    def get_event(self, event):
        pass


class Tile(Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(sprite_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class Box(Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(box_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)

    def move(self, x, y):
        self.pos = (x, y)
        self.rect = self.image.get_rect().move(
            tile_width * self.pos[0], tile_height * self.pos[1])

    def update(self):
        if pygame.sprite.collide_mask(self, hero):
            self.kill()


class Player(Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(hero_group)
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x + 15, tile_height * pos_y + 5)
        self.pos = (pos_x, pos_y)

    def move(self, x, y):
        self.pos = (x, y)
        self.rect = self.image.get_rect().move(
            tile_width * self.pos[0] + 15, tile_height * self.pos[1] + 5)


player = None
running = True
clock = pygame.time.Clock()
sprite_group = SpriteGroup()
hero_group = SpriteGroup()
box_group = SpriteGroup()


def terminate():
    pygame.quit()
    sys.exit


def start_screen():
    intro_text = ["Классическая головоломка!!!",
                  "Цель:",
                  "Необходимо все ящики",
                  "установить на звезды.",
                  "Управление - стрелки.",
                  "Старт - любое действие.",
                  "Вперед!!!!"]

    pygame.display.set_caption('Super Mario Sokoban')
    fon = pygame.transform.scale(load_image('fon.png'), screen_size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 200

    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 600
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: list(x.ljust(max_width, '.')), level_map))


def generate_level(level):
    global Boxes
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == '#':
                Tile('wall', x, y)
            elif level[y][x] == '%':
                Box('box', x, y)
            elif level[y][x] == '*':
                Tile('place', x, y)
                Boxes += 1
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x, y)
                level[y][x] = "."
    return new_player, x, y


def move(hero, movement):
    x, y = hero.pos

    if movement == "up":
        if y > 0 and (level_map[y - 1][x] == "." or level_map[y - 1][x] == "*"):
            hero.move(x, y - 1)
        elif y > 1 and level_map[y - 1][x] == "%" and level_map[y - 2][x] == ".":
            level_map[y - 1][x] = "."
            level_map[y - 2][x] = "%"
            Tile('empty', x, y - 1)
            Box('box', x, y - 2)
            hero.move(x, y - 1)
        elif y > 1 and level_map[y - 1][x] == "%" and level_map[y - 2][x] == "*":
            level_map[y - 1][x] = "."
            level_map[y - 2][x] = "%*"
            Tile('empty', x, y - 1)
            Box('box', x, y - 2)
            hero.move(x, y - 1)
        elif y > 1 and level_map[y - 1][x] == "%*" and level_map[y - 2][x] == ".":
            level_map[y - 1][x] = "*"
            level_map[y - 2][x] = "%"
            Tile('place', x, y - 1)
            Box('box', x, y - 2)
            hero.move(x, y - 1)
        elif y > 1 and level_map[y - 1][x] == "%*" and level_map[y - 2][x] == "*":
            level_map[y - 1][x] = "*"
            level_map[y - 2][x] = "%*"
            Tile('place', x, y - 1)
            Box('box', x, y - 2)
            hero.move(x, y - 1)
    elif movement == "down":
        if y < max_y - 1 and (level_map[y + 1][x] == "." or level_map[y + 1][x] == "*"):
            hero.move(x, y + 1)
        elif y < max_y - 2 and level_map[y + 1][x] == "%" and level_map[y + 2][x] == ".":
            level_map[y + 1][x] = "."
            level_map[y + 2][x] = "%"
            Tile('empty', x, y + 1)
            Box('box', x, y + 2)
            hero.move(x, y + 1)
        elif y < max_y - 2 and level_map[y + 1][x] == "%" and level_map[y + 2][x] == "*":
            level_map[y + 1][x] = "."
            level_map[y + 2][x] = "%*"
            Tile('empty', x, y + 1)
            Box('box', x, y + 2)
            hero.move(x, y + 1)
        elif y < max_y - 2 and level_map[y + 1][x] == "%*" and level_map[y + 2][x] == ".":
            level_map[y + 1][x] = "*"
            level_map[y + 2][x] = "%"
            Tile('place', x, y + 1)
            Box('box', x, y + 2)
            hero.move(x, y + 1)
        elif y < max_y - 2 and level_map[y + 1][x] == "%*" and level_map[y + 2][x] == "*":
            level_map[y + 1][x] = "*"
            level_map[y + 2][x] = "%*"
            Tile('place', x, y + 1)
            Box('box', x, y + 2)
            hero.move(x, y + 1)
    elif movement == "left":
        hero.image = player_image

        if x > 0 and (level_map[y][x - 1] == "." or level_map[y][x - 1] == "*"):
            hero.move(x - 1, y)
        elif x > 1 and level_map[y][x - 1] == "%" and level_map[y][x - 2] == ".":
            level_map[y][x - 2] = "%"
            level_map[y][x - 1] = "."
            Tile('empty', x - 1, y)
            Box('box', x - 2, y)
            hero.move(x - 1, y)
        elif x > 1 and level_map[y][x - 1] == "%" and level_map[y][x - 2] == "*":
            level_map[y][x - 2] = "%*"
            level_map[y][x - 1] = "."
            Tile('empty', x - 1, y)
            Box('box', x - 2, y)
            hero.move(x - 1, y)
        elif x > 1 and level_map[y][x - 1] == "%*" and level_map[y][x - 2] == ".":
            level_map[y][x - 2] = "%"
            level_map[y][x - 1] = "*"
            Tile('place', x - 1, y)
            Box('box', x - 2, y)
            hero.move(x - 1, y)
        elif x > 1 and level_map[y][x - 1] == "%*" and level_map[y][x - 2] == "*":
            level_map[y][x - 2] = "%*"
            level_map[y][x - 1] = "*"
            Tile('place', x - 1, y)
            Box('box', x - 2, y)
            hero.move(x - 1, y)
    elif movement == "right":
        hero.image = pygame.transform.flip(player_image, True, False)

        if x < max_x - 1 and (level_map[y][x + 1] == "." or level_map[y][x + 1] == "*"):
            hero.move(x + 1, y)
        elif x < max_x - 2 and level_map[y][x + 1] == "%" and level_map[y][x + 2] == ".":
            level_map[y][x + 2] = "%"
            level_map[y][x + 1] = "."
            Tile('empty', x + 1, y)
            Box('box', x + 2, y)
            hero.move(x + 1, y)
        elif x < max_x - 2 and level_map[y][x + 1] == "%" and level_map[y][x + 2] == "*":
            level_map[y][x + 2] = "%*"
            level_map[y][x + 1] = "."
            Tile('empty', x + 1, y)
            Box('box', x + 2, y)
            hero.move(x + 1, y)
        elif x < max_x - 2 and level_map[y][x + 1] == "%*" and level_map[y][x + 2] == ".":
            level_map[y][x + 2] = "%"
            level_map[y][x + 1] = "*"
            Tile('place', x + 1, y)
            Box('box', x + 2, y)
            hero.move(x + 1, y)
        elif x < max_x - 2 and level_map[y][x + 1] == "%*" and level_map[y][x + 2] == "*":
            level_map[y][x + 2] = "%*"
            level_map[y][x + 1] = "*"
            Tile('place', x + 1, y)
            Box('box', x + 2, y)
            hero.move(x + 1, y)


def win():
    count = 0
    for y in range(len(level_map)):
        for x in range(len(level_map[y])):
            if level_map[y][x] == '%*' and level_map_start[y][x] == '*':
                count += 1
    return count == Boxes


start_screen()
level_map = load_level("map" + str(num_level) + ".map")
level_map_start = copy.deepcopy(level_map)
hero, max_x, max_y = generate_level(level_map)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                move(hero, "up")
            elif event.key == pygame.K_DOWN:
                move(hero, "down")
            elif event.key == pygame.K_LEFT:
                move(hero, "left")
            elif event.key == pygame.K_RIGHT:
                move(hero, "right")

    screen.fill(pygame.Color("black"))
    box_group.update()
    sprite_group.draw(screen)
    box_group.draw(screen)
    hero_group.draw(screen)
    clock.tick(FPS)
    pygame.display.flip()

    if win():
        solvedRect = tile_images['solved'].get_rect()
        solvedRect.center = (450, 325)
        screen.blit(tile_images['solved'], solvedRect)
        you_win_break = True
        while you_win_break:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    #if event.key == pygame.K_SPACE:
                    you_win_break = False
            clock.tick(FPS)
            pygame.display.flip()
        num_level += 1
        if num_level == count_levels:
            running = False
        else:
            sprite_group.empty()
            box_group.empty()
            hero_group.empty()
            Boxes = 0
            level_map = load_level("map" + str(num_level) + ".map")
            level_map_start = copy.deepcopy(level_map)
            hero, max_x, max_y = generate_level(level_map)

pygame.quit()
