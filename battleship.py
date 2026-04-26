"""
Battleship Game - OOP Coursework 2026
Implements all 4 OOP pillars, Factory design pattern,
composition/aggregation, file I/O, and PEP8 style.
"""

import csv
import os
import random
from abc import ABC, abstractmethod


# ─────────────────────────────────────────────
# ABSTRACTION – abstract base classes
# ─────────────────────────────────────────────

class GameObject(ABC):
    """Abstract base for every object in the game."""

    @abstractmethod
    def display_info(self):
        """Display information about this object."""


class AbstractPlayer(ABC):
    """Abstract player contract."""

    @abstractmethod
    def choose_target(self, board) -> tuple:
        """Return (row, col) to fire at."""

    @abstractmethod
    def get_name(self) -> str:
        """Return player name."""


# ─────────────────────────────────────────────
# ENCAPSULATION – Ship hierarchy
# ─────────────────────────────────────────────

class Ship(GameObject):
    """
    Represents a ship on the board.
    Private attributes accessed through properties (encapsulation).
    """

    def __init__(self, name: str, size: int, symbol: str):
        self._name = name          # encapsulated
        self._size = size          # encapsulated
        self._symbol = symbol      # encapsulated
        self._hits = 0             # encapsulated
        self._positions = []       # list of (row, col) tuples

    # ── properties (controlled access) ──────

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        return self._size

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def positions(self) -> list:
        return list(self._positions)   # return a copy

    @property
    def is_sunk(self) -> bool:
        return self._hits >= self._size

    def add_position(self, row: int, col: int):
        self._positions.append((row, col))

    def register_hit(self):
        if not self.is_sunk:
            self._hits += 1

    def display_info(self):
        status = "SUNK" if self.is_sunk else f"{self._hits}/{self._size} hits"
        print(f"  [{self._symbol}] {self._name} (size {self._size}) – {status}")


# ─────────────────────────────────────────────
# INHERITANCE – concrete ship types
# ─────────────────────────────────────────────

class Carrier(Ship):
    """Largest ship, size 5."""
    def __init__(self):
        super().__init__("Carrier", 5, "C")

    def display_info(self):
        print("  ★ ", end="")
        super().display_info()


class Battleship(Ship):
    """Size 4."""
    def __init__(self):
        super().__init__("Battleship", 4, "B")


class Cruiser(Ship):
    """Size 3."""
    def __init__(self):
        super().__init__("Cruiser", 3, "R")


class Submarine(Ship):
    """Size 3."""
    def __init__(self):
        super().__init__("Submarine", 3, "S")


class Destroyer(Ship):
    """Smallest ship, size 2."""
    def __init__(self):
        super().__init__("Destroyer", 2, "D")


# ─────────────────────────────────────────────
# DESIGN PATTERN – Factory Method
# ─────────────────────────────────────────────

class ShipFactory:
    """
    Factory Method pattern.
    Centralises ship creation so callers never use constructors directly.
    Makes it easy to add new ship types without changing the game logic.
    """

    _registry = {
        "carrier":    Carrier,
        "battleship": Battleship,
        "cruiser":    Cruiser,
        "submarine":  Submarine,
        "destroyer":  Destroyer,
    }

    @classmethod
    def create(cls, ship_type: str) -> Ship:
        """
        Factory Method: create a Ship by type name.
        Raises ValueError for unknown types.
        """
        key = ship_type.lower()
        if key not in cls._registry:
            raise ValueError(f"Unknown ship type: '{ship_type}'")
        return cls._registry[key]()

    @classmethod
    def fleet(cls) -> list:
        """Return the standard fleet (one of each ship type)."""
        return [cls.create(t) for t in cls._registry]


# ─────────────────────────────────────────────
# COMPOSITION – Board contains Ships and a Grid
# ─────────────────────────────────────────────

class Grid:
    """
    10×10 grid of cells.
    Board *has-a* Grid (composition – Grid cannot exist without Board).
    """

    SIZE = 10
    EMPTY = "."
    HIT = "X"
    MISS = "O"

    def __init__(self):
        self._cells = [
            [self.EMPTY] * self.SIZE for _ in range(self.SIZE)
        ]

    def get(self, row: int, col: int) -> str:
        return self._cells[row][col]

    def set(self, row: int, col: int, value: str):
        self._cells[row][col] = value

    def display(self, reveal_ships: bool = False):
        header = "   " + " ".join(str(c) for c in range(self.SIZE))
        print(header)
        for r in range(self.SIZE):
            row_label = f"{r:2} "
            cells = []
            for c in range(self.SIZE):
                val = self._cells[r][c]
                if not reveal_ships and val not in (self.HIT, self.MISS, self.EMPTY):
                    cells.append(self.EMPTY)
                else:
                    cells.append(val)
            print(row_label + " ".join(cells))


class Board(GameObject):
    """
    Represents one player's board.
    Uses COMPOSITION with Grid (Board owns a Grid).
    Uses AGGREGATION with Ship objects (ships exist independently).
    """

    def __init__(self, owner_name: str):
        self._owner = owner_name          # encapsulation
        self._grid = Grid()               # composition
        self._ships = []                  # aggregation
        self._shots_received = set()      # (row, col) pairs

    # ── properties ──────────────────────────

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def ships(self) -> list:
        return list(self._ships)

    @property
    def all_sunk(self) -> bool:
        return all(s.is_sunk for s in self._ships)

    # ── ship placement ───────────────────────

    def add_ship(self, ship: Ship, row: int, col: int, horizontal: bool) -> bool:
        """Place ship on board. Returns False if placement is invalid."""
        positions = []
        for i in range(ship.size):
            r = row + (0 if horizontal else i)
            c = col + (i if horizontal else 0)
            if not (0 <= r < Grid.SIZE and 0 <= c < Grid.SIZE):
                return False
            if self._grid.get(r, c) != Grid.EMPTY:
                return False
            positions.append((r, c))

        for r, c in positions:
            self._grid.set(r, c, ship.symbol)
            ship.add_position(r, c)

        self._ships.append(ship)   # aggregation
        return True

    def place_ship_randomly(self, ship: Ship) -> bool:
        """Try to place ship at a random valid location (max 100 attempts)."""
        for _ in range(100):
            row = random.randint(0, Grid.SIZE - 1)
            col = random.randint(0, Grid.SIZE - 1)
            horizontal = random.choice([True, False])
            if self.add_ship(ship, row, col, horizontal):
                return True
        return False

    # ── shooting ────────────────────────────

    def receive_shot(self, row: int, col: int) -> str:
        """
        Process an incoming shot.
        Returns 'already_shot', 'hit', 'sunk', or 'miss'.
        """
        if (row, col) in self._shots_received:
            return "already_shot"
        self._shots_received.add((row, col))

        for ship in self._ships:
            if (row, col) in ship.positions:
                ship.register_hit()
                self._grid.set(row, col, Grid.HIT)
                return "sunk" if ship.is_sunk else "hit"

        self._grid.set(row, col, Grid.MISS)
        return "miss"

    # ── display ──────────────────────────────

    def display_info(self):
        print(f"\n{'='*24}")
        print(f"  Board – {self._owner}")
        print(f"{'='*24}")
        for ship in self._ships:
            ship.display_info()

    def display_grid(self, reveal: bool = False):
        self._grid.display(reveal_ships=reveal)


# ─────────────────────────────────────────────
# INHERITANCE + POLYMORPHISM – Player hierarchy
# ─────────────────────────────────────────────

class Player(AbstractPlayer, GameObject):
    """
    Human player.
    Inherits from AbstractPlayer and GameObject (multiple inheritance).
    """

    def __init__(self, name: str):
        self._name = name              # encapsulation
        self._board = Board(name)      # composition
        self._shots_fired = 0
        self._hits = 0

    # ── properties ──────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @property
    def board(self) -> Board:
        return self._board

    @property
    def shots_fired(self) -> int:
        return self._shots_fired

    @property
    def hits(self) -> int:
        return self._hits

    # ── AbstractPlayer interface ─────────────

    def get_name(self) -> str:
        return self._name

    def choose_target(self, board: Board) -> tuple:
        """Prompt human for (row, col)."""
        while True:
            try:
                raw = input("  Enter target (row col): ").strip().split()
                if len(raw) != 2:
                    raise ValueError
                row, col = int(raw[0]), int(raw[1])
                if not (0 <= row < Grid.SIZE and 0 <= col < Grid.SIZE):
                    print("  Out of range (0-9). Try again.")
                    continue
                return row, col
            except ValueError:
                print("  Invalid input. Enter two numbers, e.g. '3 5'")

    # ── shot tracking ────────────────────────

    def record_shot(self, result: str):
        self._shots_fired += 1
        if result in ("hit", "sunk"):
            self._hits += 1

    # ── GameObject interface ─────────────────

    def display_info(self):
        accuracy = (self._hits / self._shots_fired * 100
                    if self._shots_fired else 0)
        print(f"\n  Player : {self._name}")
        print(f"  Shots  : {self._shots_fired}")
        print(f"  Hits   : {self._hits}")
        print(f"  Accuracy: {accuracy:.1f}%")


class AIPlayer(Player):
    """
    Computer player – overrides choose_target (POLYMORPHISM).
    Adds a smarter 'hunt' mode after a hit.
    """

    def __init__(self, name: str = "Computer"):
        super().__init__(name)
        self._fired_at = set()
        self._hunt_queue = []    # squares to try after a hit

    def choose_target(self, board: Board) -> tuple:
        """
        POLYMORPHISM: AI strategy instead of human input.
        Hunt mode: after a hit, tries adjacent squares first.
        """
        while self._hunt_queue:
            row, col = self._hunt_queue.pop(0)
            if (row, col) not in self._fired_at:
                self._fired_at.add((row, col))
                return row, col

        # Random untried square
        while True:
            row = random.randint(0, Grid.SIZE - 1)
            col = random.randint(0, Grid.SIZE - 1)
            if (row, col) not in self._fired_at:
                self._fired_at.add((row, col))
                return row, col

    def notify_hit(self, row: int, col: int):
        """Queue adjacent squares for hunt mode."""
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if (0 <= nr < Grid.SIZE and 0 <= nc < Grid.SIZE
                    and (nr, nc) not in self._fired_at):
                self._hunt_queue.append((nr, nc))

    def display_info(self):
        print(f"  [AI] ", end="")
        super().display_info()


# ─────────────────────────────────────────────
# FILE I/O – CSV save / load
# ─────────────────────────────────────────────

class GameStats:
    """
    Handles saving and loading game statistics to/from CSV.
    Demonstrates file reading and writing requirement.
    """

    FILENAME = "game_stats.csv"
    FIELDNAMES = ["winner", "loser", "winner_shots", "loser_shots",
                  "winner_accuracy", "loser_accuracy"]

    @classmethod
    def save(cls, winner: Player, loser: Player):
        """Append one game result row to CSV."""
        file_exists = os.path.isfile(cls.FILENAME)
        w_acc = (winner.hits / winner.shots_fired * 100
                 if winner.shots_fired else 0)
        l_acc = (loser.hits / loser.shots_fired * 100
                 if loser.shots_fired else 0)

        with open(cls.FILENAME, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cls.FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "winner": winner.get_name(),
                "loser": loser.get_name(),
                "winner_shots": winner.shots_fired,
                "loser_shots": loser.shots_fired,
                "winner_accuracy": f"{w_acc:.1f}",
                "loser_accuracy": f"{l_acc:.1f}",
            })
        print(f"\n  ✔  Stats saved to '{cls.FILENAME}'")

    @classmethod
    def load_and_display(cls):
        """Read and print all saved game results."""
        if not os.path.isfile(cls.FILENAME):
            print("  No saved stats found.")
            return
        with open(cls.FILENAME, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            print("  Stats file is empty.")
            return

        print(f"\n{'─'*50}")
        print("  GAME HISTORY")
        print(f"{'─'*50}")
        for i, row in enumerate(rows, 1):
            print(f"  Game {i}: {row['winner']} beat {row['loser']} "
                  f"| {row['winner_shots']} vs {row['loser_shots']} shots "
                  f"| accuracy {row['winner_accuracy']}% vs "
                  f"{row['loser_accuracy']}%")
        print(f"{'─'*50}")


# ─────────────────────────────────────────────
# GAME ENGINE
# ─────────────────────────────────────────────

class BattleshipGame:
    """
    Orchestrates the full game loop.
    Aggregates two Player objects.
    """

    def __init__(self, player1: Player, player2: Player):
        self._player1 = player1   # aggregation
        self._player2 = player2   # aggregation

    def _setup_fleet_random(self, player: Player):
        """Place the standard fleet randomly on a player's board."""
        fleet = ShipFactory.fleet()
        for ship in fleet:
            ok = player.board.place_ship_randomly(ship)
            if not ok:
                print(f"  Warning: could not place {ship.name}")

    def _setup_fleet_manual(self, player: Player):
        """
        Let a human player place each ship interactively.
        Shows the board after every placement.
        """
        fleet = ShipFactory.fleet()

        print(f"\n{'═'*40}")
        print(f"  Place your fleet, {player.get_name()}!")
        print(f"{'═'*40}")
        print("  Grid is 10×10  (rows 0-9, cols 0-9)")
        print("  H = horizontal (extends right)")
        print("  V = vertical   (extends downward)\n")

        for ship in fleet:
            while True:
                # Show current board state
                print(f"\n  Your board so far:")
                player.board.display_grid(reveal=True)
                print(f"\n  Placing: {ship.name}  (size {ship.size}, "
                      f"symbol '{ship.symbol}')")

                # Get row
                try:
                    row = int(input("  Row (0-9): ").strip())
                    col = int(input("  Col (0-9): ").strip())
                    direction = input("  Direction (H/V): ").strip().upper()

                    if direction not in ("H", "V"):
                        print("  Please enter H or V.")
                        continue

                    horizontal = (direction == "H")
                    ok = player.board.add_ship(ship, row, col, horizontal)

                    if ok:
                        print(f"  ✔ {ship.name} placed!")
                        break
                    else:
                        print("  ✘ Invalid position (out of bounds or overlap). "
                              "Try again.")
                except ValueError:
                    print("  Please enter numbers for row and col.")

    def _take_turn(self, attacker: Player, defender: Player):
        """One player fires at the other's board."""
        is_ai = isinstance(attacker, AIPlayer)

        print(f"\n{'─'*40}")
        print(f"  {attacker.get_name()}'s turn")

        if not is_ai:
            print("\n  Opponent's board (your shots):")
            defender.board.display_grid(reveal=False)

        row, col = attacker.choose_target(defender.board)

        if is_ai:
            print(f"  {attacker.get_name()} fires at ({row}, {col})")

        result = defender.board.receive_shot(row, col)

        if result == "already_shot":
            print("  Already fired there! Turn wasted.")
        elif result == "miss":
            print("  Miss!")
        elif result == "hit":
            print("  HIT!")
            if is_ai:
                attacker.notify_hit(row, col)
        elif result == "sunk":
            print("  SHIP SUNK!")
            if is_ai:
                attacker.notify_hit(row, col)

        attacker.record_shot(result)

    def _check_winner(self, attacker: Player, defender: Player) -> bool:
        if defender.board.all_sunk:
            print(f"\n{'★'*40}")
            print(f"  {attacker.get_name()} WINS! All enemy ships sunk!")
            print(f"{'★'*40}")
            attacker.display_info()
            defender.display_info()
            GameStats.save(attacker, defender)
            return True
        return False

    def run(self):
        """Main game loop."""
        print("\n" + "=" * 40)
        print("       BATTLESHIP  ⚓")
        print("=" * 40)

        # Give human players the choice of manual or random placement
        for player in (self._player1, self._player2):
            if isinstance(player, AIPlayer):
                self._setup_fleet_random(player)
            else:
                print(f"\n  How would you like to place your ships, "
                      f"{player.get_name()}?")
                print("  1. Place them manually")
                print("  2. Place them randomly")
                choice = input("  Choice: ").strip()
                if choice == "1":
                    self._setup_fleet_manual(player)
                else:
                    self._setup_fleet_random(player)
                    print(f"\n  {player.get_name()}'s fleet placed randomly.")
                    player.board.display_grid(reveal=True)

        print("\n  Fleets deployed. Battle begins!\n")

        players = [self._player1, self._player2]
        turn = 0

        while True:
            attacker = players[turn % 2]
            defender = players[(turn + 1) % 2]

            self._take_turn(attacker, defender)
            if self._check_winner(attacker, defender):
                break

            turn += 1

        # Show final boards
        print("\n  Your fleet:")
        self._player1.board.display_grid(reveal=True)
        print("\n  Enemy fleet:")
        self._player2.board.display_grid(reveal=True)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    print("\n  1. Player vs Computer")
    print("  2. View game history")
    print("  3. Computer vs Computer (demo)")
    choice = input("\n  Choose option: ").strip()

    if choice == "1":
        name = input("  Enter your name: ").strip() or "Player"
        human = Player(name)
        ai = AIPlayer()
        BattleshipGame(human, ai).run()

    elif choice == "2":
        GameStats.load_and_display()

    elif choice == "3":
        ai1 = AIPlayer("Alpha")
        ai2 = AIPlayer("Beta")
        BattleshipGame(ai1, ai2).run()

    else:
        print("  Invalid option.")


if __name__ == "__main__":
    main()
