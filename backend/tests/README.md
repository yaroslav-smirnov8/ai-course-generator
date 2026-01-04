# Test Suite

## Quick Start

```bash
cd backend
test_unit.bat
```

## Test Results

**20 tests - 100% pass rate**

## Available Test Runners

### 1. Standard Runner (Recommended for Screencast)
```bash
test_unit.bat
```
Beautiful output with statistics and percentages.

### 2. HTML Report
```bash
run_tests_html.bat
```
Generates HTML report and opens in browser.

### 3. Python Stats Runner
```bash
run_tests_beautiful.bat
```
Python script with progress bar and detailed statistics.

## Test Coverage

### Unit Tests (20 tests)

#### JSON Extractor Tests (15 tests - 75%)
- Bracket fixing and balancing (3 tests)
- JSON extraction from text (3 tests)
- Truncated JSON processing (3 tests)
- Course structure extraction (3 tests)
- Edge cases (3 tests)

#### Content Processor Tests (5 tests - 25%)
- Exercise content processing (5 tests)
- Multiple exercises handling
- Empty and malformed content
- Special characters support

## Technology Stack

- Python 3.10.11
- pytest 9.0.2
- pytest-asyncio
- aiosqlite (for async tests)

## Test Structure

```
backend/tests/
├── unit/
│   ├── test_json_extractor.py      # JSON processing tests (15)
│   └── test_content_processor.py   # Content processing tests (5)
├── conftest.py                      # Test fixtures
└── improved_json_extractor.py      # Test utilities
```

## Sample Output

```
================================================================
                    TEST SUITE EXECUTION                        
================================================================

Date: 2026-01-01 17:00:00
Python: 3.10.11
Framework: pytest 9.0.2

----------------------------------------------------------------

Running tests...

tests/unit/test_content_processor.py::TestExerciseProcessing::test_process_simple_exercise PASSED
tests/unit/test_content_processor.py::TestExerciseProcessing::test_process_multiple_exercises PASSED
...
tests/unit/test_json_extractor.py::TestEdgeCases::test_empty_object PASSED

----------------------------------------------------------------

================================================================
                      TEST SUMMARY                              
================================================================

[PASS] ALL TESTS PASSED - 100% SUCCESS RATE

Test Statistics:
   Total Tests:        20
   Passed:             20
   Failed:              0
   Success Rate:       100.0%

Test Coverage by Module:
   JSON Extractor:      15 tests [PASS] (75.0%)
   Content Processor:    5 tests [PASS] (25.0%)

Categories:
   Bracket Fixing:        3 tests [PASS]
   JSON Extraction:       3 tests [PASS]
   Truncated JSON:        3 tests [PASS]
   Course Extraction:     3 tests [PASS]
   Edge Cases:            3 tests [PASS]
   Exercise Processing:   5 tests [PASS]

================================================================
TEST SUITE: PASSED
================================================================
```
