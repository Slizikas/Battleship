# Battleship Game – OOP Coursework Report

---

## 1. Introduction

### What is the application?

It's a terminal Battleship game. Two players each get a 10×10 grid and five ships. They take turns guessing coordinates, and the first to sink all of the opponent's ships wins.

There are three options in the main menu:

- Player vs Computer
- View past game results
- Computer vs Computer (mostly just to watch the AI play itself)

### How to run

```bash
git clone <your-github-url>
cd battleship
python battleship.py

# to run tests:
python -m unittest test_battleship -v
```

### How to use

Pick an option from the menu. If you go with Player vs Computer, you enter your name and choose whether to place ships manually or let the program place them randomly.

Manual placement shows your board after each ship and asks for a row (0–9), column (0–9), and direction – H for horizontal or V for vertical. If something is out of bounds or overlaps another ship, it rejects it and asks again.

During the game your opponent's board is shown each turn. Dots are unknown squares, X is a hit, O is a miss. Type two numbers like `3 7` to fire. Results are saved to `game_stats.csv` when the game ends.

---

## 2. Body / Analysis

### 2.1 Abstraction

I used two abstract base classes to define what every game object and every player has to be able to do, without saying how they do it.

```python
from abc import ABC, abstractmethod

class GameObject(ABC):
    @abstractmethod
    def display_info(self):
        pass

class AbstractPlayer(ABC):
    @abstractmethod
    def choose_target(self, board) -> tuple:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass
```

`GameObject` just means anything in the game can describe itself. `AbstractPlayer` means any player has a name and a way to pick a target. The game loop calls `choose_target` without caring if it's a human or AI – both work the same from the outside.

---

### 2.2 Encapsulation

All attributes use a `_` prefix to mark them as private, and they're only readable through properties. Outside code can read values but can't overwrite them.

```python
class Ship(GameObject):
    def __init__(self, name: str, size: int, symbol: str):
        self._name      = name
        self._size      = size
        self._hits      = 0
        self._positions = []

    @property
    def is_sunk(self) -> bool:
        return self._hits >= self._size

    def register_hit(self):
        if not self.is_sunk:
            self._hits += 1
```

`is_sunk` is calculated from `_hits` and `_size` and has no setter, so you can't set it directly. The only way to change a ship's state is `register_hit`, which also stops the hit count from going past the ship's size.

`positions` returns a copy of the internal list so nothing outside can change where the ship actually is:

```python
@property
def positions(self) -> list:
    return list(self._positions)
```

---

### 2.3 Inheritance

**Ship hierarchy:**

```
Ship
├── Carrier      (size 5)
├── Battleship   (size 4)
├── Cruiser      (size 3)
├── Submarine    (size 3)
└── Destroyer    (size 2)
```

Each ship just calls `super().__init__` with its own values. `Carrier` also overrides `display_info` to print a star in front of it:

```python
class Carrier(Ship):
    def __init__(self):
        super().__init__("Carrier", 5, "C")

    def display_info(self):
        print("  ★ ", end="")
        super().display_info()
```

**Player hierarchy:**

```
AbstractPlayer
└── Player          (human, uses input())
    └── AIPlayer    (overrides choose_target)
```

`Player` inherits from both `AbstractPlayer` and `GameObject`. `AIPlayer` gets everything from `Player` – the name, shot tracking, the board – and only changes how it picks a target:

```python
class AIPlayer(Player):
    def __init__(self, name: str = "Computer"):
        super().__init__(name)
        self._fired_at   = set()
        self._hunt_queue = []

    def choose_target(self, board: Board) -> tuple:
        while self._hunt_queue:
            row, col = self._hunt_queue.pop(0)
            if (row, col) not in self._fired_at:
                self._fired_at.add((row, col))
                return row, col
        while True:
            row = random.randint(0, Grid.SIZE - 1)
            col = random.randint(0, Grid.SIZE - 1)
            if (row, col) not in self._fired_at:
                self._fired_at.add((row, col))
                return row, col
```

---

### 2.4 Polymorphism

The game loop calls `choose_target` and `display_info` on both player types without any `isinstance` checks. Python picks the right version at runtime.

```python
# same line, works for both Player and AIPlayer
row, col = attacker.choose_target(defender.board)
```

For a human this opens an input prompt. For the AI it runs the hunt logic. The game loop doesn't know or care which one it's dealing with.

Same idea with `display_info` – `Carrier`, `Battleship`, `Player`, `AIPlayer` all have their own version but get called identically.

---

### 2.5 Design Pattern – Factory Method

`ShipFactory` is where all ship objects get created. Nothing else in the code calls `Carrier()` or `Destroyer()` directly.

```python
class ShipFactory:
    _registry = {
        "carrier":    Carrier,
        "battleship": Battleship,
        "cruiser":    Cruiser,
        "submarine":  Submarine,
        "destroyer":  Destroyer,
    }

    @classmethod
    def create(cls, ship_type: str) -> Ship:
        key = ship_type.lower()
        if key not in cls._registry:
            raise ValueError(f"Unknown ship type: '{ship_type}'")
        return cls._registry[key]()

    @classmethod
    def fleet(cls) -> list:
        return [cls.create(t) for t in cls._registry]
```

I went with Factory Method because there are multiple ship types that get created in different parts of the code, and keeping it in one place means adding a new ship is just one new class and one line in the dictionary. Singleton doesn't apply since there are many ship instances. Builder would be overkill for something this simple. Prototype would only be useful if I was cloning existing ships.

---

### 2.6 Composition and Aggregation

**Composition** – `Board` creates its own `Grid` inside `__init__`, and `Player` creates its own `Board`. These objects only exist as part of their owner.

```python
class Board(GameObject):
    def __init__(self, owner_name: str):
        self._grid = Grid()   # Grid only exists inside Board

class Player(AbstractPlayer, GameObject):
    def __init__(self, name: str):
        self._board = Board(name)   # Board only exists inside Player
```

**Aggregation** – `Board` holds ship objects that were made by `ShipFactory` and handed to it. `BattleshipGame` holds players that were created in `main()`. These objects exist on their own, independent of whatever is holding a reference to them.

```python
class BattleshipGame:
    def __init__(self, player1: Player, player2: Player):
        self._player1 = player1   # created outside, just referenced here
        self._player2 = player2
```

---

### 2.7 Reading and Writing to File

After every game the result gets saved to `game_stats.csv` using Python's `csv` module. The file opens in append mode so nothing gets overwritten.

```python
class GameStats:
    FILENAME   = "game_stats.csv"
    FIELDNAMES = ["winner", "loser", "winner_shots", "loser_shots",
                  "winner_accuracy", "loser_accuracy"]

    @classmethod
    def save(cls, winner: Player, loser: Player):
        file_exists = os.path.isfile(cls.FILENAME)
        with open(cls.FILENAME, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cls.FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "winner":          winner.get_name(),
                "winner_shots":    winner.shots_fired,
                "winner_accuracy": f"{winner.hits / winner.shots_fired * 100:.1f}",
                # loser fields follow the same pattern
            })

    @classmethod
    def load_and_display(cls):
        with open(cls.FILENAME, "r", encoding="utf-8") as f:
            for i, row in enumerate(csv.DictReader(f), 1):
                print(f"  Game {i}: {row['winner']} beat {row['loser']} ...")
```

---

### 2.8 Manual Ship Placement

Before the game starts the player can place ships manually or randomly. Manual mode shows the board after each ship and keeps asking until a valid position is entered. It catches three kinds of bad input: going off the grid, overlapping another ship, and typing something that isn't a number.

```python
def _setup_fleet_manual(self, player: Player):
    fleet = ShipFactory.fleet()
    for ship in fleet:
        while True:
            player.board.display_grid(reveal=True)
            print(f"\n  Placing: {ship.name}  (size {ship.size})")
            try:
                row       = int(input("  Row (0-9): ").strip())
                col       = int(input("  Col (0-9): ").strip())
                direction = input("  Direction (H/V): ").strip().upper()
                if direction not in ("H", "V"):
                    print("  Please enter H or V.")
                    continue
                if player.board.add_ship(ship, row, col, direction == "H"):
                    print(f"  ✔ {ship.name} placed!")
                    break
                print("  ✘ Invalid position. Try again.")
            except ValueError:
                print("  Please enter numbers for row and col.")
```

---

### 2.9 Testing

96 unit tests across 11 test classes. Methods that use `input()` like `choose_target` and `_setup_fleet_manual` are tested with `unittest.mock.patch` so the tests can run without any keyboard input.

| Test class | What it covers |
|---|---|
| `TestShip` | Hit counting, sunk detection, position storage, defensive copy |
| `TestConcreteShips` | Correct size and inheritance for all 5 ship types |
| `TestShipFactory` | Creating each type, case insensitivity, unknown type error, fleet |
| `TestGrid` | Initial state, get/set, cell isolation |
| `TestBoard` | Placing ships (valid, out of bounds, overlap, adjacent), shots, all-sunk |
| `TestPlayer` | Name, shot tracking, input parsing, rejection of bad input |
| `TestAIPlayer` | No repeated squares, hunt queue, corner edge case, no input() calls |
| `TestGameStats` | File creation, CSV contents, multiple appends, missing file |
| `TestBattleshipGameSetup` | Random fleet, manual fleet, retries on bad input |
| `TestPolymorphism` | display_info works on all types, AI targeting doesn't call input() |
| `TestEncapsulation` | Every read-only property raises AttributeError on assignment |

```bash
python -m unittest test_battleship -v
# Ran 96 tests in 0.029s – OK
```

---

## 3. Results and Summary

### Results

- The game works end to end. Both Player vs Computer and Computer vs Computer run correctly, ships get placed, shots are tracked, and the winner is shown with their accuracy at the end.
- Manual ship placement works and handles all three types of bad input without crashing. Adding it meant writing a second setup method in `BattleshipGame` and updating `run()` to ask which the player prefers.
- Factory Method was a good choice for the pattern. Adding a new ship would only mean one new class and one line in the registry – nothing else would need to change.
- I ran into a bug in the AI where it would try to fire at squares it had already shot. The test `test_choose_target_never_repeats_square` caught it and I fixed it by checking `_fired_at` before popping from the hunt queue.
- Game history saves and loads correctly across multiple sessions.

### Conclusions

The goal was to use OOP in a way that actually makes the code better, not just to tick boxes. I think it mostly worked. The abstract classes are useful because the game loop genuinely doesn't need to know if it's talking to a human or an AI. Encapsulation helped a few times during development when I noticed I was about to accidentally modify internal state. Inheritance removed a lot of duplicate code between the ship types.

If I were to keep working on it, I'd improve the AI first – right now it's random with a simple hunt mode, but a probability-based approach would make it much harder to beat. I'd also look at replacing the CSV with a SQLite database and maybe add a basic graphical interface so the grid is easier to read.

---

## 4. Resources

- [Python `abc` module](https://docs.python.org/3/library/abc.html)
- [PEP 8](https://pep8.org)
- [Python `unittest`](https://docs.python.org/3/library/unittest.html)
- [Python `unittest.mock`](https://docs.python.org/3/library/unittest.mock.html)
- [Python `csv` module](https://docs.python.org/3/library/csv.html)
- [Refactoring Guru – Factory Method](https://refactoring.guru/design-patterns/factory-method)
- [Markdown syntax](https://www.markdownguide.org/basic-syntax/)
- [Pro Git Book](https://git-scm.com/book/en/v2)
