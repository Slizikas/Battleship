"""
Unit tests for the Battleship game (OOP Coursework 2026).
Covers all core functionality using the unittest framework.
Run with:  python -m unittest test_battleship -v
"""

import csv
import io
import os
import sys
import unittest
from unittest.mock import patch

from battleship import (
    AIPlayer,
    Battleship,
    Board,
    BattleshipGame,
    Carrier,
    Cruiser,
    Destroyer,
    GameStats,
    GameObject,
    Grid,
    Player,
    Ship,
    ShipFactory,
    Submarine,
)


# ─────────────────────────────────────────────
# Ship
# ─────────────────────────────────────────────

class TestShip(unittest.TestCase):
    """Tests for the Ship base class."""

    def setUp(self):
        self.destroyer = ShipFactory.create("destroyer")   # size 2
        self.carrier   = ShipFactory.create("carrier")     # size 5

    # initial state
    def test_initial_hits_are_zero(self):
        self.assertEqual(self.destroyer.hits, 0)

    def test_not_sunk_initially(self):
        self.assertFalse(self.destroyer.is_sunk)

    # hit counting
    def test_register_hit_increments_hits(self):
        self.destroyer.register_hit()
        self.assertEqual(self.destroyer.hits, 1)

    def test_sunk_when_hits_reach_size(self):
        for _ in range(self.destroyer.size):
            self.destroyer.register_hit()
        self.assertTrue(self.destroyer.is_sunk)

    def test_hits_do_not_exceed_size_after_sinking(self):
        for _ in range(self.destroyer.size + 10):
            self.destroyer.register_hit()
        self.assertEqual(self.destroyer.hits, self.destroyer.size)

    # properties
    def test_carrier_size_is_five(self):
        self.assertEqual(self.carrier.size, 5)

    def test_destroyer_size_is_two(self):
        self.assertEqual(self.destroyer.size, 2)

    def test_carrier_symbol(self):
        self.assertEqual(self.carrier.symbol, "C")

    def test_destroyer_symbol(self):
        self.assertEqual(self.destroyer.symbol, "D")

    # positions
    def test_add_position_stores_tuple(self):
        self.destroyer.add_position(3, 4)
        self.assertIn((3, 4), self.destroyer.positions)

    def test_positions_returns_defensive_copy(self):
        self.destroyer.add_position(1, 1)
        copy = self.destroyer.positions
        copy.append((9, 9))
        self.assertNotIn((9, 9), self.destroyer.positions)


# ─────────────────────────────────────────────
# Concrete ship subclasses
# ─────────────────────────────────────────────

class TestConcreteShips(unittest.TestCase):
    """Verify each concrete ship has the correct size and inherits from Ship."""

    def test_carrier_is_ship(self):
        self.assertIsInstance(Carrier(), Ship)

    def test_battleship_size(self):
        self.assertEqual(Battleship().size, 4)

    def test_cruiser_size(self):
        self.assertEqual(Cruiser().size, 3)

    def test_submarine_size(self):
        self.assertEqual(Submarine().size, 3)

    def test_destroyer_size(self):
        self.assertEqual(Destroyer().size, 2)

    def test_carrier_overrides_display_info(self):
        carrier = Carrier()
        try:
            carrier.display_info()
        except Exception as exc:
            self.fail(f"Carrier.display_info raised: {exc}")


# ─────────────────────────────────────────────
# ShipFactory – Factory Method pattern
# ─────────────────────────────────────────────

class TestShipFactory(unittest.TestCase):
    """Tests for the Factory Method pattern."""

    def test_create_carrier(self):
        self.assertIsInstance(ShipFactory.create("carrier"), Carrier)

    def test_create_battleship(self):
        self.assertIsInstance(ShipFactory.create("battleship"), Battleship)

    def test_create_cruiser(self):
        self.assertIsInstance(ShipFactory.create("cruiser"), Cruiser)

    def test_create_submarine(self):
        self.assertIsInstance(ShipFactory.create("submarine"), Submarine)

    def test_create_destroyer(self):
        self.assertIsInstance(ShipFactory.create("destroyer"), Destroyer)

    def test_create_is_case_insensitive(self):
        self.assertIsInstance(ShipFactory.create("CARRIER"), Carrier)
        self.assertIsInstance(ShipFactory.create("Destroyer"), Destroyer)

    def test_unknown_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            ShipFactory.create("ghost_ship")

    def test_fleet_returns_five_ships(self):
        self.assertEqual(len(ShipFactory.fleet()), 5)

    def test_fleet_all_are_ship_instances(self):
        self.assertTrue(all(isinstance(s, Ship) for s in ShipFactory.fleet()))

    def test_fleet_returns_new_instances_each_call(self):
        fleet_a = ShipFactory.fleet()
        fleet_b = ShipFactory.fleet()
        self.assertIsNot(fleet_a[0], fleet_b[0])


# ─────────────────────────────────────────────
# Grid
# ─────────────────────────────────────────────

class TestGrid(unittest.TestCase):
    """Tests for the Grid class."""

    def setUp(self):
        self.grid = Grid()

    def test_size_constant_is_ten(self):
        self.assertEqual(Grid.SIZE, 10)

    def test_all_cells_empty_on_init(self):
        for r in range(Grid.SIZE):
            for c in range(Grid.SIZE):
                self.assertEqual(self.grid.get(r, c), Grid.EMPTY)

    def test_set_then_get_returns_value(self):
        self.grid.set(0, 0, Grid.HIT)
        self.assertEqual(self.grid.get(0, 0), Grid.HIT)

    def test_set_miss_marker(self):
        self.grid.set(5, 5, Grid.MISS)
        self.assertEqual(self.grid.get(5, 5), Grid.MISS)

    def test_set_does_not_affect_other_cells(self):
        self.grid.set(3, 3, Grid.HIT)
        self.assertEqual(self.grid.get(3, 4), Grid.EMPTY)


# ─────────────────────────────────────────────
# Board
# ─────────────────────────────────────────────

class TestBoard(unittest.TestCase):
    """Tests for the Board class."""

    def setUp(self):
        self.board     = Board("Alice")
        self.destroyer = ShipFactory.create("destroyer")   # size 2

    # properties
    def test_owner_property(self):
        self.assertEqual(self.board.owner, "Alice")

    def test_ships_empty_on_init(self):
        self.assertEqual(len(self.board.ships), 0)

    def test_all_sunk_vacuously_true_on_empty_board(self):
        self.assertTrue(self.board.all_sunk)

    # add_ship – valid placements
    def test_add_ship_horizontal_returns_true(self):
        self.assertTrue(self.board.add_ship(self.destroyer, 0, 0, horizontal=True))

    def test_add_ship_vertical_returns_true(self):
        ship = ShipFactory.create("destroyer")
        self.assertTrue(self.board.add_ship(ship, 0, 0, horizontal=False))

    def test_add_ship_appends_to_ships_list(self):
        self.board.add_ship(self.destroyer, 0, 0, horizontal=True)
        self.assertEqual(len(self.board.ships), 1)

    def test_add_ship_sets_positions_on_ship(self):
        self.board.add_ship(self.destroyer, 2, 3, horizontal=True)
        self.assertIn((2, 3), self.destroyer.positions)
        self.assertIn((2, 4), self.destroyer.positions)

    # add_ship – invalid placements
    def test_add_ship_out_of_bounds_horizontal(self):
        self.assertFalse(self.board.add_ship(self.destroyer, 0, 9, horizontal=True))

    def test_add_ship_out_of_bounds_vertical(self):
        self.assertFalse(self.board.add_ship(self.destroyer, 9, 0, horizontal=False))

    def test_add_ship_overlap_fails(self):
        ship2 = ShipFactory.create("destroyer")
        self.board.add_ship(self.destroyer, 0, 0, horizontal=True)
        self.assertFalse(self.board.add_ship(ship2, 0, 0, horizontal=True))

    def test_add_ship_adjacent_allowed(self):
        ship2 = ShipFactory.create("destroyer")
        self.board.add_ship(self.destroyer, 0, 0, horizontal=True)
        self.assertTrue(self.board.add_ship(ship2, 1, 0, horizontal=True))

    # place_ship_randomly
    def test_place_ship_randomly_succeeds(self):
        self.assertTrue(self.board.place_ship_randomly(ShipFactory.create("carrier")))

    def test_place_ship_randomly_adds_to_ships(self):
        self.board.place_ship_randomly(ShipFactory.create("submarine"))
        self.assertEqual(len(self.board.ships), 1)

    # receive_shot
    def test_receive_shot_miss(self):
        self.assertEqual(self.board.receive_shot(5, 5), "miss")

    def test_receive_shot_hit(self):
        self.board.add_ship(self.destroyer, 3, 3, horizontal=True)
        result = self.board.receive_shot(3, 3)
        self.assertIn(result, ("hit", "sunk"))

    def test_receive_shot_sunk(self):
        self.board.add_ship(self.destroyer, 3, 3, horizontal=True)
        self.board.receive_shot(3, 3)
        self.assertEqual(self.board.receive_shot(3, 4), "sunk")

    def test_receive_shot_already_shot(self):
        self.board.receive_shot(0, 0)
        self.assertEqual(self.board.receive_shot(0, 0), "already_shot")

    # all_sunk
    def test_all_sunk_false_with_live_ship(self):
        self.board.add_ship(self.destroyer, 0, 0, horizontal=True)
        self.assertFalse(self.board.all_sunk)

    def test_all_sunk_true_after_all_ships_destroyed(self):
        self.board.add_ship(self.destroyer, 0, 0, horizontal=True)
        self.board.receive_shot(0, 0)
        self.board.receive_shot(0, 1)
        self.assertTrue(self.board.all_sunk)

    # defensive copy
    def test_ships_property_returns_copy(self):
        self.board.add_ship(self.destroyer, 0, 0, horizontal=True)
        ships_copy = self.board.ships
        ships_copy.clear()
        self.assertEqual(len(self.board.ships), 1)


# ─────────────────────────────────────────────
# Player
# ─────────────────────────────────────────────

class TestPlayer(unittest.TestCase):
    """Tests for the human Player class."""

    def setUp(self):
        self.player = Player("Alice")

    def test_get_name(self):
        self.assertEqual(self.player.get_name(), "Alice")

    def test_name_property(self):
        self.assertEqual(self.player.name, "Alice")

    def test_shots_fired_zero_on_init(self):
        self.assertEqual(self.player.shots_fired, 0)

    def test_hits_zero_on_init(self):
        self.assertEqual(self.player.hits, 0)

    def test_record_hit_increments_both_counters(self):
        self.player.record_shot("hit")
        self.assertEqual(self.player.shots_fired, 1)
        self.assertEqual(self.player.hits, 1)

    def test_record_sunk_counts_as_hit(self):
        self.player.record_shot("sunk")
        self.assertEqual(self.player.hits, 1)

    def test_record_miss_does_not_increment_hits(self):
        self.player.record_shot("miss")
        self.assertEqual(self.player.shots_fired, 1)
        self.assertEqual(self.player.hits, 0)

    def test_record_multiple_shots(self):
        for result in ("hit", "miss", "hit", "sunk", "miss"):
            self.player.record_shot(result)
        self.assertEqual(self.player.shots_fired, 5)
        self.assertEqual(self.player.hits, 3)

    def test_board_owner_matches_player_name(self):
        self.assertEqual(self.player.board.owner, "Alice")

    def test_choose_target_valid_input(self):
        board = Board("Opponent")
        with patch("builtins.input", side_effect=["3 7"]):
            self.assertEqual(self.player.choose_target(board), (3, 7))

    def test_choose_target_rejects_out_of_range_then_accepts(self):
        board = Board("Opponent")
        with patch("builtins.input", side_effect=["10 10", "0 0"]):
            self.assertEqual(self.player.choose_target(board), (0, 0))

    def test_choose_target_rejects_non_numeric_then_accepts(self):
        board = Board("Opponent")
        with patch("builtins.input", side_effect=["abc", "5 5"]):
            self.assertEqual(self.player.choose_target(board), (5, 5))


# ─────────────────────────────────────────────
# AIPlayer
# ─────────────────────────────────────────────

class TestAIPlayer(unittest.TestCase):
    """Tests for the AIPlayer subclass."""

    def setUp(self):
        self.ai = AIPlayer("Bot")

    def test_ai_is_player_subclass(self):
        self.assertIsInstance(self.ai, Player)

    def test_get_name(self):
        self.assertEqual(self.ai.get_name(), "Bot")

    def test_default_name_is_computer(self):
        self.assertEqual(AIPlayer().get_name(), "Computer")

    def test_choose_target_returns_valid_coords(self):
        board = Board("Target")
        row, col = self.ai.choose_target(board)
        self.assertTrue(0 <= row < Grid.SIZE)
        self.assertTrue(0 <= col < Grid.SIZE)

    def test_choose_target_never_repeats_square(self):
        board = Board("Target")
        seen = set()
        for _ in range(60):
            pos = self.ai.choose_target(board)
            self.assertNotIn(pos, seen, f"AI repeated square {pos}")
            seen.add(pos)

    def test_choose_target_does_not_call_input(self):
        board = Board("Target")
        with patch("builtins.input", side_effect=AssertionError("input called")):
            row, col = self.ai.choose_target(board)
        self.assertTrue(0 <= row < Grid.SIZE)

    def test_notify_hit_queues_adjacent_squares(self):
        self.ai.notify_hit(5, 5)
        for expected in [(4, 5), (6, 5), (5, 4), (5, 6)]:
            self.assertIn(expected, self.ai._hunt_queue)

    def test_notify_hit_on_corner_skips_out_of_bounds(self):
        self.ai.notify_hit(0, 0)
        for r, c in self.ai._hunt_queue:
            self.assertTrue(0 <= r < Grid.SIZE)
            self.assertTrue(0 <= c < Grid.SIZE)

    def test_hunt_queue_fired_before_random_targets(self):
        self.ai.notify_hit(5, 5)
        board = Board("Target")
        targets = [self.ai.choose_target(board) for _ in range(4)]
        adjacent = {(4, 5), (6, 5), (5, 4), (5, 6)}
        for sq in adjacent:
            self.assertIn(sq, targets)


# ─────────────────────────────────────────────
# GameStats – file I/O
# ─────────────────────────────────────────────

class TestGameStats(unittest.TestCase):
    """Tests for CSV reading and writing."""

    TEST_FILE = "test_stats_tmp.csv"

    def setUp(self):
        GameStats.FILENAME = self.TEST_FILE
        if os.path.isfile(self.TEST_FILE):
            os.remove(self.TEST_FILE)

    def tearDown(self):
        if os.path.isfile(self.TEST_FILE):
            os.remove(self.TEST_FILE)
        GameStats.FILENAME = "game_stats.csv"

    def _make_players(self, w_name="Win", l_name="Lose"):
        winner = Player(w_name)
        loser  = Player(l_name)
        winner.record_shot("hit")
        loser.record_shot("miss")
        return winner, loser

    def test_save_creates_csv_file(self):
        GameStats.save(*self._make_players())
        self.assertTrue(os.path.isfile(self.TEST_FILE))

    def test_saved_row_has_correct_winner(self):
        GameStats.save(*self._make_players("Alice", "Bob"))
        with open(self.TEST_FILE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["winner"], "Alice")

    def test_saved_row_has_correct_loser(self):
        GameStats.save(*self._make_players("Alice", "Bob"))
        with open(self.TEST_FILE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["loser"], "Bob")

    def test_saved_row_has_shot_counts(self):
        GameStats.save(*self._make_players())
        with open(self.TEST_FILE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(int(rows[0]["winner_shots"]), 1)
        self.assertEqual(int(rows[0]["loser_shots"]),  1)

    def test_saved_row_has_accuracy_fields(self):
        GameStats.save(*self._make_players())
        with open(self.TEST_FILE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertIn("winner_accuracy", rows[0])
        self.assertIn("loser_accuracy",  rows[0])

    def test_multiple_saves_all_appended(self):
        for i in range(4):
            GameStats.save(*self._make_players(f"W{i}", f"L{i}"))
        with open(self.TEST_FILE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 4)

    def test_load_does_not_raise_when_file_exists(self):
        GameStats.save(*self._make_players())
        try:
            GameStats.load_and_display()
        except Exception as exc:
            self.fail(f"load_and_display raised: {exc}")

    def test_load_handles_missing_file_gracefully(self):
        try:
            GameStats.load_and_display()
        except Exception as exc:
            self.fail(f"load_and_display raised on missing file: {exc}")


# ─────────────────────────────────────────────
# BattleshipGame – fleet setup helpers
# ─────────────────────────────────────────────

class TestBattleshipGameSetup(unittest.TestCase):
    """Tests for the fleet setup methods in BattleshipGame."""

    def setUp(self):
        self.human = Player("Human")
        self.ai    = AIPlayer("Bot")
        self.game  = BattleshipGame(self.human, self.ai)

    def test_setup_fleet_random_places_five_ships_for_human(self):
        self.game._setup_fleet_random(self.human)
        self.assertEqual(len(self.human.board.ships), 5)

    def test_setup_fleet_random_places_five_ships_for_ai(self):
        self.game._setup_fleet_random(self.ai)
        self.assertEqual(len(self.ai.board.ships), 5)

    def test_setup_fleet_manual_places_five_ships(self):
        # Place each of the 5 ships horizontally, one per row
        inputs = []
        for row in range(5):
            inputs += [str(row), "0", "H"]
        with patch("builtins.input", side_effect=inputs):
            self.game._setup_fleet_manual(self.human)
        self.assertEqual(len(self.human.board.ships), 5)

    def test_setup_fleet_manual_retries_on_invalid_input(self):
        # First Carrier placement at col 9 is out-of-bounds; second at col 0 is valid
        inputs = [
            "0", "9", "H",   # invalid – Carrier(5) won't fit
            "0", "0", "H",   # valid Carrier
            "1", "0", "H",   # Battleship
            "2", "0", "H",   # Cruiser
            "3", "0", "H",   # Submarine
            "4", "0", "H",   # Destroyer
        ]
        with patch("builtins.input", side_effect=inputs):
            self.game._setup_fleet_manual(self.human)
        self.assertEqual(len(self.human.board.ships), 5)

    def test_setup_fleet_manual_retries_on_non_numeric_input(self):
        inputs = [
            "abc", "0", "0", "H",   # bad row, then valid Carrier
            "1", "0", "H",
            "2", "0", "H",
            "3", "0", "H",
            "4", "0", "H",
        ]
        with patch("builtins.input", side_effect=inputs):
            self.game._setup_fleet_manual(self.human)
        self.assertEqual(len(self.human.board.ships), 5)


# ─────────────────────────────────────────────
# Polymorphism
# ─────────────────────────────────────────────

class TestPolymorphism(unittest.TestCase):
    """Verify polymorphic behaviour across the class hierarchy."""

    def test_display_info_callable_on_all_game_objects(self):
        objects = [Carrier(), Battleship(), Destroyer(), Board("P"),
                   Player("P"), AIPlayer()]
        for obj in objects:
            with self.subTest(cls=type(obj).__name__):
                try:
                    obj.display_info()
                except Exception as exc:
                    self.fail(f"display_info raised {exc} on {type(obj).__name__}")

    def test_all_concrete_objects_are_game_object_instances(self):
        for obj in [Carrier(), Board("P"), Player("P"), AIPlayer()]:
            with self.subTest(cls=type(obj).__name__):
                self.assertIsInstance(obj, GameObject)

    def test_ai_choose_target_returns_tuple_of_two_ints(self):
        result = AIPlayer().choose_target(Board("T"))
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_carrier_display_info_includes_star(self):
        captured = io.StringIO()
        sys.stdout = captured
        try:
            Carrier().display_info()
        finally:
            sys.stdout = sys.__stdout__
        self.assertIn("★", captured.getvalue())


# ─────────────────────────────────────────────
# Encapsulation – read-only properties
# ─────────────────────────────────────────────

class TestEncapsulation(unittest.TestCase):
    """Verify that encapsulated attributes cannot be set from outside."""

    def test_ship_name_is_read_only(self):
        with self.assertRaises(AttributeError):
            Destroyer().name = "Hacked"

    def test_ship_size_is_read_only(self):
        with self.assertRaises(AttributeError):
            Destroyer().size = 99

    def test_ship_hits_is_read_only(self):
        with self.assertRaises(AttributeError):
            Destroyer().hits = 99

    def test_board_owner_is_read_only(self):
        with self.assertRaises(AttributeError):
            Board("Alice").owner = "Hacked"

    def test_player_name_is_read_only(self):
        with self.assertRaises(AttributeError):
            Player("Alice").name = "Hacked"

    def test_player_shots_fired_is_read_only(self):
        with self.assertRaises(AttributeError):
            Player("Alice").shots_fired = 99


if __name__ == "__main__":
    unittest.main()
