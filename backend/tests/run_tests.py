"""
Test runner script for the project
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests():
    """Run all tests with coverage"""
    args = [
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        "-W", "ignore::DeprecationWarning",
    ]
    return pytest.main(args)


def run_unit_tests():
    """Run only unit tests"""
    args = [
        "tests/unit/",
        "-v",
        "--tb=short",
    ]
    return pytest.main(args)


def run_integration_tests():
    """Run only integration tests"""
    args = [
        "tests/integration/",
        "-v",
        "--tb=short",
    ]
    return pytest.main(args)


def run_specific_test(test_path):
    """Run a specific test file or test function"""
    args = [
        test_path,
        "-v",
        "--tb=short",
    ]
    return pytest.main(args)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "unit":
            sys.exit(run_unit_tests())
        elif command == "integration":
            sys.exit(run_integration_tests())
        elif command == "all":
            sys.exit(run_all_tests())
        else:
            # Run specific test
            sys.exit(run_specific_test(command))
    else:
        # Default: run all tests
        sys.exit(run_all_tests())
