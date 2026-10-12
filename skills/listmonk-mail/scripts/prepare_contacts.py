"""Normalize a contacts CSV without uploading or printing recipient addresses."""
import argparse
import csv
import json
import re
from pathlib import Path

ALIASES = {"email": "email", "邮箱": "email", "邮件地址": "email",
           "name": "name", "姓名": "name", "名字": "name",
           "attributes": "attributes", "属性": "attributes"}
EMAIL = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")


def prepare(source, destination, encoding="utf-8-sig"):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output must be different files.")
    rows, seen, duplicate_count = [], set(), 0
    with source.open(encoding=encoding, newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        mapped = [ALIASES.get(h.strip().lower()) for h in headers]
        if not headers or None in mapped or len(set(mapped)) != len(mapped):
            raise ValueError("Unknown or duplicate columns; explicitly map additional fields first.")
        if "email" not in mapped:
            raise ValueError("A named email column is required.")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"Line {line}: inconsistent column count.")
            record = {mapped[index]: raw[header].strip() for index, header in enumerate(headers)}
            email = record["email"]
            if not EMAIL.fullmatch(email):
                raise ValueError(f"Line {line}: invalid email format.")
            try:
                attributes = json.loads(record.get("attributes") or "{}")
            except json.JSONDecodeError:
                raise ValueError(f"Line {line}: attributes must be valid JSON.") from None
            if not isinstance(attributes, dict):
                raise ValueError(f"Line {line}: attributes must be a JSON object.")
            if email.casefold() in seen:
                duplicate_count += 1
                continue
            seen.add(email.casefold())
            rows.append({"email": email, "name": record.get("name", ""),
                         "attributes": json.dumps(attributes, ensure_ascii=False)})
    if not rows:
        raise ValueError("The input contains no contacts.")
    # Exclusive create preserves existing output files, including on validation failures.
    with destination.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["email", "name", "attributes"])
        writer.writeheader()
        writer.writerows(rows)
    return {"contacts": len(rows), "duplicates_removed": duplicate_count,
            "output": str(destination.resolve())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--encoding", default="utf-8-sig")
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.input, args.output, args.encoding), ensure_ascii=False))
    except (ValueError, OSError, UnicodeError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
