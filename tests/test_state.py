from automata_based_smt_solver.automata.state import INITIAL_STATE, State


class TestState:
    TEST_ID_1 = 420
    TEST_ID_2 = 123
    TEST_ID_3 = 456

    def test_basic_state_creation(self):
        """Test basic creation of a state."""
        state = State("q1")
        assert state.state_value == "q1"
        assert state.id == -1

        state_with_id = State("q2", self.TEST_ID_1)
        assert state_with_id.state_value == "q2"
        assert state_with_id.id == self.TEST_ID_1

    def test_nested_state_creation(self):
        """Test creating a state from another state."""
        original = State("q3", self.TEST_ID_2)
        nested = State(original)

        # Should extract inner state_value
        assert nested.state_value == "q3"
        # Should preserve ID if not specified
        assert nested.id == self.TEST_ID_2

        # Test with different ID
        overridden = State(original, self.TEST_ID_3)
        assert overridden.state_value == "q3"
        assert overridden.id == self.TEST_ID_3

    def test_equality(self):
        """Test equality comparison between states."""
        state1 = State("q4", 1)
        state2 = State("q4", 1)
        state3 = State("q4", 2)
        state4 = State("q5", 1)

        # Same value, same ID
        assert state1 == state2
        # Same value, different ID
        assert state1 != state3
        # Different value, same ID
        assert state1 != state4
        # Not a state object
        assert state1 != "q4"

    def test_hash_consistency(self):
        """Test hash consistency for state objects."""
        state1 = State("q6", 10)
        state2 = State("q6", 10)
        state3 = State("q6", 20)

        # Same states should have same hash
        assert hash(state1) == hash(state2)
        # Different states should have different hash
        assert hash(state1) != hash(state3)

        # States should be usable as dictionary keys
        state_dict = {state1: "value1", state3: "value3"}
        assert state_dict[state2] == "value1"  # state2 same as state1

    def test_string_representation(self):
        """Test string representation of states."""
        # State with default ID
        state1 = State("q7")
        assert str(state1) == "q7"
        assert repr(state1) == "q7"

        # State with custom ID
        state2 = State("q8", 30)
        assert str(state2) == "q8(30)"
        assert repr(state2) == "q8(30)"

        # Nested state
        nested = State(state2)
        assert str(nested) == "q8(30)"

    def test_initial_state_constant(self):
        """Test the INITIAL_STATE constant."""
        assert INITIAL_STATE.state_value == "q0"
        assert INITIAL_STATE.id == -1

    def test_complex_values(self):
        """Test states with complex objects as values."""
        # Tuple as state value
        tuple_state = State(("q9", "q10"))
        assert tuple_state.state_value == ("q9", "q10")

        # List as state value (note: may not be hashable)
        list_state = State(["q11", "q12"])
        assert list_state.state_value == ["q11", "q12"]

        # Nested state with complex value
        nested = State(tuple_state)
        assert nested.state_value == ("q9", "q10")
