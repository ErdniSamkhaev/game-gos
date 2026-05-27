# Parsers

`parse_docx.py` is the main (and only) parser. It reads the original Synergy
DOCX (`fos_gia_vo_bak_09_03_02_rsob (2).docx`) and writes
`data/questions.json` consumed by the Vue app. DOCX is far cleaner than PDF
because every table cell arrives as a single piece of text (no PDF-layout
fragmentation), so all 450 questions land cleanly.

`validate.py` audits the resulting `questions.json` and writes
`report.html` with stats, per-discipline breakdown and a list of every
question that has a likely parsing issue or is a duplicate of another one.

## Usage

```bash
pip install -r requirements.txt

python parse_docx.py        # rebuilds data/questions.json
python validate.py          # writes parser/report.html
python validate.py --open   # also opens it in the default browser
```

The DOCX path is hard-coded at the top of `parse_docx.py`.

## Output schema

Each question is one of five types:

- `single` — single-answer multiple choice (one of А/Б/В/Г/Д)
- `multi` — multiple-answer multiple choice
- `matching` — pair items 1..N with letters А..Е
- `sequence` — order shuffled items in the right sequence
- `open` — free-form question with reference answer

Common fields: `id`, `discipline_num`, `discipline_name`, `type`, `statement`.
Type-specific fields are documented inline in `parse_docx.py`.
