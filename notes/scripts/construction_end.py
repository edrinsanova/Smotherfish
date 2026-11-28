"""What ends construction in our won games? For each won game of ours
(match.py records) that reached +8 material: plies from first +8 to the end,
the 50-move counter (half-moves) at the end and its maximum in that phase,
and how the game ended (knight smother or other mate). Construction stops
when the counter reaches SmotherSeekRule50 (60) or after SmotherBuildMoves
(160) moves; the engine then mates normally.
Usage: python construction_end.py FILE.jsonl...
"""
import collections
import json
import sys
from multiprocessing import Pool

import chess

VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def mat(b, c):
    return sum(VAL[p.piece_type] for p in b.piece_map().values() if p.color == c)


def analyse(line):
    g = json.loads(line)
    if g.get("ours") != 1:
        return None
    us = chess.WHITE if g["ours_white"] else chess.BLACK
    b = chess.Board(g["fen"])
    start = None
    hm_max = 0
    cross60 = None
    for i, u in enumerate(g["moves"].split()):
        if start is None and mat(b, us) - mat(b, not us) >= 8:
            start = i
        if start is not None:
            hm_max = max(hm_max, b.halfmove_clock)
            if cross60 is None and b.halfmove_clock >= 60:
                cross60 = i
        b.push_uci(u)
    if start is None:
        return None
    n = len(g["moves"].split())
    kind = "knight smother" if g.get("smother") == "classic" else "other mate"
    return kind, n - start, b.halfmove_clock, hm_max, (n - cross60) if cross60 is not None else None


def main():
    lines = [l for f in sys.argv[1:] for l in open(f)]
    with Pool(4) as p:
        R = [r for r in p.map(analyse, lines, chunksize=50) if r]
    for k in ("knight smother", "other mate"):
        L = [r for r in R if r[0] == k]
        n = len(L)
        med = lambda i: sorted(r[i] for r in L)[n // 2]
        hit = [r for r in L if r[4] is not None]
        print(f"{k}: {n} games; median plies from +8 to the end {med(1)}; 50-move counter reached 60 in {len(hit)} ({100*len(hit)/n:.0f}%)")
        if hit:
            after = sorted(r[4] for r in hit)
            print(f"   of those, the game ended within 20 plies of reaching 60: {sum(a <= 20 for a in after)} ({100*sum(a <= 20 for a in after)/len(hit):.0f}%); median plies after: {after[len(after)//2]}")
        print("   plies from +8 to the end:", sorted(collections.Counter(min(r[1] // 40 * 40, 320) for r in L).items()))


if __name__ == "__main__":
    main()
