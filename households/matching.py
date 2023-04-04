from datetime import datetime

import numpy as np
import pandas as pd
import recordlinkage
import textdistance
import usaddress
from recordlinkage.base import BaseCompareFeature

MATCH_THRESHOLD = 0.8
FN_WEIGHT = 0.2
PHONE_WEIGHT = 0.15
ADDR_WEIGHT = 0.35
ZIP_WEIGHT = 0.3


def addr_parse(addr):
    address_dict = {
        "number": "",
        "street": "",
        "suffix": "",
        "prefix": "",
        "value": "",
    }

    try:
        addr_tuples = usaddress.parse(addr)
    except Exception:
        return address_dict

    for pair in addr_tuples:
        if pair[1] == "AddressNumber":
            address_dict["number"] = pair[0]
        elif pair[1] == "StreetName":
            address_dict["street"] = pair[0]
        elif pair[1] == "StreetNamePostType":
            address_dict["suffix"] = pair[0]
        elif pair[1] == "OccupancyType":
            address_dict["prefix"] = pair[0]
        elif pair[1] == "OccupancyIdentifier":
            address_dict["value"] = pair[0]
    return address_dict


# Python version of FRIL matchStreetName functionality
# addr1 and addr2 are dicts that were returned from addr_parse
def address_distance(addr1, addr2):
    score = 0
    secondary_score = 0

    # Change weights based on existence of second level address
    if (
        not addr1["prefix"]
        and not addr2["prefix"]
        and not addr1["value"]
        and not addr2["value"]
    ):
        weight_number = 0.5
        weight_street_name = 0.5
        weight_secondary = 0
    else:
        weight_number = 0.3
        weight_street_name = 0.5
        weight_secondary = 0.2

    if addr1["number"] and addr2["number"]:
        score += weight_number * textdistance.hamming.normalized_similarity(
            addr1["number"], addr2["number"]
        )

    max_score_str = 0
    if addr1["street"] and addr2["street"]:
        # Try perfect match
        if addr1["suffix"] and addr2["suffix"]:
            max_score_str = (
                textdistance.jaro_winkler(addr1["street"], addr2["street"]) * 0.8
            )
            if max_score_str:
                max_score_str += (
                    textdistance.jaro_winkler(addr1["suffix"], addr2["suffix"]) * 0.2
                )
        # Try removing either suffix
        if addr1["suffix"]:
            max_score_str = max(
                max_score_str,
                textdistance.jaro_winkler(
                    addr1["street"] + " " + addr1["suffix"], addr2["street"]
                ),
            )
        if addr2["suffix"]:
            max_score_str = max(
                max_score_str,
                textdistance.jaro_winkler(
                    addr2["street"] + " " + addr2["suffix"], addr1["street"]
                ),
            )
        # Try ignoring suffixes but adjust value by 0.7
        adjustment = 1.0 if not addr1["suffix"] and not addr2["suffix"] else 0.7
        max_score_str = max(
            max_score_str,
            textdistance.jaro_winkler(addr1["street"], addr2["street"]) * adjustment,
        )
    else:
        # No street name in one address or both, test each with prefix of other
        if addr1["street"] and addr2["suffix"]:
            max_score_str = max(
                max_score_str,
                textdistance.jaro_winkler(
                    addr1["street"] + " " + addr1["suffix"], addr2["suffix"]
                )
                * 0.7,
            )
            max_score_str = max(
                max_score_str,
                textdistance.jaro_winkler(addr1["street"], addr2["suffix"]) * 0.7,
            )
        if addr2["street"] and addr1["suffix"]:
            max_score_str = max(
                max_score_str,
                textdistance.jaro_winkler(
                    addr2["street"] + " " + addr2["suffix"], addr1["suffix"]
                )
                * 0.7,
            )
            max_score_str = max(
                max_score_str,
                textdistance.jaro_winkler(addr2["street"], addr1["suffix"]) * 0.7,
            )
        if (
            not addr1["street"]
            and not addr2["street"]
            and addr1["suffix"]
            and addr1["street"]
        ):
            max_score_str = max(
                max_score_str,
                textdistance.jaro_winkler(addr1["suffix"], addr2["suffix"]) * 0.1,
            )

    if max_score_str:
        score += max_score_str * weight_street_name

    # Second level score if something to compare, else leave secondary_score = 0
    if (addr1["prefix"] and addr2["prefix"]) or (addr1["value"] and addr2["value"]):
        max_score_sec = 0
        if addr1["value"] and addr2["value"]:
            if addr1["prefix"] and addr2["prefix"]:
                max_score_sec = (
                    textdistance.jaro_winkler(addr1["value"], addr2["value"]) * 0.8
                )
                max_score_sec += (
                    textdistance.jaro_winkler(addr1["prefix"], addr2["prefix"]) * 0.2
                )
            if addr1["prefix"]:
                max_score_sec = max(
                    max_score_sec,
                    textdistance.jaro_winkler(
                        addr1["prefix"] + " " + addr1["value"], addr2["value"]
                    ),
                )
            if addr2["prefix"]:
                max_score_sec = max(
                    max_score_sec,
                    textdistance.jaro_winkler(
                        addr2["prefix"] + " " + addr2["value"], addr1["value"]
                    ),
                )
            adjustment_sec = 1 if not addr1["prefix"] and not addr2["prefix"] else 0.7
            max_score_sec = max(
                max_score_sec,
                textdistance.jaro_winkler(addr1["value"], addr2["value"])
                * adjustment_sec,
            )
        else:
            if addr1["value"]:
                max_score_sec = max(
                    max_score_sec,
                    textdistance.jaro_winkler(
                        addr1["prefix"] + addr1["value"], addr2["prefix"]
                    )
                    * 0.6,
                )
                max_score_sec = max(
                    max_score_sec,
                    textdistance.jaro_winkler(addr1["value"], addr2["prefix"]) * 0.6,
                )
            if addr2["value"]:
                max_score_sec = max(
                    max_score_sec,
                    textdistance.jaro_winkler(
                        addr2["prefix"] + addr2["value"], addr1["prefix"]
                    )
                    * 0.6,
                )
                max_score_sec = max(
                    max_score_sec,
                    textdistance.jaro_winkler(addr2["value"], addr1["prefix"]) * 0.6,
                )
        max_score_sec = max(
            max_score_sec,
            textdistance.jaro_winkler(
                addr1["prefix"] + addr1["value"], addr2["prefix"] + addr2["value"]
            )
            * 0.8,
        )
        if max_score_sec:
            secondary_score = max_score_sec

    # See if simple string compare of all things combined
    # with a 0.6 adjustment is better
    a1 = addr1["household_street_address"]
    a2 = addr2["household_street_address"]
    score = max(
        score,
        textdistance.jaro_winkler(a1, a2) * (weight_number + weight_street_name) * 0.6,
    ) + (secondary_score * weight_secondary)
    return score


# https://github.com/J535D165/recordlinkage/blob/master/recordlinkage/compare.py
class AddressComparison(BaseCompareFeature):
    """Compare the record pairs as Addresses.
    This class is used to compare records using custom address-based logic.
    ----------
    left_on : str or int
        Field name to compare in left DataFrame.
    right_on : str or int
        Field name to compare in right DataFrame.
    """

    name = "address"
    description = "Compare attributes of record pairs."

    def __init__(self, left_on, right_on, label=None):
        super(AddressComparison, self).__init__(left_on, right_on, label=label)

    def _compute_vectorized(self, s1, s2):
        # https://github.com/J535D165/recordlinkage/blob/5b3230f5cff92ef58968eedc451735e972035793/recordlinkage/algorithms/string.py
        conc = pd.Series(list(zip(s1, s2)))

        def comp_address_apply(x):
            try:
                return address_distance(x[0], x[1])
            except Exception as err:
                if pd.isnull(x[0]) or pd.isnull(x[1]):
                    return np.nan
                else:
                    raise err

        c = conc.apply(comp_address_apply)
        return c


def get_household_matches(pii_lines, split_factor=4, debug=False):
    # indexing step defines the pairs of records for comparison
    # indexer.full() does a full n^2 comparison, but we can do better
    indexer = recordlinkage.Index()
    # use two block indexes to reduce the number of candidates
    # while still retaining enough candidates to identify real households.
    # a block only on zip could work, but seems to run into memory issues
    # note sortedneighborhood on zip probably doesn't make sense
    # (zip codes in a geographic area will be too similar)
    # but if data is dirty then blocks may discard typos

    indexer.block(["household_zip", "street"])
    indexer.block(["household_zip", "family_name"])

    candidate_links = None
    # break up the dataframe into subframes,
    # and iterate over every pair of subframes.
    # we improve performance somewhat by only comparing looking forward,
    # that is, only comparing a given set of rows
    # against rows with higher indices.
    for subset_A in np.array_split(pii_lines, split_factor):
        first_item_in_A = subset_A.index.min()
        # don't compare against earlier items
        # Note: this assumes that the index is the row number
        # (NOT the record_id/patid) and the df is sequential
        # this is currently the case in households.py#parse_source_file()
        lines_to_compare = pii_lines[first_item_in_A:]

        # pick a sub split factor to give us ~same size subset_A and subset_B.
        # the idea is that there's some implicit overhead to splitting,
        # so don't split more tha necessary
        sub_split_factor = int(len(lines_to_compare) / len(subset_A))
        for subset_B in np.array_split(lines_to_compare, sub_split_factor):
            if debug:
                print(
                    f"[{datetime.now()}]  Indexing rows "
                    f"[{subset_A.index.min()}..{subset_A.index.max()}]"
                    " against "
                    f"[{subset_B.index.min()}..{subset_B.index.max()}]"
                )

            pairs_subset = indexer.index(subset_A, subset_B)

            if candidate_links is None:
                candidate_links = pairs_subset
            else:
                candidate_links = candidate_links.append(pairs_subset)

    # now we have to remove duplicate and invalid pairs
    # e.g. (1, 2) and (2, 1) should not both be in the list
    #      and (1, 1) should not be in the list
    # the simple approach is just take the items where a < b

    # unfortunately we have to loop it through a dataframe to drop items
    clf = candidate_links.to_frame()
    clf = clf[clf[0] < clf[1]]
    candidate_links = pd.MultiIndex.from_frame(clf)

    if debug:
        print(f"[{datetime.now()}] Found {len(candidate_links)} candidate pairs")

    # Comparison step performs the defined comparison algorithms
    # against the candidate pairs
    compare_cl = recordlinkage.Compare()

    compare_cl.string(
        "family_name", "family_name", method="jarowinkler", label="family_name"
    )
    compare_cl.string(
        "phone_number", "phone_number", method="jarowinkler", label="phone_number"
    )
    compare_cl.add(
        AddressComparison(
            "exploded_address",
            "exploded_address",
            label="household_street_address",
        )
    )
    compare_cl.string(
        "household_zip", "household_zip", method="levenshtein", label="household_zip"
    )
    # note: hamming distance is not implemented in this library,
    # but levenshtein is. the two metrics are likely similar enough
    # that it's not worth implementing hamming again

    if debug:
        print(f"[{datetime.now()}] Starting detailed comparison of indexed pairs")

    matching_pairs = []
    # we know that we could support len(subset_A) in memory above,
    # so use the same amount here
    len_subset_A = int(len(pii_lines) / split_factor)

    # note: np.array_split had unexpectedly poor performance here for very large indices
    for i in range(0, len(candidate_links), len_subset_A):
        subset_links = candidate_links[i : i + len_subset_A]

        # filtering the relevant pii lines before passing into compute() below
        #  seems to have a small positive impact on performance.
        # subset_links is a MultiIndex so get the unique values from each level
        #  to get the overall relevant pii lines for this iteration
        keys = set(subset_links.get_level_values(0)) | set(
            subset_links.get_level_values(1)
        )
        relevant_pii_lines = pii_lines[pii_lines.index.isin(keys)]
        if debug:
            print(
                f"[{datetime.now()}]  Detailed comparing rows "
                f"[{i}..{i + len_subset_A}]"
            )

        features = compare_cl.compute(subset_links, relevant_pii_lines)

        features["family_name"] *= FN_WEIGHT
        features["phone_number"] *= PHONE_WEIGHT
        features["household_street_address"] *= ADDR_WEIGHT
        features["household_zip"] *= ZIP_WEIGHT

        # filter the matches down based on the cumulative score
        matches = features[features.sum(axis=1) > MATCH_THRESHOLD]

        matching_pairs.extend(list(matches.index))
        # matching pairs are bi-directional and not duplicated,
        # ex if (1,9) is in the list then (9,1) won't be

    if debug:
        print(f"[{datetime.now()}] Found {len(matching_pairs)} pairs")

    pos_to_pairs = {}
    for pair in matching_pairs:
        if pair[0] in pos_to_pairs:
            pos_to_pairs[pair[0]].append(pair)
        else:
            pos_to_pairs[pair[0]] = [pair]

        if pair[1] in pos_to_pairs:
            pos_to_pairs[pair[1]].append(pair)
        else:
            pos_to_pairs[pair[1]] = [pair]

    return pos_to_pairs
