# CSV Question Import Format

This module handles parsing CSV files containing question bank data.

## Required Columns

The following columns are **required** and map to the database schema:

- `fastID` - Unique identifier for the question (maps to `serial_number`)
- `question` - The question content (maps to `content`)
- `responseLabel1`, `responseLabel2`, etc. - Option text (up to 10 options)
- `responseScore1`, `responseScore2`, etc. - Score for each option (1 = correct, 0 = incorrect)

## Optional Columns (Mapped to Schema)

These columns are optional but will be used if present:

- `solution` - Answer explanation (maps to `explanation`)
- `p1` - Discrimination parameter (IRT) (maps to `discrimination`)
- `p2` - Difficulty parameter (IRT) (maps to `difficulty`)
- `p3` - Guessing parameter (IRT) (maps to `guessing`)
- `accuracy` - Percentage of correct responses (used to calculate `selection_frequency`)
- `correctQ` - Index of correct option (1-based, e.g., "2" for option 2)
- `responseN1`, `responseN2`, etc. - Number of times each option was selected

## Columns Not Currently Mapped

The following columns are in the CSV format but not currently mapped to the database:

- `id` - Row ID (not used, `fastID` is preferred)
- `fixedIndex` - Fixed ordering index
- `origin` - Question source (ai generated, a2l, exams, etc.)
- `trait` - Trait association
- `totalScore`, `totalN` - Aggregate statistics
- `type` - Item format type
- `skippable` - Whether item can be skipped
- `instructions` - Page-level instructions
- `zScore` - Z-score in topic
- `p4` - Inattention parameter
- `responseValue1`, `responseValue2`, etc. - Response values
- `responseTrait1`, `responseTrait2`, etc. - Trait per response option

## Important Notes

1. **Unit and Subtopic**: These are NOT included in the CSV. Questions are created with `subtopic=None` and must be associated with a unit/subtopic through a separate process later.

2. **Images**: CSV files do not support embedded images like DOCX files do.

3. **Difficulty Calculation**: If `p2` (difficulty) is 0 or not provided, it will be calculated from the accuracy/selection frequency.

4. **Course**: The course is specified in the upload API request, not in the CSV file.

## Example CSV Row

```csv
id,fastID,question,solution,p1,p2,p3,accuracy,correctQ,responseLabel1,responseScore1,responseN1,responseLabel2,responseScore2,responseN2
1,Winter_2023_Test_6-q19,The liver,test,1,0,0,83.85,2,Option A,0,40,Option B,1,1169
```

This would create a question with:
- Serial number: `Winter_2023_Test_6-q19`
- Content: "The liver"
- Two options (Option A and Option B), with Option B being correct
- Discrimination: 1.0
- Guessing: 0.0
- Selection frequency: 0.8385 (83.85%)


---

# CSV Upload Implementation Summary

## Overview
Added CSV file upload support to the existing question bank upload endpoint. CSV files can now be uploaded alongside DOCX files.

## Changes Made

### 1. New CSV Parser Module
**Location:** `/core/tasks/csv/`

- **`parser.py`**: Main CSV parsing logic
  - `parse_questions_from_csv()`: Generator that reads CSV and yields question data
  - `parse_csv_row()`: Parses individual CSV rows with validation
  - `parse_options()`: Extracts response options and determines correct answer
  - `parse_decimal()`: Helper for safe decimal parsing

- **`README.md`**: Documentation explaining CSV format and column mappings

### 2. Updated Files

**`/core/tasks/parse_questions.py`**:
- Added CSV import: `from .csv.parser import parse_questions_from_csv`
- Updated `parse_file()` to handle `.csv` extension
- Added `insert_csv_data()` function for CSV-specific data insertion
- CSV questions created with `subtopic=None` (assigned separately later)

**`/core/serializers/upload_serializer.py`**:
- Added file format validation in `validate_file()`
- Updated docstring to document CSV support

**`/core/views/upload.py`**:
- Updated docstrings to mention CSV support

## CSV Column Mapping

### Mapped to Database
- `fastID` → `serial_number`
- `question` → `content`
- `solution` → `explanation`
- `p1` → `discrimination` (IRT parameter)
- `p2` → `difficulty` (IRT parameter)
- `p3` → `guessing` (IRT parameter)
- `accuracy` → `selection_frequency` (converted from percentage)
- `responseLabel1-N` → Question options
- `responseScore1-N` → Determines correct answer
- `responseN1-N` → Option selection frequencies
- `correctQ` → Indicates correct option index

### Not Currently Mapped
- `id`, `fixedIndex`, `origin`, `trait`, `totalScore`, `totalN`, `type`, `skippable`, `instructions`, `zScore`, `p4`, `responseValue*`, `responseTrait*`

## Key Differences: CSV vs DOCX

| Feature | DOCX | CSV |
|---------|------|-----|
| Unit/Subtopic | ✓ Included | ✗ Set to None (assigned later) |
| Embedded Images | ✓ Supported | ✗ Not supported |
| IRT Parameters | ✗ Calculated | ✓ Included in file |
| Answer Explanation | ✓ Supported | ✓ Supported |
| Selection Frequencies | ✓ Per option | ✓ Per option + overall accuracy |

## Usage

Upload CSV file via the existing upload endpoint:

```http
PUT /api/upload/
Content-Type: multipart/form-data

{
  "file": <csv_file>,
  "course": {
    "code": "KINES",
    "year": 2023,
    "semester": "Winter"
  },
  "create_required": false
}
```

## Notes

1. **Subtopic Assignment**: CSV questions are created without a subtopic. You'll need a separate process to assign unit/subtopic relationships after upload.

2. **Difficulty Calculation**: If `p2` (difficulty) is 0 or missing, it's calculated from the accuracy/selection frequency using the existing formula.

3. **Validation**: Parser validates:
   - Question ID exists (uses `fastID` or falls back to `id`)
   - Question content is present
   - At least one option exists

4. **Error Handling**: Invalid rows are logged and skipped, allowing the rest of the file to process successfully.

## Testing

To test the implementation:
1. Upload the sample CSV file: `/Users/laeek/Downloads/projects/Mac-FAST/kinesiology induvidual/LIVER.csv`
2. Verify questions are created without subtopic
3. Check that IRT parameters (p1, p2, p3) are correctly stored
4. Verify option parsing and correct answer detection
