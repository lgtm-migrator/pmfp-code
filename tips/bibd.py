"""A balanced incomplete block design with parameters (15, 3, 1)."""

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Collection
from typing import DefaultDict
from typing import Tuple

BIBD = Collection[Collection[str]]

# A compact representation as a string, where each
# block is a column.
bibd_15_3_1_str = """
00000001111112222223333444455556666
13579bd3478bc3478bc789a789a789a789a
2468ace569ade65a9edbcdecbeddebcedcb
"""

bibd_19_9_4_str = """
0000000001111122223
1111233562334433444
2225544777556666555
3346678888787878786
499acab99a9b9aa9b99
5aebdcdabddcbcbccaa
6bfegefcdefecdfedbd
7cgfhghfehgghfgfege
8dhiiiihgiihighifih
"""

bibd_9_4_3_str = """
000000001111122223
111233562334433444
225544777556666555
346678888787878786
"""

bibd_8_4_3_str = """
00000001111223
11122342235344
23436553446556
57647676757767
"""


def str_to_blocks(bibd_str) -> BIBD:
    """Convert from compact string format to a list of blocks."""
    return tuple(zip(*bibd_str.strip().split()))


bibd_8_4_3 = str_to_blocks(bibd_8_4_3_str)
bibd_9_4_3 = str_to_blocks(bibd_9_4_3_str)
bibd_15_3_1 = str_to_blocks(bibd_15_3_1_str)
bibd_19_9_4 = str_to_blocks(bibd_19_9_4_str)

ALL_BIBDS = [
    bibd_8_4_3,
    bibd_9_4_3,
    bibd_15_3_1,
    bibd_19_9_4,
]


@dataclass(frozen=True)
class BIBDParams:
    """A parameter set describing a Balanced Incomplete Block Design (BIBD).

    The members of this class will be described in both clinical trials
    language (subjects & treatments) and in the notation of Dinitz-Colbourn's
    Handbook of Combinatorial Designs (2nd edition), section II.1 (abbreviated HCD),
    which are the parameters (v, b, r, k, lambda).
    """

    """
    The number of treatments to be tested. In HCD, the size v of the ground set
    V.
    """
    treatments: int

    @property
    def v(self):
        return self.treatments

    """
    The number of test subjects. In HCD, the number of blocks b.
    """
    subjects: int

    @property
    def b(self):
        return self.subjects

    """
    The number of replications of each treatment. In HCD, r.
    """
    subjects_per_treatment: int

    @property
    def r(self):
        return self.subjects_per_treatment

    """
    The number of treatments to apply to each test subject. In HCD, the size k
    of a block.
    """
    treatments_per_subject: int

    @property
    def k(self):
        return self.treatments_per_subject

    """
    The number of times each pair of treatments occurs in a block. In HCD,
    the parameter lambda.
    """
    subjects_per_treatment_pair: int

    @property
    def lambda_(self):
        return self.subjects_per_treatment_pair

    def satisfies_necessary_conditions(self) -> bool:
        """Determine if the parameters satisfy the necessary conditions for
        the existence of a BIBD.

        Note that even if this function returns true, a BIBD may not exist
        for these parameters. One can relax the balancedness condition and
        still achieve a useful design for an experiment, but the statistical
        analysis is more complicated.
        """
        v, r, b, k, lambda_ = self.v, self.r, self.b, self.k, self.lambda_

        satisfies_divisibility = v * r == b * k and v % k == 0
        is_balanceable = r * (k - 1) == lambda_ * (v - 1)

        satisfies_fishers_inequality = b >= v if (v > k >= 2) else True

        return (
            satisfies_divisibility and is_balanceable and satisfies_fishers_inequality
        )

    def efficiency_factor(self) -> float:
        """Return the efficiency factor of the design.

        The efficiency factor E measures the relative precision of a
        statistical experiment using a BIBD when compared to a complete block
        design, i.e., a block design in which every treatment is applied to
        every subject (RCBD, see
        https://en.wikipedia.org/wiki/Generalized_randomized_block_design).

        The quantity 100 * (1-E) is a bound on the percent reduction in
        precision. This can also be interpreted as the amount of variance that
        must be reduced to allow a BIBD study to maintain the same precision as
        an equivalent complete block design.
        """
        return self.lambda_ * self.v / (self.r * self.k)

    @staticmethod
    def from_bibd(bibd: BIBD) -> "BIBDParams":
        """Return the parameters for a BIBD.

        Assumes the input is a valid BIBD."""
        elements = set(x for block in bibd for x in block)
        k = len(next(iter(bibd)))
        b = len(bibd)
        v = len(elements)

        any_element = next(iter(elements))
        r = len([block for block in bibd if any_element in block])

        elt_iter = iter(elements)
        e1, e2 = next(elt_iter), next(elt_iter)
        lambda_ = len([block for block in bibd if e1 in block and e2 in block])

        return BIBDParams(
            subjects=b,
            treatments=v,
            treatments_per_subject=k,
            subjects_per_treatment=r,
            subjects_per_treatment_pair=lambda_,
        )


def is_bibd(bibd: BIBD) -> bool:
    """Determine if a given list of blocks is a BIBD."""
    block_sizes = set(len(block) for block in bibd)
    if len(block_sizes) != 1:
        print(f"Block sizes = {block_sizes}")
        return False

    element_memberships: DefaultDict[str, int] = defaultdict(int)
    pairwise_memberships: DefaultDict[Tuple[str, str], int] = defaultdict(int)

    for block in bibd:
        for element in block:
            element_memberships[element] += 1
        for elt1, elt2 in combinations(block, 2):
            sorted_members = (elt1, elt2) if elt1 < elt2 else (elt2, elt1)
            pairwise_memberships[sorted_members] += 1

    if len(set(element_memberships.values())) != 1:
        print(f"Element memberships = {element_memberships}")
        return False

    if len(set(pairwise_memberships.values())) != 1:
        min_entry = min(pairwise_memberships.items(), key=lambda x: x[1])
        max_entry = max(pairwise_memberships.items(), key=lambda x: x[1])
        print(f"Pairwise memberships not all equal = {min_entry, max_entry}")
        return False

    n = len(element_memberships.keys())
    if len(pairwise_memberships.keys()) != n * (n - 1) / 2:
        print(
            "Not all pairs represented. Only found "
            f"{len(pairwise_memberships.keys())} when expecting {n * (n-1) / 2}"
        )
        return False

    return True


if __name__ == "__main__":
    for bibd in ALL_BIBDS:
        print(f"Params = {BIBDParams.from_bibd(bibd)}")
        print(f"Blocks = {bibd}")
