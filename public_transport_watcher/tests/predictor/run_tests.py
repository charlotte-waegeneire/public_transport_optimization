from pathlib import Path
import sys

import pytest

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def run_predictor_tests():
    """Run all predictor tests."""
    test_dir = Path(__file__).parent

    args = [
        str(test_dir),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable warnings for cleaner output
    ]

    # Add coverage if available
    try:
        args.extend(["--cov=public_transport_watcher.predictor", "--cov-report=term-missing"])
    except ImportError:
        print("Coverage not available, running tests without coverage")

    exit_code = pytest.main(args)

    return exit_code


def run_specific_test(test_file):
    """Run a specific test file."""
    test_path = Path(__file__).parent / test_file

    if not test_path.exists():
        print(f"Test file {test_file} not found")
        return 1

    args = [
        str(test_path),
        "-v",
        "--tb=short",
        "--strict-markers",
        "--disable-warnings",
    ]

    exit_code = pytest.main(args)
    return exit_code


def main():
    """Main function to run tests."""
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        exit_code = run_specific_test(test_file)
    else:
        exit_code = run_predictor_tests()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
