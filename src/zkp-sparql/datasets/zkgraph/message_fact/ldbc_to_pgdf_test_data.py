import random
#!/usr/bin/env python3
"""
Convert LDBC SNB CSV files (pipe-separated) into PathDB's nodes.pgdf / edges.pgdf.

All text values are Unicode-standardized (NFKC, curly quotes/dashes -> ASCII,
invisible characters removed, whitespace collapsed). Use --ascii to also
transliterate everything to plain ASCII.

Usage:
    python ldbc_to_pgdf.py --in ./ldbc --out ./pgdf
    python ldbc_to_pgdf.py --in ./ldbc --out ./pgdf --ascii
    java -jar PathDB.jar -n pgdf/nodes.pgdf -e pgdf/edges.pgdf
"""
import argparse
import csv
import os
import re
import sys
import unicodedata

csv.field_size_limit(sys.maxsize)

try:  # optional, only used with --ascii
    from unidecode import unidecode
except ImportError:
    unidecode = None

# ---------------------------------------------------------------- files
PERSON_FILE = "person_0_0.csv"
POST_FILE = "post.csv"
COMMENT_FILE = "comment.csv"
KNOWS_FILE = "person_knows_person_0_0.csv"
POST_CREATOR_FILE = "post_hasCreator_person.csv"
COMMENT_CREATOR_FILE = "comment_hasCreator_person.csv"
# Not in your list, but needed to know WHICH comments are on posts:
COMMENT_REPLY_POST_FILE = "comment_replyOf_post_0_0.csv"       # optional
COMMENT_REPLY_COMMENT_FILE = "comment_replyOf_comment_0_0.csv"  # optional

# ------------------------------------------------------- PGDF columns
# One nodes file => one header => union of all properties.
# A node leaves the columns it does not have empty.
NODE_PROPS = [
    "firstName", "lastName", "gender", "birthYear",      # Person
    "imageFile", "language",                             # Post
    "txt", "length",                                     # Post / Comment
    "creationDate", "locationIP", "browserUsed",         # all
]
EDGE_PROPS = ["creationDate", "atContext"]               # knows only

# Node id prefixes: LDBC ids are only unique per entity type.
PERSON, POST, COMMENT = "p", "po", "c"


# ----------------------------------------------------- unicode cleaning
ASCII_ONLY = False   # set from --ascii
CHANGED = 0          # how many values were modified (for the report)

# Characters NFKC leaves alone but that break/confuse queries
PUNCT_MAP = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201A": "'", "\u201B": "'",
    "\u2032": "'", "\u00B4": "'", "\u0060": "'",
    "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"',
    "\u2033": '"', "\u00AB": '"', "\u00BB": '"',
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
    "\u2014": "-", "\u2015": "-", "\u2212": "-",
    "\u2022": "*", "\u00B7": ".",
})

# Zero-width, BOM, soft hyphen, bidi marks/isolates, replacement char
INVISIBLE_RE = re.compile(
    "[\u00AD\u200B-\u200F\u202A-\u202E\u2060-\u2064\u2066-\u2069\uFEFF\uFFFD]"
)
WHITESPACE_RE = re.compile(r"\s+")


def to_ascii(text: str) -> str:
    if unidecode is not None:  # best: handles ss, o-slash, Cyrillic, CJK...
        return unidecode(text)
    # Fallback: strip accents only; non-Latin letters are dropped
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.encode("ascii", "ignore").decode("ascii")


def clean(value: str) -> str:
    """Standardize a value so it is safe in a PGDF file and in queries."""
    global CHANGED
    original = value

    value = unicodedata.normalize("NFKC", value)
    value = value.translate(PUNCT_MAP)
    value = INVISIBLE_RE.sub("", value)
    # Drop remaining control / surrogate / private-use / unassigned characters;
    # tabs, CR, LF and other separators become spaces.
    value = "".join(
        " " if (c.isspace() or unicodedata.category(c) in ("Zs", "Zl", "Zp"))
        else c
        for c in value
        if unicodedata.category(c) not in ("Cc", "Cs", "Co", "Cn") or c.isspace()
    )
    if ASCII_ONLY:
        value = to_ascii(value)

    value = value.replace("|", " ")  # the PGDF separator
    value = WHITESPACE_RE.sub(" ", value).strip()

    if value != original:
        CHANGED += 1
    return value


# ------------------------------------------------------------ helpers
def get_knows_context(edge_number: int) -> str:
    """Same logic as the Java getKnowsContext (edge_number starts at 1)."""
    contexts = ["work", "school", "family", "neighborhood", "conference"]
    return contexts[(edge_number - 1) % len(contexts)]


def birth_year(birthday: str) -> str:
    """'1989-12-03' -> '1989'"""
    return birthday[:4] if len(birthday) >= 4 else ""


def read_rows(folder, name, optional=False):
    """Yield data rows (list of str) of a '|' separated file, skipping the header."""
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        if optional:
            print(f"WARNING: optional file not found, skipping: {path}", file=sys.stderr)
            return
        sys.exit(f"ERROR: missing required file: {path}")
    # utf-8-sig removes a BOM; errors="replace" avoids crashes on invalid bytes
    # (the resulting U+FFFD is removed later by clean()).
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter="|", quoting=csv.QUOTE_NONE)
        next(reader, None)  # header
        for row in reader:
            if row:
                yield row


def col(row, i):
    return row[i] if i < len(row) else ""


def write_line(out, values):
    out.write("|".join(clean(v) for v in values) + "\n")

# -------------------------------------------------------------- sampling
def sample_rows(rows, limit):
    """Deterministically sample up to limit rows, preserving no particular order."""
    if limit is None or len(rows) <= limit:
        return rows
    return random.sample(rows, limit)


def read_all_rows(folder, name, optional=False):
    return list(read_rows(folder, name, optional))


# -------------------------------------------------------------- nodes
def write_nodes(folder, out_path, target_nodes):
    ids = {"person": set(), "post": set(), "comment": set()}

    def node_line(out, node_id, label, props):
        write_line(out, [node_id, label] + [props.get(k, "") for k in NODE_PROPS])

    persons = read_all_rows(folder, PERSON_FILE)
    posts = read_all_rows(folder, POST_FILE)
    comments = read_all_rows(folder, COMMENT_FILE)

    # Fixed mixture: 40% Person, 30% Post, 30% Comment.
    n_person = min(len(persons), int(target_nodes * 0.40))
    n_post = min(len(posts), int(target_nodes * 0.30))
    n_comment = min(len(comments), max(0, target_nodes - n_person - n_post))

    persons = sample_rows(persons, n_person)
    posts = sample_rows(posts, n_post)
    comments = sample_rows(comments, n_comment)

    with open(out_path, "w", encoding="utf-8", newline="") as out:
        write_line(out, ["@id", "@label"] + NODE_PROPS)

        for r in persons:
            ids["person"].add(r[0])
            node_line(out, PERSON + r[0], "Person", {
                "firstName": col(r, 1), "lastName": col(r, 2), "gender": col(r, 3),
                "birthYear": birth_year(col(r, 4)),
                "creationDate": col(r, 5), "locationIP": col(r, 6),
                "browserUsed": col(r, 7),
            })

        for r in posts:
            ids["post"].add(r[0])
            node_line(out, POST + r[0], "Post", {
                "imageFile": col(r, 1), "creationDate": col(r, 2),
                "locationIP": col(r, 3), "browserUsed": col(r, 4),
                "language": col(r, 5), "txt": col(r, 6), "length": col(r, 7),
            })

        for r in comments:
            ids["comment"].add(r[0])
            node_line(out, COMMENT + r[0], "Comment", {
                "creationDate": col(r, 1), "locationIP": col(r, 2),
                "browserUsed": col(r, 3), "txt": col(r, 4), "length": col(r, 5),
            })

    return ids


# -------------------------------------------------------------- edges
def write_edges(folder, out_path, ids, target_edges, add_created=True):
    # Each item is one output edge line.
    candidates = []

    def add_candidate(label, src, dst, props=None):
        candidates.append((label, src, dst, props or {}))

    def collect_simple_edges(file, label, src_prefix, src_set, dst_prefix, dst_set,
                             optional=False, also_created=False):
        for r in read_all_rows(folder, file, optional):
            if r[0] not in src_set or col(r, 1) not in dst_set:
                continue
            src = src_prefix + r[0]
            dst = dst_prefix + r[1]
            add_candidate(label, src, dst)
            if also_created:
                add_candidate("created", dst, src)

    # knows first so that its relative order is stable.
    for r in read_all_rows(folder, KNOWS_FILE):
        if r[0] in ids["person"] and col(r, 1) in ids["person"]:
            add_candidate(
                "knows", PERSON + r[0], PERSON + r[1],
                {"creationDate": col(r, 2)},
            )

    collect_simple_edges(
        POST_CREATOR_FILE, "hasCreator",
        POST, ids["post"], PERSON, ids["person"],
    )

    collect_simple_edges(
        COMMENT_CREATOR_FILE, "hasCreator",
        COMMENT, ids["comment"], PERSON, ids["person"],
        also_created=add_created,
    )

    collect_simple_edges(
        COMMENT_REPLY_POST_FILE, "replyOf",
        COMMENT, ids["comment"], POST, ids["post"], optional=True,
    )

    collect_simple_edges(
        COMMENT_REPLY_COMMENT_FILE, "replyOf",
        COMMENT, ids["comment"], COMMENT, ids["comment"], optional=True,
    )

    selected = sample_rows(candidates, target_edges)

    knows_seen = 0
    counter = 0
    with open(out_path, "w", encoding="utf-8", newline="") as out:
        write_line(out, ["@id", "@label", "@dir", "@out", "@in"] + EDGE_PROPS)

        for label, src, dst, props in selected:
            counter += 1
            if label == "knows":
                knows_seen += 1
                props = dict(props)
                props["atContext"] = get_knows_context(knows_seen)

            write_line(
                out,
                [f"E{counter}", label, "T", src, dst]
                + [props.get(k, "") for k in EDGE_PROPS],
            )

    return counter, len(candidates) - len(selected)


# --------------------------------------------------------------- main
def main():
    global ASCII_ONLY

    ap = argparse.ArgumentParser(description="LDBC CSV -> PathDB nodes.pgdf / edges.pgdf")
    ap.add_argument("--in", dest="in_dir", required=True,
                    help="folder with the LDBC CSV files")
    ap.add_argument("--out", dest="out_dir", default="pgdf", help="output folder")
    ap.add_argument("--target-nodes", type=int, default=5000,
                    help="approximate number of node data rows (default: 5000)")
    ap.add_argument("--target-edges", type=int, default=5000,
                    help="approximate number of edge data rows (default: 5000)")
    ap.add_argument("--seed", type=int, default=42,
                    help="random seed for reproducible sampling")
    ap.add_argument("--no-created", action="store_true",
                    help="do not add the extra Person -created-> Comment edges")
    ap.add_argument("--ascii", action="store_true",
                    help="also transliterate everything to plain ASCII")
    args = ap.parse_args()

    ASCII_ONLY = args.ascii
    random.seed(args.seed)

    if ASCII_ONLY and unidecode is None:
        print("WARNING: 'unidecode' not installed; accents are stripped but "
              "non-Latin letters will be dropped.", file=sys.stderr)

    os.makedirs(args.out_dir, exist_ok=True)
    nodes_path = os.path.join(args.out_dir, "nodes.pgdf")
    edges_path = os.path.join(args.out_dir, "edges.pgdf")

    ids = write_nodes(args.in_dir, nodes_path, args.target_nodes)
    n_edges, skipped = write_edges(
        args.in_dir, edges_path, ids, args.target_edges, not args.no_created,
    )

    print(f"Target node rows: {args.target_nodes}; "
          f"actual: {sum(len(s) for s in ids.values())} "
          f"(Person={len(ids['person'])}, Post={len(ids['post'])}, "
          f"Comment={len(ids['comment'])})")
    print(f"Target edge rows: {args.target_edges}; actual: {n_edges} "
          f"(unsampled eligible edges: {skipped})")
    print(f"Values changed by Unicode cleaning: {CHANGED}")
    print(f"\nRun:\n  java -jar PathDB.jar -n {nodes_path} -e {edges_path}")

if __name__ == "__main__":
    main()