# За основу взят код из: https://russianblogs.com/article/64361336576/

import random
import pygame
import sys
import numpy as np

BG = (34, 40, 49) # Фоновый цвет
LIFECOLOR = (255, 211, 105)  # Цвет живой клетки
LINECOLOR = (57, 62, 70)  # Цвет сетки

LINE_WIDTH = 3  # Ширина линии
EDGE_WIDTH = 20 # Ширина сетки от края фоновой рамки
START_POSX = 20
START_POSY = 20

SCREEN_SIZE = 550 # размер экрана
CELL_NUM = 25 # размер игрового поля

# натюрморты
F_BLOCK = {0: [0, 1], 1 : [0, 1]}
F_HIVE = {0: [1, 2], 1 : [0, 3], 2 : [1, 2]}
F_LOAF = {0 : [2], 1 : [1, 3], 2 : [0, 3], 3 : [1, 2]}
F_BOX = {0 : [1], 1 : [0, 2], 2 : [1]}

# осцилляторы
F_BLINKER = {0: [0, 1, 2]}
F_TOAD = {0: [1, 2, 3], 1 : [0, 1, 2]}
F_BEACON = {0 : [0, 1], 1 : [0], 2 : [3], 3 : [2, 3]}

F_CROSS = {0 : [2, 3, 4, 5], 1 : [2, 5], 2 : [0, 1, 2, 5, 6, 7], 3 : [0, 7], 4 : [0, 7], 5 : [0, 1, 2, 5, 6, 7], 6 : [2, 5], 7 : [2, 3, 4, 5]} # крест
F_GALAXY = {
    0 : [3, 4, 6, 7, 8, 9, 10, 11], 
    1 : [3, 4, 6, 7, 8, 9, 10, 11],
    2 : [3, 4],
    3 : [3, 4, 10, 11],
    4 : [3, 4, 10, 11],
    5 : [3, 4, 10, 11],
    6 : [10, 11],
    7 : [3, 4, 5, 6, 7, 8, 10, 11],
    8 : [3, 4, 5, 6, 7, 8, 10, 11]
    }

# космические корбали
F_GLIDER = {0: [1], 1 : [2], 2 : [0, 1, 2]}

# ружья
F_GUN = {
    0 : [24], 
    1 : [22, 24],
    2 : [12, 13, 20, 21, 34, 35],
    3 : [11, 15, 20, 21, 34, 35],
    4 : [0, 1, 10, 16, 20, 21],
    5 : [0, 1, 10, 14, 16, 17, 22, 24],
    6 : [10, 16, 24],
    7 : [11, 15],
    8 : [12, 13]
}

# некоторые начальные конфигурации игры
PLAYGROUND_1 = [(F_BLOCK, (1, 1)), (F_HIVE, (5, 1)), (F_LOAF, (10, 1)), (F_BOX, (16, 1)), (F_BLINKER, (2, 5)), (F_TOAD, (7, 7)), (F_BEACON, (13, 7)), (F_GLIDER, (2, 13)), (F_GLIDER, (8, 13))]
PLAYGROUND_2 = [(F_GALAXY, (3, 0)), (F_CROSS, (14, 14))]
PLAYGROUND_3 = [(F_GUN, (1, 1))] # для этой конфигурации требуется игровое поле размера:

# SCREEN_SIZE = 880
# CELL_NUM = 40 

class Cell:
    """
    Клетка
    """
    def __init__(self, ix, iy, is_live):
        self.ix = ix # координата по x
        self.iy = iy # координата по y
        self.is_live = is_live # жива ли
        self.neighbour_count = 0 # число живых соседей

    def __str__(self):
        return "[{},{},{:5}]".format(self.ix, self.iy, str(self.is_live))

    # подсчитываем количество живых соседей вокруг, координаты верхнего левого угла экрана (0, 0)
    def calc_neighbour_count(self):
        count = 0
        pre_x = self.ix - 1 if self.ix > 0 else 0  # зачение x левого соседа клетки
        for i in range(pre_x, self.ix + 1 + 1):    # от левого соседа до правого соседа клетки
            pre_y = self.iy - 1 if self.iy > 0 else 0 # значение y соседа в клетки
            for j in range(pre_y, self.iy + 1 + 1): # от верхнего соседа до нижнего соседа клетки
                # клетка сама по себе, продолжить, без счета
                if i == self.ix and j == self.iy:
                    continue
                # клетка недействительна, продолжить, нет подсчета
                if self.invalidate(i, j):
                    continue
                # CellGrid.cells [i] [j] .is_live возвращает логическое значение, int (True) равно 1, int (False) равно 0
                # count подсчитывает количество живых соседей
                count += int(CellGrid.cells[i][j].is_live)
        self.neighbour_count = count
        return count

    def invalidate(self, x, y):
        if x >= CellGrid.cx or y >= CellGrid.cy: # значение x или y клетки больше диапазона решётки, недопустимо
            return True
        if x < 0 or y < 0: # значение x или y клетки не входит в диапазон решётки, недопустимо
            return True
        return False

    # правила игры:
    def rule(self):
        if self.neighbour_count > 3 or self.neighbour_count < 2:
            self.is_live = False
        elif self.neighbour_count == 3:
            self.is_live = True
        elif self.neighbour_count == 2:
            pass

class CellGrid:
    """
    Решётка из клеток длиной cx и шириной cy
    """
    cells = []
    cx = 0
    cy = 0

    def __init__(self, cx, cy, configuration = []):
        CellGrid.cx = cx
        CellGrid.cy = cy

        for i in range(cx):
            cell_list = []

            for j in range(cy):
                if len(configuration) == 0:
                    cell = Cell(i, j, random.random() > 0.5) # инициализируем клетки случайно
                else:
                    cell = Cell(i, j, configuration[i][j]) # задаем определенные состояния

                cell_list.append(cell)  # промещаем клетки в список
            CellGrid.cells.append(cell_list)  # собираем списки из клеток в список

    # проверяем каждую клетку, чтобы определить ее жизненное состояние
    def circulate_rule(self):
        for cell_list in CellGrid.cells:
            for item in cell_list:
                item.rule()

    # проверяем каждую клетку, чтобы вычислить количество живых соседей
    def circulate_nbcount(self):
        for cell_list in CellGrid.cells:
            for item in cell_list:
                item.calc_neighbour_count()

class Game:
    screen = None

    def __init__(self, width, height, cx, cy, configuration = []):
        self.width = width
        self.height = height
        self.cx_rate = int((width - 2*EDGE_WIDTH) / cx)   # ширина клетки
        self.cy_rate = int((height - 2*EDGE_WIDTH) / cy)  # высота клетки

        # pygame.display.set_mode () Инициализировать окно или экран для отображения (ширина * высота)
        self.screen = pygame.display.set_mode([width, height])

        if len(configuration) == 0: # если не было передано начальной конфигурации
            self.cells = CellGrid(cx, cy) # инициализируем случайным образом
        else:
            self.cells = CellGrid(cx, cy, configuration)

    # показать "жизнь" на экране
    def show_life(self):
        # pygame.draw.line(Surface, color, start_pos, end_pos, width=1)
        for i in range(self.cells.cx + 1):
            pygame.draw.line(self.screen, LINECOLOR, (START_POSX, START_POSY + i * self.cy_rate),
                             (START_POSX + self.cells.cx * self.cx_rate, START_POSY + i * self.cy_rate), LINE_WIDTH)  # рисуем линии решетки
            pygame.draw.line(self.screen, LINECOLOR, (START_POSX + i * self.cx_rate, START_POSY),
                             (START_POSX + i * self.cx_rate, START_POSY + self.cells.cx * self.cy_rate), LINE_WIDTH)  # рисуем вертикальные линии решетки

        for cell_list in self.cells.cells:
            for item in cell_list:
                x = item.ix
                y = item.iy
                if item.is_live:
                    """
                    pygame.draw.rect(Surface, color, Rect, width=0)
                                         Rect имеет вид ((x, y), (width, height))
                    """
                    pygame.draw.rect(self.screen, LIFECOLOR,
                                     [START_POSX+x * self.cx_rate+ (LINE_WIDTH - 1),
                                      START_POSY+y * self.cy_rate+ (LINE_WIDTH - 1),
                                      self.cx_rate- LINE_WIDTH, self.cy_rate- LINE_WIDTH])

def max_2d(list_2d):
    """
    Максимум в списке из списков 
    """
    res = list_2d[0][0]
    for l in list_2d:
        for element in l:
            if element > res:
                res = element
    return res

def add_figure(configuration, figure, indexes):
    """
    configuration (ndarray) - начальная конфигурация поля;
    figure (dict) - структура для добавления на поле;
    indexes = (x, y) - месторасположение структуры
    """
    (x, y) = indexes

    x_max = max(list(figure.keys())) + 1
    y_max = max_2d(list(figure.values())) + 1

    if (x + x_max > len(configuration) or y + y_max > len(configuration[0])):
        print("Ошибка! Некорректное расположение или соотношение размеров поля и фигуры")
        return configuration

    fig = np.full((x_max, y_max), False)

    for (key, value) in figure.items():
        fig[key][value] = True

    configuration = np.array(configuration)
    configuration[x : x + x_max, y : y + y_max] = fig

    return configuration

def main():
    pygame.init()   # инициализировать все импортированные модули pygame
    pygame.display.set_caption("Game of Life")  # установить заголовок окна

    playground = np.full((CELL_NUM, CELL_NUM), False)

    for (fig, indexes) in PLAYGROUND_2:
        playground = add_figure(playground, fig, indexes)

    # game = Game(SCREEN_SIZE, SCREEN_SIZE, CELL_NUM, CELL_NUM, playground)
    game = Game(SCREEN_SIZE, SCREEN_SIZE, CELL_NUM, CELL_NUM) # случайная инициализация

    clock = pygame.time.Clock() # создать экземпляр объекта Clock
    while True:
        game.screen.fill(BG)
        clock.tick(1) # цикл 1 раз в секунду
        for event in pygame.event.get(): # pygame.event.get () Получить события из очереди
            if event.type == pygame.QUIT:
                sys.exit()

        # game - экземпляр объекта класса Game, game.cells - экземпляр объекта класса CellGrid
        game.cells.circulate_nbcount()  # подсчитайте количество выживших соседей
        game.cells.circulate_rule()     # оцените свое собственное жизненное состояние в соответствии с правилами

        game.show_life()
        pygame.display.flip()  # обновить всю поверхность для отображения на экране

if __name__ == "__main__":
    main()