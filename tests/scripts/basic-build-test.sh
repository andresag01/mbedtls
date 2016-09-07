#!/bin/sh

# basic-build-tests.sh
#
# This file is part of mbed TLS (https://tls.mbed.org)
#
# Copyright (c) 2016, ARM Limited, All Rights Reserved
#
# Purpose
#
# Executes the basic test suites, captures the results, and generates a simple
# test report and code coverage report.
#
# The tests include:
#   * Unit tests                - executed using tests/scripts/run-test-suite.pl
#   * Self-tests                - executed using the test suites above
#   * System tests              - executed using tests/ssl-opt.sh
#   * Interoperability tests    - executed using tests/compat.sh
#
# The tests focus on functionality and do not consider performance.
#
# Note the tests self-adapt due to configurations in include/mbedtls/config.h
# which can lead to some tests being skipped, and can cause the number of
# available tests to fluctuate.
#
# This script has been written to be generic and should work on any shell.
#
# Usage: basic-build-tests.sh
#

# Abort on errors (and uninitiliased variables)
set -eux

if [ -d library -a -d include -a -d tests ]; then :; else
    echo "Must be run from mbed TLS root" >&2
    exit 1
fi

CONFIG_H='include/mbedtls/config.h'
CONFIG_BAK="$CONFIG_H.bak"

# Step 0 - print build environment info
scripts/output_env.sh
echo

# Step 1 - Make and instrumented build for code coverage
export CFLAGS=' --coverage -g3 -O0 '
make clean
cp "$CONFIG_H" "$CONFIG_BAK"
scripts/config.pl full
scripts/config.pl unset MBEDTLS_MEMORY_BACKTRACE
make -j


# Step 2 - Execute the tests
TEST_OUTPUT=out_${PPID}
cd tests

# Step 2a - Unit Tests
perl scripts/run-test-suites.pl -v |tee unit-test-$TEST_OUTPUT
echo

# Step 2b - System Tests
sh ssl-opt.sh |tee sys-test-$TEST_OUTPUT
echo

# Step 2c - Compatibility tests
sh compat.sh |tee compat-test-$TEST_OUTPUT
echo

# Step 3 - Process the coverage report
cd ..
make lcov |tee tests/cov-$TEST_OUTPUT

# Step - Clean up the changes so far
make clean

if [ -f "$CONFIG_BAK" ]; then
    mv "$CONFIG_BAK" "$CONFIG_H"
fi

# Step 3a - Calculate RAM usage
./scripts/memory.sh |tee tests/memory-$TEST_OUTPUT

# Step 3b - Calculate Flash usage
./scripts/footprint.sh |tee tests/footprint-$TEST_OUTPUT

#rm 00-footprint-summary.txt
#rm mbedtls-footprint.zip
#rm size-default.txt
#rm size-psk.txt
#rm size-suite-b.txt
#rm size-thread.txt
#rm size-yotta.txt


# Step 4 - Summarise the test report
echo
echo "========================================================================="
echo "Creating test reports"
echo

cd tests

REPORT_TIMESTAMP="$(date +%s)"
: ${REPORTS_DIR:=./basic-build-tests-reports}
if [ ! -d $REPORTS_DIR ]; then
    mkdir -p "$REPORTS_DIR"
fi

# Steap 4a - Unit tests
echo "Unit tests - tests/scripts/run-test-suites.pl"

PASSED_TESTS=$(tail -n6 unit-test-$TEST_OUTPUT|sed -n -e 's/test cases passed :[\t]*\([0-9]*\)/\1/p'| tr -d ' ')
SKIPPED_TESTS=$(tail -n6 unit-test-$TEST_OUTPUT|sed -n -e 's/skipped :[ \t]*\([0-9]*\)/\1/p'| tr -d ' ')
FAILED_TESTS=$(tail -n6 unit-test-$TEST_OUTPUT|sed -n -e 's/failed :[\t]*\([0-9]*\)/\1/p' |tr -d ' ')

UNIT_TESTS_REPORT="${REPORTS_DIR}/unit_tests_$REPORT_TIMESTAMP"

echo "Passed=$PASSED_TESTS"                                      >> "$UNIT_TESTS_REPORT"
echo "Failed=$FAILED_TESTS"                                      >> "$UNIT_TESTS_REPORT"
echo "Skipped=$SKIPPED_TESTS"                                    >> "$UNIT_TESTS_REPORT"
echo "Executed=$(($PASSED_TESTS + $FAILED_TESTS))"               >> "$UNIT_TESTS_REPORT"
echo "Total=$(($PASSED_TESTS + $FAILED_TESTS + $SKIPPED_TESTS))" >> "$UNIT_TESTS_REPORT"

echo "    Test report written to '$UNIT_TESTS_REPORT'"
echo

# Step 4b - TLS Options tests
echo "TLS Options tests - tests/ssl-opt.sh"

PASSED_TESTS=$(tail -n5 sys-test-$TEST_OUTPUT|sed -n -e 's/.* (\([0-9]*\) \/ [0-9]* tests ([0-9]* skipped))$/\1/p')
SKIPPED_TESTS=$(tail -n5 sys-test-$TEST_OUTPUT|sed -n -e 's/.* ([0-9]* \/ [0-9]* tests (\([0-9]*\) skipped))$/\1/p')
TOTAL_TESTS=$(tail -n5 sys-test-$TEST_OUTPUT|sed -n -e 's/.* ([0-9]* \/ \([0-9]*\) tests ([0-9]* skipped))$/\1/p')
FAILED_TESTS=$(($TOTAL_TESTS - $PASSED_TESTS))

OPTS_TESTS_REPORT="${REPORTS_DIR}/opts_tests_$REPORT_TIMESTAMP"

echo "Passed=$PASSED_TESTS"                      >> "$OPTS_TESTS_REPORT"
echo "Failed=$FAILED_TESTS"                      >> "$OPTS_TESTS_REPORT"
echo "Skipped=$SKIPPED_TESTS"                    >> "$OPTS_TESTS_REPORT"
echo "Executed=$TOTAL_TESTS"                     >> "$OPTS_TESTS_REPORT"
echo "Total=$(($TOTAL_TESTS + $SKIPPED_TESTS))"  >> "$OPTS_TESTS_REPORT"

echo "    Test report written to '$OPTS_TESTS_REPORT'"
echo

# Step 4c - System Compatibility tests
echo "System/Compatibility tests - tests/compat.sh"

PASSED_TESTS=$(tail -n5 compat-test-$TEST_OUTPUT|sed -n -e 's/.* (\([0-9]*\) \/ [0-9]* tests ([0-9]* skipped))$/\1/p')
SKIPPED_TESTS=$(tail -n5 compat-test-$TEST_OUTPUT|sed -n -e 's/.* ([0-9]* \/ [0-9]* tests (\([0-9]*\) skipped))$/\1/p')
EXED_TESTS=$(tail -n5 compat-test-$TEST_OUTPUT|sed -n -e 's/.* ([0-9]* \/ \([0-9]*\) tests ([0-9]* skipped))$/\1/p')
FAILED_TESTS=$(($EXED_TESTS - $PASSED_TESTS))

COMPAT_TESTS_REPORT="$REPORTS_DIR/compat_tests_$REPORT_TIMESTAMP"

echo "Passed=$PASSED_TESTS"                       >> "$COMPAT_TESTS_REPORT"
echo "Failed=$FAILED_TESTS"                       >> "$COMPAT_TESTS_REPORT"
echo "Skipped=$SKIPPED_TESTS"                     >> "$COMPAT_TESTS_REPORT"
echo "Executed=$EXED_TESTS"                       >> "$COMPAT_TESTS_REPORT"
echo "Total=$(($EXED_TESTS + $SKIPPED_TESTS))"    >> "$COMPAT_TESTS_REPORT"
echo

echo "    Test report written to '$COMPAT_TESTS_REPORT'"
echo

# Step 4d - Coverage
echo "Coverage"

LINES_TESTED=$(tail -n3 cov-$TEST_OUTPUT|sed -n -e 's/  lines......: [0-9]*.[0-9]% (\([0-9]*\) of [0-9]* lines)/\1/p')
LINES_TOTAL=$(tail -n3 cov-$TEST_OUTPUT|sed -n -e 's/  lines......: [0-9]*.[0-9]% ([0-9]* of \([0-9]*\) lines)/\1/p')
FUNCS_TESTED=$(tail -n3 cov-$TEST_OUTPUT|sed -n -e 's/  functions..: [0-9]*.[0-9]% (\([0-9]*\) of [0-9]* functions)$/\1/p')
FUNCS_TOTAL=$(tail -n3 cov-$TEST_OUTPUT|sed -n -e 's/  functions..: [0-9]*.[0-9]% ([0-9]* of \([0-9]*\) functions)$/\1/p')

LINES_PERCENT=$((1000*$LINES_TESTED/$LINES_TOTAL))
LINES_PERCENT="$(($LINES_PERCENT/10)).$(($LINES_PERCENT-($LINES_PERCENT/10)*10))"

FUNCS_PERCENT=$((1000*$FUNCS_TESTED/$FUNCS_TOTAL))
FUNCS_PERCENT="$(($FUNCS_PERCENT/10)).$(($FUNCS_PERCENT-($FUNCS_PERCENT/10)*10))"

COVERAGE_REPORT="$REPORTS_DIR/coverage_$REPORT_TIMESTAMP"

echo "Tested lines=$LINES_TESTED"     >> "$COVERAGE_REPORT"
echo "Total lines=$LINES_TOTAL"       >> "$COVERAGE_REPORT"
echo "Tested functions=$FUNCS_TESTED" >> "$COVERAGE_REPORT"
echo "Total functions=$FUNCS_TOTAL"   >> "$COVERAGE_REPORT"
echo

# Step 4e - Write general information about this test run
GENERAL_INFO="$REPORTS_DIR/general_$REPORT_TIMESTAMP"

echo "hash=$(git rev-parse HEAD)" >> "$GENERAL_INFO"

# Step 4f - Write RAM consumption
cp memory-$TEST_OUTPUT "$REPORTS_DIR/memory_$REPORT_TIMESTAMP"

# Step 4g - Write FLASH consumption
cp footprint-$TEST_OUTPUT "$REPORT_DIR/footprint_$REPORT_TIMESTAMP"

#rm unit-test-$TEST_OUTPUT
#rm sys-test-$TEST_OUTPUT
#rm compat-test-$TEST_OUTPUT
#rm cov-$TEST_OUTPUT
#rm memory-$TEST_OTPUT
#rm footprint-$TEST_OUTPUT

cd ..
make clean

if [ -f "$CONFIG_BAK" ]; then
    mv "$CONFIG_BAK" "$CONFIG_H"
fi
