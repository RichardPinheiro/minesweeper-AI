import itertools
import random


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """
        count = 0

        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                if (i, j) == cell:
                    continue
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        if self.count == len(self.cells):
            return self.cells
        return set()

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        if self.count == 0:
            return self.cells
        return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            self.cells.remove(cell)
            self.count = max(self.count - 1, 0)

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            self.cells.remove(cell)

class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge: list[Sentence] = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.
        """
        self.moves_made.add(cell)
        self.mark_safe(cell)
        self.knowledge.append(self.create_sentence_from_neighbors(cell, count))
        self.infer_cells_from_knowledge();
        self.infer_new_sentences();

    def create_sentence_from_neighbors(self, cell: tuple[int, int], count: int) -> Sentence:
        """
        Constructs a sentence from the unknown neighbors of a revealed safe cell.
        Excludes known safes, mines, and past moves, and adjusts the count if mines are known.
        """
        neighbors = set()

        for row in range(cell[0] - 1, cell[0] + 2):
            for col in range(cell[1] - 1, cell[1] + 2):
                if 0 <= row < self.height and 0 <= col < self.width:
                    neighbor = (row, col)
                    if neighbor == cell:
                        continue
                    if (
                        neighbor not in self.safes and
                        neighbor not in self.mines and
                        neighbor not in self.moves_made
                    ):
                        neighbors.add(neighbor)
                    else:
                        count = max(count - 1, 0)

        return Sentence(neighbors, count)

    def infer_cells_from_knowledge(self) -> None:
        """
        Infers and marks additional safe cells and mines based on the current knowledge base.
        Iterates through all known logical sentences. If a sentence implies that all remaining
        cells are either safe or mines, those cells are marked accordingly.
        """
        for sentence in self.knowledge:
            for cell in list(sentence.known_mines()):
                self.mark_mine(cell)
            for cell in list(sentence.known_safes()):
                self.mark_safe(cell)

    def infer_new_sentences(self) -> None:
        """
        Infers new logical sentences by analyzing subset relationships in the knowledge base.
        If one sentence is a subset of another, a new sentence is formed from the difference
        in cells and counts, representing additional knowledge about remaining unknown cells.
        """
        for a in self.knowledge:
            for b in self.knowledge:
                if a is b:
                    continue
                if b.cells.issubset(a.cells):
                    new = Sentence(a.cells - b.cells, a.count - b.count)
                    if new.cells and new not in self.knowledge:
                        self.knowledge.append(new)

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.
        """
        for move in self.safes:
            if move not in self.moves_made:
                return move
        return None

    def make_random_move(self):
        """
        Returns a random move that is not known to be a mine
        and has not been made on the Minesweeper board.
        """
        moves = [
            (row, col)
            for row in range(self.height)
            for col in range(self.width)
            if (row, col) not in self.moves_made and (row, col) not in self.mines
        ]

        return random.choice(moves) if moves else None
