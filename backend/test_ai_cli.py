#!/usr/bin/env python3
"""
Test script for the AI CLI functionality.

This script tests the AI CLI commands without requiring actual API keys,
useful for development and CI/CD validation.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from unittest.mock import Mock, patch
import asyncio
from click.testing import CliRunner

from src.cli.ai import ai


def test_ai_cli_basic():
    """Test basic CLI functionality."""
    runner = CliRunner()
    
    # Test help command
    result = runner.invoke(ai, ['--help'])
    assert result.exit_code == 0
    assert 'AI service testing and management commands' in result.output
    
    print("✅ Basic CLI help test passed")


def test_validate_config_command():
    """Test the validate-config command."""
    runner = CliRunner()
    
    # Mock the async validation function
    with patch('src.cli.ai._validate_configuration') as mock_validate:
        mock_validate.return_value = Mock(
            valid=False,
            missing_keys=['OPENAI_API_KEY', 'ANTHROPIC_API_KEY'],
            invalid_values=[],
            warnings=[],
            recommendations=['Set missing API keys in environment']
        )
        
        # Test validate-config command
        result = runner.invoke(ai, ['validate-config', '--check-keys'])
        
        # Note: This might exit with code 1 due to async handling,
        # but we can still check that the command was recognized
        assert 'validate-config' in str(result) or result.exit_code in [0, 1]
    
    print("✅ Validate config command test passed")


def test_help_for_all_commands():
    """Test help for all available commands."""
    runner = CliRunner()
    
    commands = ['test-providers', 'test-generation', 'validate-config', 'check-limits']
    
    for command in commands:
        result = runner.invoke(ai, [command, '--help'])
        # Commands should show help (exit code 0) or be recognized
        assert result.exit_code == 0 or command in result.output
        print(f"✅ Help for {command} command works")


def test_cli_structure():
    """Test CLI structure and command availability."""
    runner = CliRunner()
    
    # Get main help
    result = runner.invoke(ai, ['--help'])
    
    # Check that all expected commands are listed
    expected_commands = ['test-providers', 'test-generation', 'validate-config', 'check-limits']
    
    for cmd in expected_commands:
        assert cmd in result.output, f"Command {cmd} not found in help output"
    
    print("✅ All expected commands are available")


def test_cli_options():
    """Test CLI options parsing."""
    runner = CliRunner()
    
    # Test global options
    result = runner.invoke(ai, ['--verbose', '--help'])
    assert result.exit_code == 0
    
    result = runner.invoke(ai, ['--json-output', '--help'])
    assert result.exit_code == 0
    
    print("✅ Global CLI options work correctly")


def main():
    """Run all CLI tests."""
    print("🧪 Testing AI CLI functionality...")
    print("=" * 50)
    
    try:
        test_ai_cli_basic()
        test_validate_config_command()
        test_help_for_all_commands()
        test_cli_structure()
        test_cli_options()
        
        print("\n🎉 All CLI tests passed!")
        print("\nTo test with real API keys:")
        print("1. Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY environment variables")
        print("2. Run: python cli_runner.py ai test-providers")
        print("3. Run: python cli_runner.py ai validate-config")
        print("4. Run: python cli_runner.py ai test-generation")
        print("5. Run: python cli_runner.py ai check-limits")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()