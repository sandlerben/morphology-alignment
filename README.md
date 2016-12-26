# Estimating the meanings of morphemes

This repo contains my Independent Study (CIS099) research project, which I completed under the supervision of Professor Mitch Marcus. The goal of the project was to estimate the meanings of morphemes detected by the Penn unsupervised morphology system. The final product is quite effective given the limitations of the input data.

## Usage Details for align.py

align.py creates a csv representing an estimated alignment of segments (morphemes) and features (meanings). 

```
usage: align.py [-h] [--normalize_by_column]
                [--frequency_threshold FREQUENCY_THRESHOLD]
                feature_file segment_file output_file

positional arguments:
  feature_file         The unimorph feature csv
  segment_file       The segmenter text file
  output_file           The csv file to write

optional arguments:
  --normalize_by_column
                        Normalize by columns. The default behavior is to
                        normalize by row.
  --frequency_threshold FREQUENCY_THRESHOLD
                        Remove all segments with frequency below threshold.
                        The default behavior is to remove root segments.
```

## Structure of output file

The output csv is a matrix with each row corresponding to a segment and each feature column corresponding to the likelihood that segment corresponds to that feature. For examples, open the files in the demo/ folder of the repo.

### Which segments are included? 

Under the default mode, roots are removed from the segment list before the data is analyzed. A segment is considered a root if it occurs the fewest number of times within a word. In other words, if the word A-B-C maps to segments A, B, and C, and A occurs the fewest number of times over the entire dataset, then A will be removed.

Alternatively, a minimum frequency threshold can be specified so that all segments which occur less than the frequency are removed from the segment list before the data is analyzed.

### How are likelihoods (scores) computed?

For a segment `s` and a feature `f`, `output[s][f]` is first set to the number of times `s` occurs with `f`. Following, `output[s][f]` is divided by the total number of words that `s` occurs in, so `output[s][f]` is the fraction of words with `s` which corresponds to `f`. Alternatively, if the `--normalize_by_column` flag is given, columns are divided by their sums so that they sum to 1. 

## Analysis of results

There are two queries which can be answered using this utility.

1. For a segment, what does it mean? (What features does the segment correspond to?)
2. For a feature, what segments are most likely to correspond to it?

Take a look at the demo csv, the result of running align.py with default options and then filtering the output down to segments which occur at least 100 times (since the data is much noiser for low-occurence segments). 

Query (1) is easily answered using any segment row. For example, take a look at the row for “s”. The top features for “s” are “Number: PL” (0.89) and “Part of Speech: N” (.89). 

Query (2) is also easily answered using any feature column. For example, the top segments for the “Number: PL” column are “ers” (1), “rs” (.99), “es” (.96), and “s” (.89).

## Experiment to detect allomorphs

Ideally, the alignment utility would detect and merge allomorphs (e.g. “s” and “es” would be collapsed into one morpheme). I experiment with this idea and had some positive results.

If two morphemes are allomorphs, then they should never occur in the same location in a word. For example, since “s” and “es” are allomorphs, it’s highly unlikely that there would be a word “pianoes” given that there is a word “pianos.” This can be framed as a pointwise mutual information (PMI) problem. PMI is the amount of information obtained about one event through another event. It is log(p(x, y)/(p(x)p(y)). In this case, p(x) is the probability that x occurs in a word, p(y) is the probability that y occurs in a word, and p(x, y) is the probability that x and y are in the same position in a word (in other words, if , e.g. pianoes - {es} = pianos - {s}).
