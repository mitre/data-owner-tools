import textdistance
import usaddress
import pandas as pd
import numpy as np
from recordlinkage.base import BaseCompareFeature


MATCH_THRESHOLD = 0.7
FN_WEIGHT = 0.2
PHONE_WEIGHT = 0.2
ADDR_WEIGHT = 0.3
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
    except:
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
def address_distance(a1, a2):
    score = 0
    secondary_score = 0
    # Need to parse because usaddress returns list of tuples without set indices
    addr1 = addr_parse(a1)
    addr2 = addr_parse(a2)
    # Alternative way to parse usaddress.parse(a1) return (less efficient I think)
    # addr_number_1 = next((v[0] for v in addr1 if v[1] == 'AddressNumber'), None)

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

    # See if simple string compare of all things combined with a 0.6 adjustment is better
    score = (
        max(
            score,
            textdistance.jaro_winkler(a1, a2)
            * (weight_number + weight_street_name)
            * 0.6,
        )
        + (secondary_score * weight_secondary)
    )
    return score


# see https://github.com/J535D165/recordlinkage/blob/master/recordlinkage/compare.py
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

    def __init__(self,
                 left_on,
                 right_on,
                 label=None):
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

def match_households(already_added, pat_clks, pat_ids, line, pii_lines):
    for position, line_compare in enumerate(pii_lines):
        if position in already_added:
            continue
        weighted_fn = textdistance.jaro_winkler(line[2], line_compare[2]) * FN_WEIGHT
        weighted_phone = textdistance.jaro_winkler(line[5], line_compare[5]) * PHONE_WEIGHT
        weighted_addr = address_distance(line[6], line_compare[6]) * ADDR_WEIGHT
        weighted_zip = (
            textdistance.hamming.normalized_similarity(line[7], line_compare[7]) * ZIP_WEIGHT
        )
        total_distance = weighted_fn + weighted_zip + weighted_addr + weighted_phone
        if total_distance > MATCH_THRESHOLD:
            pat_clks.append(position)
            pat_ids.append(line_compare[0])
            already_added.append(position)
