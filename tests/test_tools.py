"""Tests for agent tools."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from agent.tools import (
    get_menu,
    calculate_order,
    check_balance,
    make_transfer_tool,
)


class TestGetMenuTool:
    """Test the get_menu tool."""

    def test_get_menu_returns_string(self):
        """Test that get_menu returns a string."""
        result = get_menu.func()
        assert isinstance(result, str)

    def test_get_menu_contains_all_items(self):
        """Test that menu output contains all menu items."""
        result = get_menu.func()
        items = ["espresso", "flat white", "cappuccino", "cold brew",
                 "matcha latte", "chai latte", "blueberry muffin",
                 "croissant", "avocado toast"]
        for item in items:
            assert item.lower() in result.lower()

    def test_get_menu_contains_prices(self):
        """Test that menu output contains HBAR prices."""
        result = get_menu.func()
        assert "ℏ" in result or "HBAR" in result.upper()

    def test_get_menu_contains_categories(self):
        """Test that menu output contains category headers."""
        result = get_menu.func()
        assert "Coffee" in result
        assert "Specials" in result or "Special" in result
        assert "Food" in result


class TestCalculateOrderTool:
    """Test the calculate_order tool."""

    def test_calculate_order_single_item(self):
        """Test calculating cost of a single item."""
        result = calculate_order.func(["espresso"])
        assert "1ℏ" in result or "1 HBAR" in result.upper()
        assert "Total:" in result

    def test_calculate_order_multiple_items(self):
        """Test calculating cost of multiple items."""
        result = calculate_order.func(["flat white", "croissant"])
        assert "Flat White" in result
        assert "Croissant" in result
        assert "3ℏ" in result or "Total: 3" in result

    def test_calculate_order_case_insensitive(self):
        """Test that item names are case-insensitive."""
        result1 = calculate_order.func(["ESPRESSO"])
        result2 = calculate_order.func(["espresso"])
        result3 = calculate_order.func(["Espresso"])
        assert "1ℏ" in result1 and "1ℏ" in result2 and "1ℏ" in result3

    def test_calculate_order_with_whitespace(self):
        """Test that item names with extra whitespace work."""
        result = calculate_order.func(["  flat white  "])
        assert "Flat White" in result
        assert "2ℏ" in result

    def test_calculate_order_invalid_item(self):
        """Test handling of invalid item names."""
        result = calculate_order.func(["invalid item"])
        assert "don't have" in result.lower() or "not found" in result.lower()

    def test_calculate_order_mixed_valid_invalid(self):
        """Test mixed valid and invalid items."""
        result = calculate_order.func(["espresso", "invalid"])
        assert "invalid" in result.lower()
        assert "don't have" in result.lower() or "not found" in result.lower()

    def test_calculate_order_shows_receipt_prompt(self):
        """Test that receipt shows confirmation prompt."""
        result = calculate_order.func(["cappuccino"])
        assert "confirm" in result.lower() or "yes" in result.lower()


class TestCheckBalanceTool:
    """Test the check_balance tool."""

    @patch('httpx.get')
    def test_check_balance_sufficient(self, mock_get):
        """Test that balance check passes when sufficient."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "balance": {"balance": 500_000_000}  # 5 HBAR
        }
        mock_get.return_value = mock_response

        result = check_balance.func("0.0.123", 3.0)
        assert "Balance OK" in result
        assert "5.00ℏ" in result or "5" in result

    @patch('httpx.get')
    def test_check_balance_insufficient(self, mock_get):
        """Test that balance check fails when insufficient."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "balance": {"balance": 100_000_000}  # 1 HBAR
        }
        mock_get.return_value = mock_response

        result = check_balance.func("0.0.123", 5.0)
        assert "Insufficient balance" in result
        assert "short by" in result.lower() or "Short by" in result

    @patch('httpx.get')
    def test_check_balance_api_error(self, mock_get):
        """Test handling of API errors."""
        mock_get.side_effect = Exception("Network error")

        result = check_balance.func("0.0.123", 1.0)
        assert "Could not fetch balance" in result
        assert "Proceeding" in result or "proceeding" in result.lower()

    @patch('httpx.get')
    def test_check_balance_exact_amount(self, mock_get):
        """Test balance check with exact amount."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "balance": {"balance": 200_000_000}  # 2 HBAR
        }
        mock_get.return_value = mock_response

        result = check_balance.func("0.0.123", 2.0)
        assert "Balance OK" in result


class TestTransferToolFactory:
    """Test the transfer_hbar_tool factory."""

    @pytest.mark.asyncio
    async def test_transfer_tool_creation(self):
        """Test that transfer tool is created correctly."""
        mock_pay_session = AsyncMock()
        mock_pay_session.request_payment.return_value = "0.0.1-1000-1"

        tool = make_transfer_tool(
            user_account_id="0.0.100",
            shop_account_id="0.0.200",
            pay_session=mock_pay_session
        )

        assert tool.name == "transfer_hbar_tool"
        assert "Transfer" in tool.description

    @pytest.mark.asyncio
    async def test_transfer_tool_calls_pay_session(self):
        """Test that transfer tool calls pay_session correctly."""
        mock_pay_session = AsyncMock()
        mock_pay_session.request_payment.return_value = "0.0.1-1000-1"

        tool = make_transfer_tool(
            user_account_id="0.0.100",
            shop_account_id="0.0.200",
            pay_session=mock_pay_session
        )

        # Get the coroutine function from the tool
        result = await tool.coroutine(2.5, "Test order")
        
        mock_pay_session.request_payment.assert_called_once()
        assert "0.0.1-1000-1" in result or "confirmed" in result.lower()

    @pytest.mark.asyncio
    async def test_transfer_tool_error_handling(self):
        """Test that transfer tool handles errors gracefully."""
        mock_pay_session = AsyncMock()
        mock_pay_session.request_payment.side_effect = Exception("Payment failed")

        tool = make_transfer_tool(
            user_account_id="0.0.100",
            shop_account_id="0.0.200",
            pay_session=mock_pay_session
        )

        result = await tool.coroutine(2.5, "Test order")
        assert "failed" in result.lower() or "Payment failed" in result
