# AI Service Testing CLI Guide

This guide explains how to use the AI service testing CLI for the course generation platform. The CLI provides comprehensive tools for testing AI provider connectivity, validating configuration, testing generation capabilities, and monitoring API usage limits.

## Features

### 🧪 Provider Testing
- Test OpenAI and Anthropic provider connectivity
- Validate API keys and authentication
- Measure response times and basic functionality
- Support for specific model testing

### 🎯 Generation Testing  
- Test course structure generation
- Test chapter content generation
- Test content quality validation
- Support for different proficiency levels
- Performance benchmarking (2-minute chapter target)

### ⚙️ Configuration Validation
- Validate API key formats and availability
- Check endpoint accessibility
- Verify model availability
- Provide configuration recommendations

### 📊 Usage Monitoring
- Check API usage limits and quotas
- Monitor usage percentages
- Provide usage recommendations
- Alert on approaching limits

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   export OPENAI_API_KEY="sk-your-openai-key-here"
   export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here"
   ```

3. **Verify installation:**
   ```bash
   python test_ai_cli.py
   ```

## Usage

### Basic Command Structure

```bash
python cli_runner.py ai [COMMAND] [OPTIONS]
```

### Global Options

- `--verbose, -v`: Enable verbose output
- `--json-output, -j`: Output results in JSON format
- `--help`: Show help message

## Commands

### 1. Test Providers

Test AI provider connectivity and basic functionality.

```bash
# Test all providers
python cli_runner.py ai test-providers

# Test specific provider
python cli_runner.py ai test-providers --provider openai
python cli_runner.py ai test-providers --provider anthropic

# Test with specific model
python cli_runner.py ai test-providers --provider openai --model gpt-4
python cli_runner.py ai test-providers --provider anthropic --model claude-3-sonnet-20240229

# Set custom timeout
python cli_runner.py ai test-providers --timeout 60
```

**Options:**
- `--provider, -p`: Provider to test (`openai`, `anthropic`, `all`)
- `--model, -m`: Specific model to test (optional)
- `--timeout, -t`: Request timeout in seconds (default: 30)

**Example Output:**
```
🧪 Testing AI Providers
==================================================

┌─ OPENAI Test ─────────────────────────────────┐
│                                               │
│ OPENAI Provider                               │
│                                               │
│ Status: ✅ Available                          │
│ Response Time: 2.34s                          │
│ Model: gpt-4                                  │
│ Test Result: Generated 5 chapters             │
│                                               │
│ Metadata:                                     │
│   chapters_count: 5                           │
│   total_duration: 8.0                         │
│   quality_indicators: {'progression': 0.9}    │
└───────────────────────────────────────────────┘

Provider Test Summary
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Provider ┃ Status        ┃ Response Time ┃ Model ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━┩
│ OPENAI   │ ✅ Available  │ 2.34s        │ gpt-4 │
└──────────┴───────────────┴───────────────┴───────┘
```

### 2. Test Generation

Test AI content generation capabilities with real content scenarios.

```bash
# Test all generation types
python cli_runner.py ai test-generation

# Test specific generation type
python cli_runner.py ai test-generation --test-type structure
python cli_runner.py ai test-generation --test-type content
python cli_runner.py ai test-generation --test-type validation

# Test with specific provider
python cli_runner.py ai test-generation --provider anthropic

# Test with different proficiency level
python cli_runner.py ai test-generation --level beginner
python cli_runner.py ai test-generation --level expert

# Run multiple iterations
python cli_runner.py ai test-generation --iterations 3
```

**Options:**
- `--provider, -p`: Provider to test (`openai`, `anthropic`)
- `--test-type, -t`: Type of generation (`structure`, `content`, `validation`, `all`)
- `--level, -l`: Proficiency level (`beginner`, `intermediate`, `advanced`, `expert`)
- `--iterations, -i`: Number of test iterations (default: 1)

**Example Output:**
```
🎯 Testing AI Generation
==================================================

Iteration 1/1

┌─ STRUCTURE Generation Test ───────────────────┐
│                                               │
│ STRUCTURE Generation Test                     │
│                                               │
│ Status: ✅ Success                            │
│ Duration: 3.45s                               │
│ Content Length: 8 chars                       │
│ Quality Score: 0.92                           │
│                                               │
│ Details:                                      │
│   chapters_count: 8                           │
│   total_duration: 8.0                         │
│   difficulty_progression: [1.0, 1.5, 2.0]    │
│   learning_path_rationale: 156                │
└───────────────────────────────────────────────┘
```

### 3. Validate Configuration

Validate AI service configuration settings and API keys.

```bash
# Validate all configuration aspects
python cli_runner.py ai validate-config

# Check only API keys
python cli_runner.py ai validate-config --check-keys

# Check only endpoints
python cli_runner.py ai validate-config --check-endpoints

# Check only model availability
python cli_runner.py ai validate-config --check-models
```

**Options:**
- `--check-keys, -k`: Check API key validity
- `--check-endpoints, -e`: Check endpoint accessibility  
- `--check-models, -m`: Check model availability

**Example Output:**
```
⚙️ Validating Configuration
==================================================

┌─ Configuration Validation ────────────────────┐
│                                               │
│ Configuration Validation                      │
│                                               │
│ Status: ❌ Invalid                            │
│                                               │
│ Missing Keys:                                 │
│   • ANTHROPIC_API_KEY                         │
│                                               │
│ Warnings:                                     │
│   • Could not connect to Anthropic endpoint   │
│                                               │
│ Recommendations:                              │
│   • Set missing API keys in environment       │
│   • Set DEFAULT_AI_PROVIDER to valid option   │
└───────────────────────────────────────────────┘
```

### 4. Check Limits

Check API usage limits and quotas for configured providers.

```bash
# Check all provider limits
python cli_runner.py ai check-limits

# Check specific provider
python cli_runner.py ai check-limits --provider openai
python cli_runner.py ai check-limits --provider anthropic

# Show detailed usage information
python cli_runner.py ai check-limits --detailed
```

**Options:**
- `--provider, -p`: Provider to check (`openai`, `anthropic`, `all`)
- `--detailed, -d`: Show detailed usage information

**Example Output:**
```
📊 Checking API Limits
==================================================

┌─ OPENAI Limits ───────────────────────────────┐
│                                               │
│ OPENAI API Limits                             │
│                                               │
│ Status: ⚠️ WARNING                            │
│ Usage: 1,500 / 10,000 (15.0%)                │
│                                               │
│ Recommendations:                              │
│   • Monitor usage closely                     │
└───────────────────────────────────────────────┘

API Limits Summary
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Provider ┃ Status        ┃ Usage         ┃ Percentage ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ OPENAI   │ ⚠️ WARNING    │ 1,500 / 10,000│ 15.0%     │
└──────────┴───────────────┴───────────────┴────────────┘
```

## JSON Output

All commands support JSON output for integration with other tools:

```bash
python cli_runner.py ai test-providers --json-output
python cli_runner.py ai validate-config --json-output --check-keys
```

**JSON Example:**
```json
[
  {
    "provider": "openai",
    "available": true,
    "response_time": 2.34,
    "error": null,
    "model": "gpt-4",
    "test_content": "Generated 5 chapters",
    "metadata": {
      "chapters_count": 5,
      "total_duration": 8.0,
      "quality_indicators": {"progression_smoothness": 0.9}
    }
  }
]
```

## Error Handling

The CLI provides comprehensive error handling and diagnostics:

### Common Error Scenarios

1. **Missing API Keys:**
   ```
   ❌ Error testing providers: OpenAI API key not configured
   ```

2. **Network Issues:**
   ```
   ❌ Error testing providers: Request timed out after 30 seconds
   ```

3. **Invalid Configuration:**
   ```
   ❌ Error validating configuration: OPENAI_API_KEY: Invalid format
   ```

4. **Service Unavailable:**
   ```
   ❌ Error testing providers: AI service 'openai' is currently unavailable
   ```

### Troubleshooting

1. **Check API Keys:**
   ```bash
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   ```

2. **Validate Configuration:**
   ```bash
   python cli_runner.py ai validate-config --check-keys
   ```

3. **Test Basic Connectivity:**
   ```bash
   python cli_runner.py ai test-providers --timeout 60
   ```

4. **Check Verbose Output:**
   ```bash
   python cli_runner.py ai test-providers --verbose
   ```

## Integration Examples

### CI/CD Pipeline

```bash
#!/bin/bash
# CI/CD script for AI service validation

echo "Validating AI service configuration..."
python cli_runner.py ai validate-config --json-output > config_results.json

if [ $? -eq 0 ]; then
    echo "✅ Configuration valid"
    
    echo "Testing AI providers..."
    python cli_runner.py ai test-providers --json-output > provider_results.json
    
    if [ $? -eq 0 ]; then
        echo "✅ Provider tests passed"
    else
        echo "❌ Provider tests failed"
        exit 1
    fi
else
    echo "❌ Configuration invalid"
    exit 1
fi
```

### Monitoring Script

```bash
#!/bin/bash
# Monitor API usage limits

python cli_runner.py ai check-limits --json-output > limits.json

# Parse JSON and alert if usage > 80%
python -c "
import json
with open('limits.json') as f:
    limits = json.load(f)
for limit in limits:
    if limit['percentage_used'] > 80:
        print(f'WARNING: {limit[\"provider\"]} usage at {limit[\"percentage_used\"]}%')
"
```

## Performance Benchmarks

The CLI tests against platform performance requirements:

- **Chapter Generation**: Target <2 minutes per chapter
- **Structure Generation**: Target <30 seconds
- **Quality Validation**: Target <10 seconds
- **Provider Response**: Target <5 seconds

Performance warnings are displayed when targets are exceeded.

## Development

### Adding New Tests

1. **Create test function:**
   ```python
   async def _test_new_feature(ai_client: AIClient) -> GenerationTest:
       # Test implementation
       pass
   ```

2. **Add to command:**
   ```python
   if test_type in ['new_feature', 'all']:
       result = await _test_new_feature(ai_client)
       results.append(result)
   ```

3. **Update help text and options:**
   ```python
   @click.option('--test-type', type=click.Choice(['new_feature', 'all']))
   ```

### Testing

Run the test suite to verify CLI functionality:

```bash
python test_ai_cli.py
```

## Support

For issues or questions:

1. Check this guide for common solutions
2. Run diagnostic commands with `--verbose` flag
3. Review error messages and support IDs
4. Check API provider status pages
5. Validate environment configuration

The CLI is designed to provide comprehensive diagnostics for AI service integration issues.