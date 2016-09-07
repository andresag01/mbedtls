#! /usr/bin/env python

import os
import sys
import re
import datetime
import subprocess

REPORTS_DIR    = os.path.join("tests", "basic-build-tests-reports")
REPORT_HISTORY = 10

results = {
    "unit_tests": {
        "Title": "Unit tests - tests/scripts/run-test-suites.pl",
        "Passed"   : [],
        "Failed"   : [],
        "Executed" : [],
        "Total"    : [],
        "Skipped"  : [],
    },
    "compat_tests": {
        "Title": "TLS Options tests - tests/ssl-opt.sh",
        "Passed"   : [],
        "Failed"   : [],
        "Executed" : [],
        "Total"    : [],
        "Skipped"  : [],
    },
    "opts_tests": {
        "Title": "System/Compatibility tests - tests/compat.sh",
        "Passed"   : [],
        "Failed"   : [],
        "Executed" : [],
        "Total"    : [],
        "Skipped"  : [],
    },
}

lines_cov = []
lines_total = []

func_cov = []
func_total = []

commit = []

dates = []

memory = {
    "ram": "",
    "flash": "",
}

def extract_mem_info(memory_filepath, footprint_filepath):
    for title, filepath in [("ram", memory_filepath), ("flash", footprint_filepath)]:
        with open(filepath, "r") as f:
            for line in f:
                memory[title] += line

def extract_data(compat_filepath, coverage_filepath, general_filepath,
    opts_tests_filepath, unit_tests_filepath):

    for name, path in [("compat_tests", compat_filepath), ("unit_tests", unit_tests_filepath),
        ("opts_tests", opts_tests_filepath)]:
        with open(path, "r") as f:
            for line in f:
                m = re.match("(?P<key>[A-Za-z ]+)=(?P<val>[0-9]+)", line)
                key = m.group("key")
                val = m.group("val")

                results[name][key].append(int(val))

    with open(general_filepath, "r") as f:
        for line in f:
            m = re.match("(?P<key>[A-Za-z ]+)=(?P<val>[0-9a-fA-F]+)", line)
            if "hash" == m.group("key"):
                commit.append(m.group("val"))
            else:
                print "Unknown key {0} when parsing {1}".format(m.group("key"),
                    general_filepath)

    with open(coverage_filepath, "r") as f:
        for line in f:
            m = re.match("(?P<key>[A-Za-z ]+)=(?P<val>[0-9]+)", line)
            key = m.group("key")
            val = m.group("val")

            if key == "Tested lines":
                lines_cov.append(int(val))
            elif key == "Total lines":
                lines_total.append(int(val))
            elif key == "Tested functions":
                func_cov.append(int(val))
            elif key == "Total functions":
                func_total.append(int(val))
            else:
                print "Unknown key {0} when parsing {1}".format(key, coverage_filepath)

def write_report(timestamp):
    # Write the ascii report
    with open(os.path.join(REPORTS_DIR, "report_{0}".format(timestamp)), "w") as f:
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_executed = 0
        total_tests = 0

        readable_date = dates[0].strftime('%d/%m/%Y %H:%M:%S')
        week          = "{0}w{1}".format(dates[0].strftime('%y'),
            dates[0].isocalendar()[1])

        f.write("=========================================================================\n")
        f.write("Test general information\n\n")
        f.write("Git commit hash    : {0}\n".format(commit[0]))
        f.write("Date               : {0} ({1})\n".format(readable_date, week))
        f.write("\n")

        f.write("=========================================================================\n")
        f.write("Test Report Summary\n\n")
        for name in ["compat_tests", "unit_tests", "opts_tests"]:
            f.write("{0}\n".format(results[name]["Title"]))
            f.write("Passed             : {0}\n".format(results[name]["Passed"  ][0]))
            f.write("Failed             : {0}\n".format(results[name]["Failed"  ][0]))
            f.write("Skipped            : {0}\n".format(results[name]["Executed"][0]))
            f.write("Total exec'd tests : {0}\n".format(results[name]["Total"   ][0]))
            f.write("Total avail tests  : {0}\n".format(results[name]["Skipped" ][0]))
            f.write("\n")

            total_passed   += results[name]["Passed"  ][0]
            total_failed   += results[name]["Failed"  ][0]
            total_skipped  += results[name]["Executed"][0]
            total_executed += results[name]["Total"   ][0]
            total_tests    += results[name]["Skipped" ][0]

        f.write("-------------------------------------------------------------------------\n")
        f.write("Total tests\n")
        f.write("Passed             : {0}\n".format(total_passed  ))
        f.write("Failed             : {0}\n".format(total_failed  ))
        f.write("Skipped            : {0}\n".format(total_skipped ))
        f.write("Total exec'd tests : {0}\n".format(total_executed))
        f.write("Total avail tests  : {0}\n".format(total_tests   ))
        f.write("\n")

        f.write("=========================================================================\n")
        f.write("Coverage\n")
        f.write("Lines tested       : {0} of {1} ({2:0.2f}%)\n".format(lines_cov[0],
            lines_total[0], float(lines_cov[0] * 100) / float(lines_total[0])))
        f.write("Functions tested   : {0} of {1} ({2:0.2f}%)\n".format(func_cov[0],
            func_total[0], float(func_cov[0] * 100) / float(func_total[0])))
        f.write("\n")

        f.write("=========================================================================\n")
        f.write("RAM usage\n")
        f.write(memory["ram"])
        f.write("\n")

        f.write("=========================================================================\n")
        f.write("FLASH usage\n")
        f.write(memory["flash"])
        f.write("\n")

        # Stop if we only have history of length 1
        if len(commit) < 2:
            print "History length is 1, cannot create more than basic report"
            sys.exit(0)

        # Get the git stat
        git_command = ["git", "diff", "--stat", commit[1], commit[0]]
        p = subprocess.Popen(git_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            out, err = p.communicate(timeout=5)
        except TimeoutExpired:
            p.kill()
            print "Timeout for git diff --stat expired"
            sys.exit(1)

        f.write("=========================================================================\n")
        f.write("Lines changed\n")
        f.write(git_command)
        f.write("\n")
        f.write(out)
        f.write("\n")

def main():
    # List the contents of the directory and sort them.
    reports = sorted(os.listdir(REPORTS_DIR), reverse=True)
    latest  = None

    # Extract data from the files
    for i, filename in enumerate(reports):
        if i >= REPORT_HISTORY:
            # We have enough data!
            break

        # Get the timestamp that we are processing to infer the name of other files
        m = re.match("unit_tests_(?P<timestamp>[0-9]+)", filename)
        if not m:
            # skip this file
            continue
        elif latest is None:
            latest = m.group("timestamp")

        dates.append(datetime.datetime.fromtimestamp(int(m.group("timestamp"))))
        compat_filepath     = os.path.join(REPORTS_DIR,
                                "compat_tests_{0}".format(m.group("timestamp")))
        coverage_filepath   = os.path.join(REPORTS_DIR,
                                "coverage_{0}".format(m.group("timestamp")))
        general_filepath    = os.path.join(REPORTS_DIR,
                                "general_{0}".format(m.group("timestamp")))
        opts_tests_filepath = os.path.join(REPORTS_DIR,
                                "opts_tests_{0}".format(m.group("timestamp")))
        unit_tests_filepath = os.path.join(REPORTS_DIR,
                                "unit_tests_{0}".format(m.group("timestamp")))
        # Process the files
        extract_data(compat_filepath, coverage_filepath, general_filepath,
            opts_tests_filepath, unit_tests_filepath)


    # Extract data that we just need for last report
    memory_filepath     = os.path.join(REPORTS_DIR,
                            "memory_{0}".format(latest))
    footprint_filepath  = os.path.join(REPORTS_DIR,
                            "footprint_{0}".format(latest))

    extract_mem_info(memory_filepath, footprint_filepath)

    # Write the report
    write_report(latest)

if __name__ == "__main__":
    main()
