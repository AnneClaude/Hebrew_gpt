# Experiment log

## Data
- Hebrew Wikipedia (20231101.he): 333,874 articles, fields: id, url, title, text
- Observation: some articles have niqqud on the first word (e.g. מָתֵמָטִיקָה); we will strip it in the  normalizer 

## Phase 0: Cleaned dataset

| | Articles | Characters |
|---|---|---|
| Train | 304,478 | 945,199,196 |
| Val | 15,850 | 48,946,432 |

- Read 333,874 articles, dropped 13,546 (4.1%) as shorter than 200 chars after cleaning, 0 exact duplicates
- Cleaning removed about 9% of the raw characters (trailing sections, categories, niqqud, foreign scripts)
- First version of prepare.py ran at ~128 articles/sec; replacing per-character Python loops with regexes made cleaning ~3x faster
- Known limitation: accented Latin letters (é, ü) are removed by the allowed-character filter