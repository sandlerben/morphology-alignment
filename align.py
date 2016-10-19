import argparse
import csv
import json
import collections


def get_word_to_features(wfile):
    with open(wfile, 'rb') as f:
        reader = csv.reader(f)

        first_row = next(reader)
        index_of_words = first_row.index('cell_value')

        features = first_row[0:index_of_words]

        # word -> feature_name -> feature_instantiation
        word_to_features = collections.defaultdict(list)

        for line in reader:
            word = line[index_of_words]
            feature_name_to_instantiation = {
                features[i]: line[i]
                for i in xrange(index_of_words) if line[i].strip()
            }
            word_to_features[word].append(feature_name_to_instantiation)

    return word_to_features


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--wfile')
    args = parser.parse_args()
    print json.dumps(get_word_to_features(args.wfile))
