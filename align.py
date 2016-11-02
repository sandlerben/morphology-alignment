import argparse
import csv
import json
import collections
import copy
import operator


def get_word_to_features(feature_file):
    with open(feature_file, 'rb') as f:
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


def get_word_to_segments(segment_file):
    with open(segment_file, 'r') as f:
        # word -> word segments
        word_to_segments = {}
        for line in f:
            line_split_tabs = line.split('\t')
            word = line_split_tabs[0]
            segments = line_split_tabs[1].split()
            word_to_segments[word] = segments
    return word_to_segments


def get_segment_feature_counts(word_to_features, word_to_segments):
    # segment -> feature instance (as string like feature: instance) -> count
    segment_feature_counts = collections.defaultdict(
        lambda: collections.defaultdict(int))

    for word in word_to_features:
        if word in word_to_segments:  # TODO: Be more smart about this.
            segments_for_word = word_to_segments[word]
            for segment in segments_for_word:
                for feature_mapping in word_to_features[word]:
                    for feature_name in feature_mapping:
                        for feature_instance in feature_mapping[feature_name]:
                            feature_and_instance = '{}: {}'.format(
                                feature_name, feature_instance)
                            segment_feature_counts[segment][
                                feature_and_instance] += 1

    return segment_feature_counts


def normalize_segment_feature_counts(segment_feature_counts):
    segment_feature_counts = copy.deepcopy(segment_feature_counts)

    # feature instance (as string like feature: instance) -> global count
    global_feature_counts = collections.defaultdict(int)

    for segment in segment_feature_counts:
        for feature_instance in segment_feature_counts[segment]:
            global_feature_counts[feature_instance] += segment_feature_counts[
                segment][feature_instance]

    for segment in segment_feature_counts:
        for feature_instance in segment_feature_counts[segment]:
            segment_feature_counts[segment][feature_instance] /= float(
                global_feature_counts[feature_instance])

    return segment_feature_counts


def write_segment_feature_counts(segment_feature_counts):
    segment_feature_counts = copy.deepcopy(segment_feature_counts)

    with open('out.csv', 'w') as csvfile:
        fieldnames_set = set()
        rows = []  # list of dictionaries. each dictionary is one segment.

        for segment, row in segment_feature_counts.iteritems():
            for fieldname in row:
                fieldnames_set.add(fieldname)

            row['Segment'] = segment
            rows.append(row)

        rows.sort(key=operator.itemgetter('Segment'))

        fieldnames = ['Segment']
        fieldnames.extend(sorted(list(fieldnames_set)))
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--feature_file')
    parser.add_argument('--segment_file')
    args = parser.parse_args()

    word_to_features = get_word_to_features(args.feature_file)
    word_to_segments = get_word_to_segments(args.segment_file)
    segment_feature_counts = get_segment_feature_counts(word_to_features,
                                                        word_to_segments)
    normalized_segment_feature_counts = normalize_segment_feature_counts(
        segment_feature_counts)
    write_segment_feature_counts(normalized_segment_feature_counts)
    print normalized_segment_feature_counts['ed']
