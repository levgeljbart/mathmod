import pathlib
import typing as tp
from random import randint, shuffle
import threading
import os
from time import sleep, time

width, height = os.get_terminal_size()

T = tp.TypeVar("T")


def read_sudoku(path: tp.Union[str, pathlib.Path]) -> tp.List[tp.List[str]]:
    """ Прочитать судоку из файла """
    path = pathlib.Path(path)
    with path.open() as f:
        puzzle = f.read()
    return create_grid(puzzle)


def create_grid(puzzle: str) -> tp.List[tp.List[str]]:
    digits = [c for c in puzzle if c in "123456789."]
    grid = group(digits, 9)
    return grid


def display(grid: tp.List[tp.List[str]]) -> None:
    """Вывод судоку """
    width = 2
    line = "+".join(["-" * (width * 3)] * 3)
    for row in range(9):
        print(
            "".join(
                grid[row][col].center(width) + ("|" if str(col) in "25" else "") for col in range(9)
            )
        )
        if str(row) in "25":
            print(line)

    print()


def group(values: tp.List[T], n: int) -> tp.List[tp.List[T]]:
    """
    Сгруппировать значения values в список, состоящий из списков по n элементов

    >>> group([1,2,3,4], 2)
    [[1, 2], [3, 4]]
    >>> group([1,2,3,4,5,6,7,8,9], 3)
    [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    """

    matrix = []
    for i in range(0, n):
        matrix.append([values[c] for c in range(i*n, (i+1)*n)])
    return matrix




def get_row(grid: tp.List[tp.List[str]], pos: tp.Tuple[int, int]) -> tp.List[str]:
    """Выбирает значения ячеек из строки, в который попадает pos

    >>> get_row([['1', '2', '.'], ['4', '5', '6'], ['7', '8', '9']], (0, 0))
    ['1', '2', '.']
    >>> get_row([['1', '2', '3'], ['4', '.', '6'], ['7', '8', '9']], (1, 0))
    ['4', '.', '6']
    >>> get_row([['1', '2', '3'], ['4', '5', '6'], ['.', '8', '9']], (2, 0))
    ['.', '8', '9']
    """
    (row_index, *_)  = pos
    return grid[row_index]
    


def get_col(grid: tp.List[tp.List[str]], pos: tp.Tuple[int, int]) -> tp.List[str]:
    """Выбирает значения ячеек из столбца, в который попадает pos

    >>> get_col([['1', '2', '.'], ['4', '5', '6'], ['7', '8', '9']], (0, 0))
    ['1', '4', '7']
    >>> get_col([['1', '2', '3'], ['4', '.', '6'], ['7', '8', '9']], (0, 1))
    ['2', '.', '8']
    >>> get_col([['1', '2', '3'], ['4', '5', '6'], ['.', '8', '9']], (0, 2))
    ['3', '6', '9']
    """

    (_, col_index)  = pos
    return [grid[i][col_index] for i in range(len(grid))]


def get_block(grid: tp.List[tp.List[str]], pos: tp.Tuple[int, int]) -> tp.List[str]:
    """Выбирает значения ячеек из квадрата 3 на 3, в который попадает pos

    >>> grid = read_sudoku('puzzle1.txt')
    >>> get_block(grid, (0, 1))
    ['5', '3', '.', '6', '.', '.', '.', '9', '8']
    >>> get_block(grid, (4, 7))
    ['.', '.', '3', '.', '.', '1', '.', '.', '6']
    >>> get_block(grid, (8, 8))
    ['2', '8', '.', '.', '.', '5', '.', '7', '9']
    """
    assert len(grid) == 9
    y, x = pos
    x, y = x // 3 , y // 3 
    x, y = x*3, y* 3


    res =  grid[y][x:x+3] + grid[y + 1][x:x+3] + grid[y + 2][x:x+3]
    return res

    


def find_empty_positions(grid: tp.List[tp.List[str]]) -> tp.Optional[tp.Tuple[int, int]]:
    """Находит первую свободную ячейку в паззле

    >>> find_empty_positions([['1', '2', '.'], ['4', '5', '6'], ['7', '8', '9']])
    (0, 2)
    >>> find_empty_positions([['1', '2', '3'], ['4', '.', '6'], ['7', '8', '9']])
    (1, 1)
    >>> find_empty_positions([['1', '2', '3'], ['4', '5', '6'], ['.', '8', '9']])
    (2, 0)
    """
    #suppose is squared
    N = len(grid)*len(grid[0])
    size = len(grid)
    for i in range(N):
        magic_x, magic_y = i%size, i//size # magic_x  returning x, magic_y returnig y
        if grid[magic_y][magic_x] == '.':
            return(magic_y, magic_x)
    return None



def find_possible_values(grid: tp.List[tp.List[str]], pos: tp.Tuple[int, int]) -> tp.Set[str]:
    """Для данной ячейки получить допустимые значения

    >>> grid = read_sudoku('puzzle1.txt')
    >>> values = find_possible_values(grid, (0,2))
    >>> values == {'1', '2', '4'}
    True
    >>> values = find_possible_values(grid, (4,7))
    >>> values == {'2', '5', '9'}
    True
    """
    block = get_block(grid, pos)
    row = get_row(grid, pos)
    col = get_col(grid, pos)
    values = block +  row + col 
    return set([str(possible) for possible in range(1, 10) if str(possible) not in values])

def newgrid(grid: tp.List[tp.List[str]], y: int ,x: int, value: int):
    g = [[val for val in line] for line in grid]
    g[y][x] = str(value);
    return g;

def solve(grid: tp.List[tp.List[str]]) -> tp.Optional[tp.List[tp.List[str]]]:
    """ Решение пазла, заданного в grid """
    """ Как решать Судоку?
        1. Найти свободную позицию
        2. Найти все возможные значения, которые могут находиться на этой позиции
        3. Для каждого возможного значения:
            3.1. Поместить это значение на эту позицию
            3.2. Продолжить решать оставшуюся часть пазла

    >>> grid = read_sudoku('puzzle1.txt')
    >>> solve(grid)
    [['5', '3', '4', '6', '7', '8', '9', '1', '2'], ['6', '7', '2', '1', '9', '5', '3', '4', '8'], ['1', '9', '8', '3', '4', '2', '5', '6', '7'], ['8', '5', '9', '7', '6', '1', '4', '2', '3'], ['4', '2', '6', '8', '5', '3', '7', '9', '1'], ['7', '1', '3', '9', '2', '4', '8', '5', '6'], ['9', '6', '1', '5', '3', '7', '2', '8', '4'], ['2', '8', '7', '4', '1', '9', '6', '3', '5'], ['3', '4', '5', '2', '8', '6', '1', '7', '9']]
    """
    free_position = find_empty_positions(grid)
    if not free_position:
        return grid
    else:
        possible_values = list(find_possible_values(grid, free_position))
        shuffle(possible_values)
        possible_values = set(possible_values)
        if possible_values:
            y, x = free_position
            res = None

            for value in possible_values:
                grid[y][x] = value
                val = solve(grid)
                if val:
                    res = val
                    break
                    
            if res:
                return res
            else:
                grid[y][x] = '.'
            return None

            
def dot_filter(array):

    return list(filter(lambda x: x != '.', array))

def unique(array):

    return len(array) == len(set(array))

def grid_is_unique(grid):

    results = []
    for i in range(9):
        results.append(cell_is_unique(grid, (i,0), (0,i), (3*(i//3), 3 * (i % 3))))
    return(all(results))
        
        
def cell_is_unique(grid, pos_row, pos_col, pos_block):
    row = dot_filter(get_row(grid, pos_row))
    col = dot_filter(get_col(grid, pos_col))
    block = dot_filter(get_block(grid, pos_block))

    if unique(row) and unique(col) and unique(block):
        return True
    return False
        


def check_solution(solution: tp.List[tp.List[str]]) -> bool:
    """ Если решение solution верно, то вернуть True, в противном случае False 

    >>> grid = read_sudoku('puzzle1.txt')
    >>> check_solution(solve(grid))
    True
    >>> grid = read_sudoku('puzzle2.txt')
    >>> check_solution(solve(grid))
    True
    >>> grid = read_sudoku('puzzle3.txt')
    >>> check_solution(solve(grid))
    True

    """
    if solution == None:
        return False
    is_full = all([i.count('.')  == 0 for i in solution])
    is_correct = all([len(find_possible_values(solution, (i,j )))==0 for j in range(9) for i in range(9)])
    is_unique = grid_is_unique(solution)
            
            
    if is_full and is_correct and solution != None and is_unique:
        return True
    return False




def generate_sudoku(N: int) -> tp.List[tp.List[str]]:
    """Генерировать судоку, заполненное на N элементов

    >>> grid = generate_sudoku(40)
    >>> sum(1 for row in grid for e in row if e == '.')
    41
    >>> solution = solve(grid)
    >>> check_solution(solution)
    True
    >>> grid = generate_sudoku(1000)
    >>> sum(1 for row in grid for e in row if e == '.')
    0
    >>> solution = solve(grid)
    >>> check_solution(solution)
    True
    >>> grid = generate_sudoku(0)
    >>> sum(1 for row in grid for e in row if e == '.')
    81
    >>> solution = solve(grid)
    >>> check_solution(solution)
    True
    """
    if (N > 81):
        N = 81
    grid = [['.' for j in range(9)] for i in range(9)]
    grid[0][0] = str(randint(1,9))
    solution = solve(grid)
    for i in range(81 - N):
        y,x = randint(0,8), randint(0,8)
        while grid[y][x] == '.':
            y,x = randint(0,8), randint(0,8)
        grid[y][x] = '.'
    return grid
        
        


        
def get_hard_puzzles():
    f = open("hard_puzzles.txt", "r")
    lines = f.readlines()
    return [puzzle[0:81] for puzzle in lines]

    
def run_solve(grid, index) -> None:
    start = time()
    sol = solve(grid)
    end = time()
    print(f"{index} reshen za {end-start}")



if __name__ == "__main__":
    for fname in ["puzzle1.txt", "puzzle2.txt", "puzzle3.txt"]:
        grid = read_sudoku(fname)
        display(grid)
        solution = solve(grid)
        if not solution:
            print(f"Puzzle {fname} ne reshaetsa")
        else:
            print("\n --- Puzzle reshen! --- \n\n")
            display(solution)
    pazzles = get_hard_puzzles()
    index = 0
    for puzzle in pazzles:
        index += 1
        grid = group(puzzle, 9)
        t = threading.Thread(target=run_solve, args=(grid,index,))
        t.start()

