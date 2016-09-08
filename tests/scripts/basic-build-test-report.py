#! /usr/bin/env python

import os
import sys
import re
import datetime
import time
import subprocess
import matplotlib.pyplot as plt

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
    total_passed = []
    total_failed = []
    total_skipped = []
    total_executed = []
    total_tests = []

    for i in range(len(commit)):
        passed   = 0
        failed   = 0
        skipped  = 0
        executed = 0
        tests    = 0

        for key in results.keys():
            passed   += results[key]["Passed"][i]
            failed   += results[key]["Failed"][i]
            skipped  += results[key]["Skipped"][i]
            executed += results[key]["Executed"][i]
            tests    += results[key]["Total"][i]

        total_passed.append(passed)
        total_failed.append(failed)
        total_skipped.append(skipped)
        total_executed.append(executed)
        total_tests.append(tests)

    # Write the ascii report
    with open(os.path.join(REPORTS_DIR, "report_{0}".format(timestamp)), "w") as f:
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

        f.write("-------------------------------------------------------------------------\n")
        f.write("Total tests\n")
        f.write("Passed             : {0}\n".format(total_passed[0]  ))
        f.write("Failed             : {0}\n".format(total_failed[0]  ))
        f.write("Skipped            : {0}\n".format(total_skipped[0] ))
        f.write("Total exec'd tests : {0}\n".format(total_executed[0]))
        f.write("Total avail tests  : {0}\n".format(total_tests[0]   ))
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

        f.write("=========================================================================\n")
        f.write("Lines changed\n")
        f.write(" ".join(git_command))
        f.write("\n")
        f.write(p.communicate()[0])
        f.write("\n")

        # Plot the graphs
        total_passed.reverse()
        total_failed.reverse()
        total_skipped.reverse()
        total_executed.reverse()
        total_tests.reverse()
        ticks_dates = \
            ["{0}w{1}".format(g.strftime('%y'), g.isocalendar()[1]) for g in dates]

        total_bars = len(commit)
        bar_width  = 0.35
        ind        = range(total_bars)

        passed_bar = plt.bar(ind, total_passed, bar_width, color='r')
        failed_bar = plt.bar(ind, total_failed, bar_width, color='b',
            bottom=total_passed)
        skipped_bar = plt.bar(ind, total_skipped, bar_width, color='g',
            bottom=[x + y for x, y in zip(total_passed, total_failed)])

        plt.ylabel("Number of tests")
        plt.title("mbed TLS test resutls")
        plt.xticks([float(w) + bar_width / 2 for w in ind], ticks_dates, size="small")
        plt.legend([passed_bar[0], failed_bar[0], skipped_bar[0]],
            ["Passed", "Failed", "Skipped"], bbox_to_anchor=(1.05, 1),
            loc=2, borderaxespad=0.)
        fig = plt.gcf()
        fig.set_size_inches(26.0, 10.5)
        fig.savefig(os.path.join(REPORTS_DIR,
            "barchart_{0}.png".format(int(time.mktime(dates[0].timetuple())))))

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
