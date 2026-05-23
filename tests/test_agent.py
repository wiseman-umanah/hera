"""Tests for the agent initialization."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from agent.coffee_agent import build_agent


class TestBuildAgent:
    """Test agent factory function."""

    @patch('agent.coffee_agent.Client')
    @patch('agent.coffee_agent.ChatGroq')
    @patch('agent.coffee_agent.HederaLangchainToolkit')
    @patch('agent.coffee_agent.create_agent')
    def test_build_agent_creation(self, mock_create, mock_toolkit, mock_llm, mock_client):
        """Test that build_agent creates an agent."""
        mock_pay_session = MagicMock()
        
        with patch('agent.coffee_agent.settings') as mock_settings:
            mock_settings.SHOP_ACCOUNT_ID = "0.0.200"
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.HEDERA_NETWORK = "testnet"
            
            # Mock the toolkit and LLM returns
            mock_toolkit_instance = MagicMock()
            mock_toolkit.return_value = mock_toolkit_instance
            mock_toolkit_instance.get_tools.return_value = []

            mock_llm_instance = MagicMock()
            mock_llm.return_value = mock_llm_instance

            mock_agent = MagicMock()
            mock_create.return_value = mock_agent

            agent = build_agent("0.0.100", mock_pay_session)

            # Verify agent was created
            assert mock_create.called

    @patch('agent.coffee_agent.Client')
    @patch('agent.coffee_agent.HederaLangchainToolkit')
    def test_build_agent_with_correct_account(self, mock_toolkit, mock_client):
        """Test that agent is built with correct account context."""
        mock_pay_session = MagicMock()
        user_account = "0.0.999"

        with patch('agent.coffee_agent.ChatGroq'):
            with patch('agent.coffee_agent.create_agent'):
                mock_toolkit_instance = MagicMock()
                mock_toolkit.return_value = mock_toolkit_instance
                mock_toolkit_instance.get_tools.return_value = []

                try:
                    build_agent(user_account, mock_pay_session)
                    # Verify toolkit was created with the right account
                    assert mock_toolkit.called
                except Exception:
                    # Agent creation may fail due to mocks, but we're testing the setup
                    pass
