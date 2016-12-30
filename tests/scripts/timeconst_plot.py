#! /usr/bin/env python

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import sys
import os

def main(args):
    scatter(args[0], args[1])
    distro(args[0], args[1])

def distro(plots_dir, filenames):
    filenames = filenames.split(",")

    for filename in filenames:
        with open(filename, "r") as istream:
            samples = []
            for line in istream.readlines():
                samples.append(int(line.strip()))
            samples = sorted(samples)

            fig, ax = plt.subplots()
            ax.hist(samples, bins=100)

            plt.tight_layout()
            plt.grid(True)
            plt.savefig(os.path.join(plots_dir, "{0}.png".format(
                        os.path.basename(os.path.splitext(filename)[0]))))

def scatter(plots_dir, filenames):
    filenames = filenames.split(",")
    samples = [[], []]
    means = [[], []]
    medians = [[], []]
    xticks = []
    handles = []
    processed_files = 0

    for filename in filenames:
        with open(filename, "r") as istream:
            cur_samples = []
            for line in istream.readlines():
                cur_samples.append(int(line.strip()))
            samples[0] += [processed_files] * len(cur_samples)
            samples[1] += cur_samples
            means[0].append(processed_files)
            means[1].append(np.mean(cur_samples))
            medians[0].append(processed_files)
            medians[1].append(np.median(cur_samples))
            xticks.append((os.path.basename(os.path.splitext(filename)[0])))
            processed_files += 1

    fig, ax = plt.subplots()
    handles.append(ax.scatter(samples[0], samples[1]))
    ax.set_xticks(range(0, processed_files))
    ax.set_xticklabels(xticks, rotation='vertical')

    # Plot means
    handles.append(ax.scatter(means[0], means[1], color="red"))

    # Plot medians
    handles.append(ax.scatter(medians[0], medians[1], color="green"))

    # Add legend
    ax.legend(handles, ["Sample", "Mean", "Median"], loc="upper left")

    plt.tight_layout()
    plt.grid(True)
    plt.savefig(os.path.join(plots_dir, "scatter.png"))

if __name__ == "__main__":
    main(sys.argv[1:])
