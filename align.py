import argparse
import csv
import json
import collections
import operator
import math


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
                        feature_and_instance = '{}: {}'.format(
                            feature_name, feature_mapping[feature_name])
                        segment_feature_counts[segment][
                            feature_and_instance] += 1

    return segment_feature_counts


# Remove roots and combine allomorphs.
def remove_roots_from_segment_feature_counts(segment_feature_counts, word_to_features, word_to_segments):
    # segment -> global count
    global_segment_counts = collections.defaultdict(float)

    # first, compute global_segment_counts
    for word in word_to_features:
        if word in word_to_segments:
            segments_for_word = word_to_segments[word]
            for segment in segments_for_word:
                global_segment_counts[segment] += 1

    # second, remove roots from segment_feature_counts
    # TODO: rethink this a lot.
    for word in word_to_features:
        if word in word_to_segments:
            segments_for_word = word_to_segments[word]
            segments_to_counts = {segment: global_segment_counts[segment] for segment in segments_for_word}
            min_segment = min(segments_to_counts, key=segments_to_counts.get)
            if min_segment in segment_feature_counts:
                del segment_feature_counts[min_segment]

    return segment_feature_counts


def remove_low_frequency_segments(segment_feature_counts, word_to_features, word_to_segments, threshold=100):
    # segment -> global count
    global_segment_counts = collections.defaultdict(int)

    # first, compute global_segment_counts
    for word in word_to_features:
        if word in word_to_segments:
            segments_for_word = word_to_segments[word]
            for segment in segments_for_word:
                global_segment_counts[segment] += 1

    # second, remove segments with counts below threshold
    for segment in global_segment_counts:
        if global_segment_counts[segment] < threshold:
            del segment_feature_counts[segment]

    return segment_feature_counts


def combine_allomorphs(segment_feature_counts, word_to_features, word_to_segments):
    subword_to_segments_missing = collections.defaultdict(set)

    for word in word_to_segments:
        segments = word_to_segments[word]
        if len(segments) > 1:
            for i in xrange(len(segments)):
                if ''.join(segments[0:i]) + ''.join(segments[i + 1:]) == 'bak':
                subword_to_segments_missing[''.join(segments[0:i]) + ''.join(segments[i + 1:])].add(segments[i])

    # compute mutual information for segment pairs which occur in the same word
    segment_pair_counts = collections.defaultdict(float)
    segment_pair_mutual_info = collections.defaultdict(float)

    for subword in subword_to_segments_missing:
        segments_missing = list(subword_to_segments_missing[subword])
        for i in xrange(len(segments_missing)):
            for j in xrange(i, len(segments_missing)):
                seg_one = segments_missing[i]
                seg_two = segments_missing[j]
                if seg_one != seg_two and seg_one in segment_feature_counts and seg_two in segment_feature_counts: # TODO: hack
                    segment_pair_counts[min(seg_one, seg_two), max(seg_one, seg_two)] += 1

    # compute global_segment_counts
    for segment in segment_feature_counts:
        sum_of_feature_counts = 0
        for feature_instance in segment_feature_counts[segment]:
            sum_of_feature_counts += segment_feature_counts[segment][feature_instance]
        global_segment_counts[segment] = sum_of_feature_counts

    for seg_one, seg_two in segment_pair_counts:
        times_together = segment_pair_counts[seg_one, seg_two]
        times_for_one = global_segment_counts[seg_one]
        times_for_two = global_segment_counts[seg_two]
        segment_pair_mutual_info[seg_one, seg_two] = math.log((times_together * len(word_to_segments)) / (times_for_one * times_for_two), 2)

    for key, value in sorted(segment_pair_mutual_info.items(), key=lambda x: x[1]):
        print 'pair {} has mutual information {}'.format(key, value)


def normalize_segment_feature_counts_by_feature_and_segment(segment_feature_counts):
    # feature instance (as string like feature: instance) -> global count
    global_feature_counts = collections.defaultdict(int)

    # first, compute global_feature_counts
    for segment in segment_feature_counts:
        for feature_instance in segment_feature_counts[segment]:
            global_feature_counts[feature_instance] += segment_feature_counts[
                segment][feature_instance]

    # segment -> global count
    global_segment_counts = collections.defaultdict(int)

    # second, compute global_segment_counts
    for segment in segment_feature_counts:
        sum_of_feature_counts = 0
        for feature_instance in segment_feature_counts[segment]:
            sum_of_feature_counts += segment_feature_counts[segment][feature_instance]
        global_segment_counts[segment] = sum_of_feature_counts

    # third, normalize segment_feature_counts
    for segment in segment_feature_counts:
        for feature_instance in segment_feature_counts[segment]:
            segment_feature_counts[segment][feature_instance] /= (float(
                global_feature_counts[feature_instance]) * float(global_segment_counts[segment]))

    return segment_feature_counts

def normalize_segment_feature_counts_by_feature(segment_feature_counts):
    # feature instance (as string like feature: instance) -> global count
    global_feature_counts = collections.defaultdict(int)

    # first, compute global_feature_counts
    for segment in segment_feature_counts:
        for feature_instance in segment_feature_counts[segment]:
            global_feature_counts[feature_instance] += segment_feature_counts[
                segment][feature_instance]

    # second, normalize segment_feature_counts
    for segment in segment_feature_counts:
        for feature_instance in segment_feature_counts[segment]:
            segment_feature_counts[segment][feature_instance] /= float(
                global_feature_counts[feature_instance])

    return segment_feature_counts


def normalize_segment_feature_counts_by_segment(segment_feature_counts):
    # normalize segment_feature_counts
    for segment in segment_feature_counts:
        sum_of_feature_counts = 0
        for feature_instance in segment_feature_counts[segment]:
            sum_of_feature_counts += segment_feature_counts[segment][feature_instance]
        for feature_instance in segment_feature_counts[segment]:
            segment_feature_counts[segment][feature_instance] /= float(sum_of_feature_counts)

    return segment_feature_counts


def write_segment_feature_counts(output_file, segment_feature_counts, word_to_features, word_to_segments):
    # segment -> global count
    global_segment_counts = collections.defaultdict(int)

    # first, compute global_segment_counts
    for word in word_to_features:
        if word in word_to_segments:
            segments_for_word = word_to_segments[word]
            for segment in segments_for_word:
                global_segment_counts[segment] += 1

    with open(output_file, 'w') as csvfile:
        fieldnames_set = set()
        rows = []  # list of dictionaries. each dictionary is one segment.

        for segment, row in segment_feature_counts.iteritems():
            for fieldname in row:
                fieldnames_set.add(fieldname)

            row['Segment'] = segment
            row['Count'] = global_segment_counts[segment]
            rows.append(row)

        rows.sort(key=operator.itemgetter('Segment'))

        fieldnames = ['Segment']
        fieldnames.extend(sorted(list(fieldnames_set)))
        fieldnames.append('Count')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--feature_file')
    parser.add_argument('--segment_file')
    parser.add_argument('--output_file')
    args = parser.parse_args()

    word_to_features = get_word_to_features(args.feature_file)
    word_to_segments = get_word_to_segments(args.segment_file)
    segment_feature_counts = get_segment_feature_counts(word_to_features,
                                                        word_to_segments)
    # segment_feature_counts = remove_low_frequency_segments(segment_feature_counts, word_to_features, word_to_segments, threshold=100)
    # segment_feature_counts = remove_roots_from_segment_feature_counts(segment_feature_counts, word_to_features, word_to_segments)
    segment_feature_counts = combine_allomorphs(segment_feature_counts, word_to_features, word_to_segments)
    # normalized_segment_feature_counts = normalize_segment_feature_counts_by_feature(
    #     segment_feature_counts)
    # write_segment_feature_counts(args.output_file, normalized_segment_feature_counts, word_to_features, word_to_segments)
