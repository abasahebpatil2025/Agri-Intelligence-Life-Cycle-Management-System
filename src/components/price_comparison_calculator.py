"""
Price Comparison Calculator Component

This module provides functionality to compare Prophet ML model predictions
with live market prices from Agmarknet API, calculating various comparison
metrics for display to farmers.

Requirements: 4.2, 4.3, 4.4
"""


class PriceComparisonCalculator:
    """
    Compares Prophet predictions with live market prices and calculates
    comparison metrics.
    
    This class provides methods to calculate absolute difference, percentage
    difference, direction, and accuracy score between predicted and actual prices.
    """
    
    def calculate_comparison(
        self,
        predicted_price: float,
        actual_price: float
    ) -> dict:
        """
        Calculate comparison metrics between predicted and actual prices.
        
        Args:
            predicted_price: The price predicted by the Prophet model
            actual_price: The actual live market price from Agmarknet
            
        Returns:
            Dictionary containing:
                - difference (float): Absolute difference (actual - predicted)
                - percentage_diff (float): Percentage difference ((actual - predicted) / predicted) * 100
                - direction (str): "higher" if actual > predicted, "lower" if actual < predicted, "same" if equal
                - accuracy (float): Accuracy score from 0-100 (100 = perfect prediction)
                
        Example:
            >>> calculator = PriceComparisonCalculator()
            >>> result = calculator.calculate_comparison(2000.0, 2100.0)
            >>> result['percentage_diff']
            5.0
            >>> result['direction']
            'higher'
        """
        # Calculate absolute difference
        difference = actual_price - predicted_price
        
        # Calculate percentage difference: ((actual - predicted) / predicted) * 100
        if predicted_price != 0:
            percentage_diff = (difference / predicted_price) * 100
        else:
            # Handle edge case of zero predicted price
            percentage_diff = 0.0 if actual_price == 0 else float('inf')
        
        # Determine direction
        if actual_price > predicted_price:
            direction = "higher"
        elif actual_price < predicted_price:
            direction = "lower"
        else:
            direction = "same"
        
        # Calculate accuracy score (0-100)
        # Accuracy is 100 when prices match exactly, decreases as difference increases
        # Formula: max(0, 100 - abs(percentage_diff))
        accuracy = max(0.0, 100.0 - abs(percentage_diff))
        
        return {
            "difference": difference,
            "percentage_diff": percentage_diff,
            "direction": direction,
            "accuracy": accuracy
        }
