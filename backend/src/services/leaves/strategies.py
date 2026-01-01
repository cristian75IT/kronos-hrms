"""
Accrual Calculation Strategies.
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import date
from typing import Dict, Any, Optional

class CalculationStrategy(ABC):
    @abstractmethod
    def calculate(
        self, 
        annual_amount: Decimal, 
        contract: Any, 
        period_start: date, 
        period_end: date,
        params: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Calculate accrual for a specific period."""
        pass

class MonthlyStandardStrategy(CalculationStrategy):
    """Standard 1/12 calculation (if >= 15 days)."""
    
    def calculate(
        self, 
        annual_amount: Decimal, 
        contract: Any, 
        period_start: date, 
        period_end: date, 
        params: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        params = params or {}
        # Try to find specific divisor or default to 12
        divisor = Decimal(params.get("divisor", 12))
        
        # Calculate overlap
        c_start = contract.start_date
        c_end = contract.end_date or date(9999, 12, 31)
        
        actual_start = max(c_start, period_start)
        actual_end = min(c_end, period_end)
        
        # Check validity
        if actual_start > actual_end:
            return Decimal(0)
            
        days_worked = (actual_end - actual_start).days + 1
        
        if days_worked < 0:
            return Decimal(0)
            
        # 15 days threshold (configurable)
        min_days = int(params.get("min_days", 15))
        
        if days_worked >= min_days:
            return annual_amount / divisor
            
        return Decimal(0)

class Daily365Strategy(CalculationStrategy):
    """Daily calculation (Annual / 365 * days)."""
    
    def calculate(
        self, 
        annual_amount: Decimal, 
        contract: Any, 
        period_start: date, 
        period_end: date, 
        params: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        params = params or {}
        year_basis = Decimal(params.get("year_basis", 365))
        
        c_start = contract.start_date
        c_end = contract.end_date or date(9999, 12, 31)
        
        actual_start = max(c_start, period_start)
        actual_end = min(c_end, period_end)
        
        if actual_start > actual_end:
            return Decimal(0)
            
        days_worked = (actual_end - actual_start).days + 1
        
        if days_worked <= 0:
            return Decimal(0)
            
        daily_rate = annual_amount / year_basis
        return daily_rate * Decimal(days_worked)

class StrategyFactory:
    _strategies: Dict[str, CalculationStrategy] = {
        "calculate_accrual_monthly_std": MonthlyStandardStrategy(),
        "calculate_accrual_daily_365": Daily365Strategy(),
        # Placeholder for hourly if needed
    }
    
    @classmethod
    def get(cls, function_name: str) -> CalculationStrategy:
        return cls._strategies.get(function_name, cls._strategies["calculate_accrual_monthly_std"])
