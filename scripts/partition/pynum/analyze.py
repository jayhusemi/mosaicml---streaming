# Copyright 2023 MosaicML Streaming authors
# SPDX-License-Identifier: Apache-2.0

"""Find the patterns in required dataset padding."""

from argparse import ArgumentParser, Namespace
from typing import Optional

import numpy as np
from numpy.typing import NDArray


def parse_args() -> Namespace:
    """Parse command-line arguments.

    Returns:
        Namespace: Command-line arguments.
    """
    args = ArgumentParser()
    args.add_argument('--in', type=str, required=True)
    return args.parse_args()


def is_pattern(text: str, pattern: str) -> bool:
    """Tell whether the given text can be explained by the pattern."""
    num_repeats = len(text) // len(pattern) + 1
    text2 = ''.join([pattern] * num_repeats)[:len(text)]
    return text == text2


def get_pattern(text: str) -> Optional[str]:
    """Find the shortest pattern in the given text.

    Args:
        text (str): Full text.

    Returns:
        Optional[str]: Pattern, if one is found.
    """
    for pattern_len in range(1, len(text) // 2):
        pattern = text[:pattern_len]
        if is_pattern(text, pattern):
            return pattern


def normalize_pattern(pattern: str) -> str:
    """Rotate the pattern to the canonical position.

    Args:
        pattern (str): Input pattern.

    Returns:
        str: Pattern in canonical form.
    """
    patterns = []
    for i in range(len(pattern)):
        pattern2 = pattern[i:] + pattern[:i]
        patterns.append(pattern2)
    patterns.sort()
    return patterns[-1]


def analyze(seq: NDArray[np.int64]) -> None:
    """Search for a pattern to explain the given sequence.

    Args:
        seq (NDArray[np.int64]): Sequence to analyze.
    """
    if not any(seq):
        return

    text = ''.join(map(chr, seq))
    pattern = get_pattern(text) or ''
    if pattern:
        pattern = normalize_pattern(pattern)
    human_pattern = ''.join(map(lambda c: chr(ord(c) + ord('a')), pattern))
    human_text = ''.join(map(lambda n: chr(n + ord('a')), seq))
    print(f'        {human_text[:40]} -> {human_pattern}')


def main(args: Namespace) -> None:
    """Find the patterns in required dataset padding.

    Args:
        args (Namespace): Command-line arguments.
    """
    x = np.load(getattr(args, 'in'), allow_pickle=True)
    num_c, num_p, num_r, num_w, num_b, _ = x.shape

    for ci in range(num_c):
        c = 1 + ci
        print(f'c {c}')
        for pi in range(num_p):
            p = 1 + pi
            if c < p:
                if p % c:
                    continue
            elif p < c:
                if c % p:
                    continue
            print(f'    c {c}, p {p}')
            for ri in range(num_r):
                for wi in range(num_w):
                    for bi in range(num_b):
                        analyze(x[ci, pi, ri, wi, bi])
            print()

    xc = x.reshape(num_c, -1).max(1)
    print('Max over canonical nodes:', xc)

    xp = x.transpose(1, 0, 2, 3, 4, 5).reshape(num_p, -1).max(1)
    print('Max over physical nodes:', xp)

    xr = x.transpose(2, 0, 1, 3, 4, 5).reshape(num_r, -1).max(1)
    print('Max over ranks per node:', xr)

    xw = x.transpose(3, 0, 1, 2, 4, 5).reshape(num_w, -1).max(1)
    print('Max over workers per node:', xw)

    xb = x.transpose(4, 0, 1, 2, 3, 5).reshape(num_b, -1).max(1)
    print('Max over batch size per rank:', xb)


if __name__ == '__main__':
    main(parse_args())