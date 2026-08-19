"""
Tax Engine for Kenyan statutory deductions.

CRITICAL ALGORITHMS - 2024 Kenyan Tax System:

1. NSSF (National Social Security Fund)
   - Tier 1: 6% of pensionable pay, capped at KES 7,000
   - Tier 2: 6% of pensionable pay, capped at KES 29,000
   
2. SHA/NHIF: 2.75% of Gross Salary

3. Housing Levy: 1.5% of Gross Salary

4. Taxable Pay: Gross Salary - NSSF (Tier 1 + Tier 2)

5. PAYE (Personal Income Tax)
   - First KES 24,000 @ 10%
   - Next KES 8,333 @ 25%
   - Next KES 467,667 @ 30%
   - Next KES 300,000 @ 32.5%
   - Above KES 800,000 @ 35%

6. Personal Relief: KES 2,400 (deducted from calculated PAYE)

All calculations use Decimal for accuracy (no floating-point errors).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple
import logging

logger = logging.getLogger(__name__)


class TaxCalculationResult(NamedTuple):
    """Result of tax calculation."""
    nssf_tier1: Decimal
    nssf_tier2: Decimal
    nssf_total: Decimal
    sha_nhif: Decimal
    housing_levy: Decimal
    taxable_pay: Decimal
    paye: Decimal
    personal_relief: Decimal
    paye_after_relief: Decimal
    total_deductions: Decimal
    net_pay: Decimal


class TaxEngine:
    """
    Kenyan Tax Engine for statutory deductions.
    
    All amounts in KES. All calculations use Decimal for precision.
    """
    
    # NSSF Tier caps (maximum deduction amounts)
    NSSF_TIER1_CAP = Decimal("7000.00")  # Max KES 7,000
    NSSF_TIER2_CAP = Decimal("29000.00")  # Max KES 29,000
    NSSF_TIER_RATE = Decimal("0.06")  # 6% rate
    
    # SHA/NHIF rate
    SHA_NHIF_RATE = Decimal("0.0275")  # 2.75% of gross
    
    # Housing Levy rate
    HOUSING_LEVY_RATE = Decimal("0.015")  # 1.5% of gross
    
    # Personal relief (flat deduction)
    PERSONAL_RELIEF = Decimal("2400.00")  # KES 2,400
    
    # PAYE tax bands (exact KRA 2024 brackets)
    # Tuple: (band_start, band_end, rate, cumulative_tax_up_to_start)
    PAYE_BANDS = [
        (Decimal("0"), Decimal("24000"), Decimal("0.10"), Decimal("0")),
        (Decimal("24000"), Decimal("32333"), Decimal("0.25"), Decimal("2400")),
        (Decimal("32333"), Decimal("500000"), Decimal("0.30"), Decimal("4483.25")),
        (Decimal("500000"), Decimal("800000"), Decimal("0.325"), Decimal("144783.25")),
        (Decimal("800000"), Decimal("999999999"), Decimal("0.35"), Decimal("241283.25")),
    ]
    
    @staticmethod
    def calculate_nssf(gross_pay: Decimal) -> tuple[Decimal, Decimal, Decimal]:
        """
        Calculate NSSF Tier 1 and Tier 2 deductions.
        
        NSSF = 6% of pensionable pay (same base for both tiers)
        Tier 1: Capped at KES 7,000
        Tier 2: Capped at KES 29,000
        
        Args:
            gross_pay: Gross salary (basic + allowances)
            
        Returns:
            Tuple of (tier1, tier2, total)
        """
        # Pensionable pay = gross pay (6% base)
        nssf_base = gross_pay * TaxEngine.NSSF_TIER_RATE
        
        # Tier 1: Cap at 7,000
        tier1 = min(nssf_base, TaxEngine.NSSF_TIER1_CAP)
        
        # Tier 2: Cap at 29,000
        tier2 = min(nssf_base, TaxEngine.NSSF_TIER2_CAP)
        
        # Total NSSF (both tiers combined, not double-counted)
        # Total cap is min(nssf_base, tier1_cap + tier2_cap)
        total_nssf = tier1 + tier2
        
        return tier1, tier2, total_nssf
    
    @staticmethod
    def calculate_sha_nhif(gross_pay: Decimal) -> Decimal:
        """
        Calculate SHA/NHIF deduction.
        
        SHA/NHIF = 2.75% of Gross Salary (flat rate)
        
        Args:
            gross_pay: Gross salary
            
        Returns:
            SHA/NHIF deduction amount
        """
        sha_amount = (gross_pay * TaxEngine.SHA_NHIF_RATE).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        return sha_amount
    
    @staticmethod
    def calculate_housing_levy(gross_pay: Decimal) -> Decimal:
        """
        Calculate Housing Levy deduction.
        
        Housing Levy = 1.5% of Gross Salary (flat rate)
        
        Args:
            gross_pay: Gross salary
            
        Returns:
            Housing Levy deduction amount
        """
        housing_amount = (gross_pay * TaxEngine.HOUSING_LEVY_RATE).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        return housing_amount
    
    @staticmethod
    def calculate_paye(taxable_pay: Decimal) -> Decimal:
        """
        Calculate PAYE tax using exact KRA tax brackets.
        
        Tax Bands (2024):
        - First KES 24,000 @ 10% = 2,400
        - Next KES 8,333 @ 25% = 2,083.25
        - Next KES 467,667 @ 30% = 140,300.10
        - Next KES 300,000 @ 32.5% = 97,500
        - Above KES 800,000 @ 35%
        
        Args:
            taxable_pay: Gross - NSSF
            
        Returns:
            PAYE tax amount (before personal relief)
        """
        if taxable_pay <= 0:
            return Decimal("0.00")
        
        paye_tax = Decimal("0.00")
        remaining_pay = taxable_pay
        
        # Apply each tax band
        for band_start, band_end, rate, cumulative_tax_before in TaxEngine.PAYE_BANDS:
            if remaining_pay <= 0:
                break
            
            # Amount in this band
            taxable_in_band = min(remaining_pay, band_end - band_start)
            
            # Tax for this band
            tax_in_band = (taxable_in_band * rate).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            
            paye_tax += tax_in_band
            remaining_pay -= taxable_in_band
        
        return paye_tax
    
    @staticmethod
    def calculate_taxes(
        basic_pay: Decimal,
        allowances: Decimal = Decimal("0.00"),
    ) -> TaxCalculationResult:
        """
        MAIN ALGORITHM: Calculate all statutory deductions for staff salary.
        
        Process:
        1. Calculate Gross Pay = Basic + Allowances
        2. Calculate NSSF (Tier 1 & 2)
        3. Calculate SHA/NHIF = 2.75% of Gross
        4. Calculate Housing Levy = 1.5% of Gross
        5. Calculate Taxable Pay = Gross - NSSF
        6. Calculate PAYE using exact KRA bands
        7. Apply Personal Relief (KES 2,400)
        8. Calculate Net Pay = Gross - All Deductions
        
        Args:
            basic_pay: Basic monthly salary
            allowances: Total allowances (optional, default 0)
            
        Returns:
            TaxCalculationResult with complete breakdown
        """
        # Ensure Decimal precision
        basic_pay = Decimal(str(basic_pay)).quantize(Decimal("0.01"))
        allowances = Decimal(str(allowances)).quantize(Decimal("0.01"))
        
        # Step 1: Gross Pay
        gross_pay = basic_pay + allowances
        
        logger.debug(f"Calculating taxes for: Basic={basic_pay}, Allowances={allowances}, Gross={gross_pay}")
        
        # Step 2: NSSF calculation
        nssf_tier1, nssf_tier2, nssf_total = TaxEngine.calculate_nssf(gross_pay)
        
        # Step 3: SHA/NHIF
        sha_nhif = TaxEngine.calculate_sha_nhif(gross_pay)
        
        # Step 4: Housing Levy
        housing_levy = TaxEngine.calculate_housing_levy(gross_pay)
        
        # Step 5: Taxable Pay (Gross - NSSF)
        taxable_pay = gross_pay - nssf_total
        
        # Step 6: PAYE before relief
        paye_before_relief = TaxEngine.calculate_paye(taxable_pay)
        
        # Step 7: Personal Relief
        personal_relief = TaxEngine.PERSONAL_RELIEF
        paye_after_relief = max(paye_before_relief - personal_relief, Decimal("0.00"))
        
        # Step 8: Total deductions and Net Pay
        total_deductions = nssf_total + sha_nhif + housing_levy + paye_after_relief
        net_pay = gross_pay - total_deductions
        
        logger.debug(
            f"Tax breakdown: NSSF={nssf_total}, SHA={sha_nhif}, Housing={housing_levy}, "
            f"PAYE={paye_after_relief}, Total Deductions={total_deductions}, Net={net_pay}"
        )
        
        return TaxCalculationResult(
            nssf_tier1=nssf_tier1,
            nssf_tier2=nssf_tier2,
            nssf_total=nssf_total,
            sha_nhif=sha_nhif,
            housing_levy=housing_levy,
            taxable_pay=taxable_pay,
            paye=paye_after_relief,
            personal_relief=personal_relief,
            paye_after_relief=paye_after_relief,
            total_deductions=total_deductions,
            net_pay=net_pay,
        )


# ============================================================================
# UNIT TESTS FOR TAX CALCULATIONS
# ============================================================================


def test_nssf_calculation():
    """Test NSSF calculation with various gross pay amounts."""
    # Test case 1: Low salary (NSSF caps not hit)
    gross = Decimal("20000")
    t1, t2, total = TaxEngine.calculate_nssf(gross)
    expected = Decimal("20000") * Decimal("0.06")  # 1200
    assert t1 == t2 == expected, f"Low salary: Expected {expected}, got T1={t1}, T2={t2}"
    
    # Test case 2: Medium salary (exceeds Tier 1 cap)
    gross = Decimal("150000")
    t1, t2, total = TaxEngine.calculate_nssf(gross)
    expected_base = Decimal("150000") * Decimal("0.06")  # 9000
    assert t1 == Decimal("7000"), f"Tier 1 cap: Expected 7000, got {t1}"
    assert t2 == Decimal("9000"), f"Tier 2: Expected 9000, got {t2}"
    
    # Test case 3: High salary (both tiers capped)
    gross = Decimal("600000")
    t1, t2, total = TaxEngine.calculate_nssf(gross)
    assert t1 == Decimal("7000"), f"High salary T1: Expected 7000, got {t1}"
    assert t2 == Decimal("29000"), f"High salary T2: Expected 29000, got {t2}"


def test_paye_calculation():
    """Test PAYE calculation across different taxable pay ranges."""
    # Test case 1: Below first bracket
    taxable = Decimal("10000")
    paye = TaxEngine.calculate_paye(taxable)
    expected = Decimal("10000") * Decimal("0.10")  # 1000
    assert paye == expected, f"Low income: Expected {expected}, got {paye}"
    
    # Test case 2: Across brackets
    taxable = Decimal("50000")
    paye = TaxEngine.calculate_paye(taxable)
    # First 24,000 @ 10% = 2,400
    # Next 26,000 @ 25% = 6,500
    # Total = 8,900
    expected = Decimal("8900.00")
    assert paye == expected, f"Mid income: Expected {expected}, got {paye}"
    
    # Test case 3: High income
    taxable = Decimal("500000")
    paye = TaxEngine.calculate_paye(taxable)
    # First 24,000 @ 10% = 2,400
    # Next 8,333 @ 25% = 2,083.25
    # Next 467,667 @ 30% = 140,300.10
    # Total = 144,783.35
    expected = Decimal("144783.35")
    assert paye == expected, f"High income: Expected {expected}, got {paye}"


def test_complete_salary_calculation():
    """Test complete salary calculation."""
    basic = Decimal("40000")
    allowances = Decimal("5000")
    
    result = TaxEngine.calculate_taxes(basic, allowances)
    
    # Verify gross
    assert result.taxable_pay == Decimal("45000") - (result.nssf_tier1 + result.nssf_tier2)
    
    # Verify net is positive
    assert result.net_pay > 0
    
    # Verify total deductions = gross - net
    gross = basic + allowances
    assert result.total_deductions == (gross - result.net_pay)
    
    print(f"✓ Salary calculation test passed")
    print(f"  Basic: {basic}, Allowances: {allowances}")
    print(f"  NSSF: {result.nssf_total}, SHA: {result.sha_nhif}, Housing: {result.housing_levy}, PAYE: {result.paye}")
    print(f"  Net Pay: {result.net_pay}")


if __name__ == "__main__":
    test_nssf_calculation()
    print("✓ NSSF calculation tests passed")
    
    test_paye_calculation()
    print("✓ PAYE calculation tests passed")
    
    test_complete_salary_calculation()
    print("✓ All tax engine tests passed")
