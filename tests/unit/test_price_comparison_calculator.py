"""
Unit tests for PriceComparisonCalculator.

Tests the price comparison calculations including absolute difference,
percentage difference, direction, and accuracy score.

Requirements: 4.2, 4.3, 4.4
"""

import pytest
from src.components.price_comparison_calculator import PriceComparisonCalculator


@pytest.fixture
def calculator():
    """Create PriceComparisonCalculator instance for testing."""
    return PriceComparisonCalculator()


class TestPriceComparisonHigher:
    """Test comparison when actual price is higher than predicted."""
    
    def test_comparison_actual_higher_than_predicted(self, calculator):
        """
        Test correct calculation when actual price > predicted price.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=2000.0,
            actual_price=2100.0
        )
        
        assert result["difference"] == 100.0
        assert result["percentage_diff"] == 5.0
        assert result["direction"] == "higher"
        assert result["accuracy"] == 95.0
    
    def test_comparison_actual_much_higher(self, calculator):
        """
        Test calculation when actual price is significantly higher.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=1000.0,
            actual_price=1500.0
        )
        
        assert result["difference"] == 500.0
        assert result["percentage_diff"] == 50.0
        assert result["direction"] == "higher"
        assert result["accuracy"] == 50.0
    
    def test_comparison_actual_slightly_higher(self, calculator):
        """
        Test calculation when actual price is slightly higher.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=2500.0,
            actual_price=2510.0
        )
        
        assert result["difference"] == 10.0
        assert result["percentage_diff"] == pytest.approx(0.4, rel=0.01)
        assert result["direction"] == "higher"
        assert result["accuracy"] == pytest.approx(99.6, rel=0.01)


class TestPriceComparisonLower:
    """Test comparison when actual price is lower than predicted."""
    
    def test_comparison_actual_lower_than_predicted(self, calculator):
        """
        Test correct calculation when actual price < predicted price.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=2000.0,
            actual_price=1900.0
        )
        
        assert result["difference"] == -100.0
        assert result["percentage_diff"] == -5.0
        assert result["direction"] == "lower"
        assert result["accuracy"] == 95.0
    
    def test_comparison_actual_much_lower(self, calculator):
        """
        Test calculation when actual price is significantly lower.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=3000.0,
            actual_price=2100.0
        )
        
        assert result["difference"] == -900.0
        assert result["percentage_diff"] == -30.0
        assert result["direction"] == "lower"
        assert result["accuracy"] == 70.0
    
    def test_comparison_actual_slightly_lower(self, calculator):
        """
        Test calculation when actual price is slightly lower.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=1800.0,
            actual_price=1795.0
        )
        
        assert result["difference"] == -5.0
        assert result["percentage_diff"] == pytest.approx(-0.278, rel=0.01)
        assert result["direction"] == "lower"
        assert result["accuracy"] == pytest.approx(99.722, rel=0.01)


class TestPriceComparisonEqual:
    """Test comparison when prices are equal."""
    
    def test_comparison_prices_equal(self, calculator):
        """
        Test correct calculation when actual price == predicted price.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=2500.0,
            actual_price=2500.0
        )
        
        assert result["difference"] == 0.0
        assert result["percentage_diff"] == 0.0
        assert result["direction"] == "same"
        assert result["accuracy"] == 100.0


class TestPriceComparisonEdgeCases:
    """Test edge cases in price comparison."""
    
    def test_comparison_zero_predicted_price_zero_actual(self, calculator):
        """
        Test handling when both prices are zero.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=0.0,
            actual_price=0.0
        )
        
        assert result["difference"] == 0.0
        assert result["percentage_diff"] == 0.0
        assert result["direction"] == "same"
        assert result["accuracy"] == 100.0
    
    def test_comparison_zero_predicted_price_nonzero_actual(self, calculator):
        """
        Test handling when predicted price is zero but actual is not.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=0.0,
            actual_price=100.0
        )
        
        assert result["difference"] == 100.0
        assert result["percentage_diff"] == float('inf')
        assert result["direction"] == "higher"
        assert result["accuracy"] == 0.0  # Accuracy capped at 0 for infinite difference
    
    def test_comparison_very_small_prices(self, calculator):
        """
        Test calculation with very small price values.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=0.5,
            actual_price=0.6
        )
        
        assert result["difference"] == pytest.approx(0.1, rel=0.01)
        assert result["percentage_diff"] == pytest.approx(20.0, rel=0.01)
        assert result["direction"] == "higher"
        assert result["accuracy"] == pytest.approx(80.0, rel=0.01)
    
    def test_comparison_very_large_prices(self, calculator):
        """
        Test calculation with very large price values.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=1000000.0,
            actual_price=1050000.0
        )
        
        assert result["difference"] == 50000.0
        assert result["percentage_diff"] == 5.0
        assert result["direction"] == "higher"
        assert result["accuracy"] == 95.0
    
    def test_comparison_negative_accuracy_capped_at_zero(self, calculator):
        """
        Test that accuracy is capped at 0 when difference exceeds 100%.
        
        Requirements: 4.4
        """
        result = calculator.calculate_comparison(
            predicted_price=1000.0,
            actual_price=2500.0
        )
        
        assert result["difference"] == 1500.0
        assert result["percentage_diff"] == 150.0
        assert result["direction"] == "higher"
        assert result["accuracy"] == 0.0  # Capped at 0, not negative


class TestPriceComparisonFormula:
    """Test the specific formula requirements."""
    
    def test_percentage_diff_formula(self, calculator):
        """
        Test that percentage difference uses correct formula:
        ((actual - predicted) / predicted) * 100
        
        Requirements: 4.2
        """
        # Test case 1: actual higher
        result1 = calculator.calculate_comparison(2000.0, 2200.0)
        expected1 = ((2200.0 - 2000.0) / 2000.0) * 100
        assert result1["percentage_diff"] == pytest.approx(expected1, rel=0.001)
        
        # Test case 2: actual lower
        result2 = calculator.calculate_comparison(3000.0, 2700.0)
        expected2 = ((2700.0 - 3000.0) / 3000.0) * 100
        assert result2["percentage_diff"] == pytest.approx(expected2, rel=0.001)
        
        # Test case 3: equal
        result3 = calculator.calculate_comparison(1500.0, 1500.0)
        expected3 = 0.0
        assert result3["percentage_diff"] == expected3
    
    def test_absolute_difference_formula(self, calculator):
        """
        Test that absolute difference is calculated as (actual - predicted).
        
        Requirements: 4.2
        """
        # Test case 1: actual higher
        result1 = calculator.calculate_comparison(1000.0, 1200.0)
        assert result1["difference"] == 200.0
        
        # Test case 2: actual lower
        result2 = calculator.calculate_comparison(1000.0, 800.0)
        assert result2["difference"] == -200.0
        
        # Test case 3: equal
        result3 = calculator.calculate_comparison(1000.0, 1000.0)
        assert result3["difference"] == 0.0
    
    def test_accuracy_formula(self, calculator):
        """
        Test that accuracy is calculated as max(0, 100 - abs(percentage_diff)).
        
        Requirements: 4.4
        """
        # Test case 1: 5% difference
        result1 = calculator.calculate_comparison(2000.0, 2100.0)
        expected1 = max(0.0, 100.0 - abs(5.0))
        assert result1["accuracy"] == expected1
        
        # Test case 2: 30% difference
        result2 = calculator.calculate_comparison(1000.0, 700.0)
        expected2 = max(0.0, 100.0 - abs(-30.0))
        assert result2["accuracy"] == expected2
        
        # Test case 3: 150% difference (should cap at 0)
        result3 = calculator.calculate_comparison(1000.0, 2500.0)
        expected3 = max(0.0, 100.0 - abs(150.0))
        assert result3["accuracy"] == expected3
        assert result3["accuracy"] == 0.0


class TestPriceComparisonReturnStructure:
    """Test the structure of returned dictionary."""
    
    def test_return_dict_has_all_keys(self, calculator):
        """
        Test that returned dictionary contains all required keys.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(2000.0, 2100.0)
        
        assert "difference" in result
        assert "percentage_diff" in result
        assert "direction" in result
        assert "accuracy" in result
    
    def test_return_dict_value_types(self, calculator):
        """
        Test that returned dictionary values have correct types.
        
        Requirements: 4.2, 4.3, 4.4
        """
        result = calculator.calculate_comparison(2000.0, 2100.0)
        
        assert isinstance(result["difference"], float)
        assert isinstance(result["percentage_diff"], float)
        assert isinstance(result["direction"], str)
        assert isinstance(result["accuracy"], float)
    
    def test_direction_values(self, calculator):
        """
        Test that direction only returns valid values.
        
        Requirements: 4.3
        """
        # Test higher
        result1 = calculator.calculate_comparison(1000.0, 1100.0)
        assert result1["direction"] in ["higher", "lower", "same"]
        assert result1["direction"] == "higher"
        
        # Test lower
        result2 = calculator.calculate_comparison(1000.0, 900.0)
        assert result2["direction"] in ["higher", "lower", "same"]
        assert result2["direction"] == "lower"
        
        # Test same
        result3 = calculator.calculate_comparison(1000.0, 1000.0)
        assert result3["direction"] in ["higher", "lower", "same"]
        assert result3["direction"] == "same"
