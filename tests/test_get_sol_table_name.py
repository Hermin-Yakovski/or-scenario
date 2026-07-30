"""Isolated test for _get_sol_table_name() helper method - avoids ortools dependency."""

import sys
import types


def test_get_sol_table_name():
    """Test sol table name generation with alphabetical sorting."""
    # Import Dimension from register module
    from or_register import Dimension

    try:
        # Mock the or_algo module to avoid ortools dependency
        mock_or_algo = types.ModuleType("or_algo")

        class MockAlgorithm:
            def solve(self, data):
                pass

        mock_or_algo.Algorithm = MockAlgorithm
        sys.modules["or_algo"] = mock_or_algo

        # Clear any cached or_scenario modules to force reload
        modules_to_clear = [k for k in list(sys.modules.keys()) if k.startswith("or_scenario")]
        for module in modules_to_clear:
            del sys.modules[module]

        # Import Scenario and BaseRequest from or_scenario
        from or_scenario import BaseRequest, Scenario

        # Create scenario instance
        scenario = Scenario(BaseRequest())

        # Single dimension
        result = scenario._get_sol_table_name((Dimension("A", "", ""),))
        assert result == "sol_a", f"Expected 'sol_a', got '{result}'"

        # Two dimensions - should be sorted alphabetically
        result = scenario._get_sol_table_name(
            (Dimension("Zebra", "", ""), Dimension("Apple", "", ""))
        )
        assert result == "sol_apple_zebra", f"Expected 'sol_apple_zebra', got '{result}'"

        # Three dimensions
        result = scenario._get_sol_table_name(
            (Dimension("C", "", ""), Dimension("B", "", ""), Dimension("A", "", ""))
        )
        assert result == "sol_a_b_c", f"Expected 'sol_a_b_c', got '{result}'"

        # Test case sensitivity - should use lowercase
        result = scenario._get_sol_table_name(
            (Dimension("Product", "", ""), Dimension("Region", "", ""))
        )
        assert result == "sol_product_region", f"Expected 'sol_product_region', got '{result}'"

        print("All _get_sol_table_name tests passed!")
    finally:
        # Remove the mock module
        sys.modules.pop("or_algo", None)

        # Try to reload the real or_algo module (may fail if dependency uses old import name)
        import importlib

        try:
            import or_algo

            importlib.reload(or_algo)
        except (ImportError, ModuleNotFoundError):
            pass

        # Clear any cached or_scenario modules to prevent test pollution
        modules_to_clear = [k for k in list(sys.modules.keys()) if k.startswith("or_scenario")]
        for module in modules_to_clear:
            del sys.modules[module]


if __name__ == "__main__":
    test_get_sol_table_name()
