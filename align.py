import argparse
import csv
import json
import collections
import operator


def get_word_to_features(feature_file):
    '''
    Given the unimorph feature csv, returns a mapping of words to features to
    feature instantiations

    feature_file: unimorph feature csv
    '''

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
    '''
    Given the segmenter text file, returns a mapping of words to segments

    segment_file: segmenter text file
    '''

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
    '''
    Given a mapping from word to features and a mapping from word to segments,
    returns a mapping from segments to feature instances to counts

    word_to_features: mapping of words to features
    word_to_segments: mapping of words to segments
    '''

    # segment -> feature instance (as string like feature: instance) -> count
    segment_feature_counts = collections.defaultdict(
        lambda: collections.defaultdict(int))

    for word in word_to_features:
        if word in word_to_segments:
            segments_for_word = word_to_segments[word]
            for segment in segments_for_word:
                for feature_mapping in word_to_features[word]:
                    for feature_name in feature_mapping:
                        feature_and_instance = '{}: {}'.format(
                            feature_name, feature_mapping[feature_name])
                        segment_feature_counts[segment][
                            feature_and_instance] += 1

    return segment_feature_counts


def remove_roots_from_segment_feature_counts(
        segment_feature_counts, word_to_features, word_to_segments):
    '''
    Given a mapping from segments to feature instances to counts, modify that
    mapping in-place to remove all 'roots', or segments which occur the fewest
    number of times within a word. In other words, if the word ABC maps to
    segments A, B, and C, and A occurs the fewest number of times over the
    entire dataset, then A will be removed from segment_feature_counts.

    word_to_features: mapping of words to features
    word_to_segments: mapping of words to segments
    segment_feature_counts: mapping from segments to feature instances to counts
    '''

    # segment -> global count
    global_segment_counts = collections.defaultdict(int)

    # first, compute global_segment_counts
    for word in word_to_features:
        if word in word_to_segments:
            segments_for_word = word_to_segments[word]
            for segment in segments_for_word:
                global_segment_counts[segment] += 1

    # second, remove roots from segment_feature_counts
    for word in word_to_features:
        if word in word_to_segments:
            segments_for_word = word_to_segments[word]
            segments_to_counts = {
                segment: global_segment_counts[segment]
                for segment in segments_for_word
            }
            min_segment = min(segments_to_counts, key=segments_to_counts.get)
            if min_segment in segment_feature_counts:
                del segment_feature_counts[min_segment]

    return segment_feature_counts


def remove_low_frequency_segments(segment_feature_counts,
                                  word_to_features,
                                  word_to_segments,
                                  threshold=100):
    '''
    Given a mapping from segments to feature instances to counts, modify that
    mapping in-place to remove all segments which occur fewer than `threshold`
    times.

    word_to_features: mapping of words to features
    word_to_segments: mapping of words to segments
    segment_feature_counts: mapping from segments to feature instances to counts
    threshold: segments which occur with frequency fewer than this number are
    removed.
    '''

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
            if segment in segment_feature_counts:
                del segment_feature_counts[segment]

    return segment_feature_counts


def normalize_segment_feature_counts_by_feature(segment_feature_counts):
    '''
    Given a mapping from segments to feature instances to counts, modify that
    mapping in-place to normalize each feature column so that they each sum to
    1.

    segment_feature_counts: mapping from segments to feature instances
    '''

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


def normalize_segment_feature_counts_by_segment(segment_feature_counts, word_to_features, word_to_segments):
    '''
    Given a mapping from segments to feature instances to counts, modify that
    mapping in-place to normalize each segment row so that they each sum to 1.

    segment_feature_counts: mapping from segments to feature instances to counts
    '''

    # segment -> global count
    global_segment_counts = collections.defaultdict(int)

    # first, compute global_segment_counts
    for word in word_to_features:
        if word in word_to_segments:
            segments_for_word = word_to_segments[word]
            for segment in segments_for_word:
                global_segment_counts[segment] += 1

    # normalize segment_feature_counts
    for segment in segment_feature_counts:
        for feature_instance in segment_feature_counts[segment]:
            segment_feature_counts[segment][feature_instance] /= float(
                global_segment_counts[segment])
            segment_feature_counts[segment][feature_instance] = min(
                segment_feature_counts[segment][feature_instance], 1)

    return segment_feature_counts


def write_segment_feature_counts(output_file, segment_feature_counts,
                                 word_to_features, word_to_segments):
    '''
    Given a mapping from segments to feature instances to counts and an output
    file, write a csv where rows correspond to segments and columns correspond
    to feature counts.

    output_file: the csv file to write to
    word_to_features: mapping of words to features
    word_to_segments: mapping of words to segments
    segment_feature_counts: mapping from segments to feature instances
    '''

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
    parser = argparse.ArgumentParser(description='Creates a csv representing an estimated alignment of segments (morphemes) and features (meanings). The csv is a matrix where each row corresponds to a segment and each column corresponds to the likelihood that segment corresponds to that feature.')
    parser.add_argument('feature_file', help='The unimorph feature csv')
    parser.add_argument('segment_file', help='The segmenter text file')
    parser.add_argument('output_file', help='The csv file to write')
    parser.add_argument("--normalize_by_column", help='Normalize by columns. The default behavior is to normalize by row.', action="store_true")
    parser.add_argument('--frequency_threshold', type=int, help='Remove all segments with frequency below threshold. The default behavior is to remove root segments.')

    args = parser.parse_args()

    word_to_features = get_word_to_features(args.feature_file)
    word_to_segments = get_word_to_segments(args.segment_file)
    segment_feature_counts = get_segment_feature_counts(word_to_features,
                                                        word_to_segments)
    if args.frequency_threshold:
        print 'removing below {}'.format(args.frequency_threshold)
        segment_feature_counts = remove_low_frequency_segments(segment_feature_counts, word_to_features, word_to_segments, threshold=args.frequency_threshold)
    else:
        segment_feature_counts = remove_roots_from_segment_feature_counts(segment_feature_counts, word_to_features, word_to_segments)

    if args.normalize_by_column:
        print 'normalizing by column'
        normalized_segment_feature_counts = normalize_segment_feature_counts_by_feature(segment_feature_counts)
    else:
        normalized_segment_feature_counts = normalize_segment_feature_counts_by_segment(segment_feature_counts, word_to_features, word_to_segments)
    write_segment_feature_counts(
        args.output_file, normalized_segment_feature_counts, word_to_features,
        word_to_segments)
