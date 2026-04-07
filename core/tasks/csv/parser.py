import csv
from typing import Generator, Dict, Any
from ..utils import str_to_float, clamp_decimal


def parse_questions_from_csv(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Parse questions from a CSV file.
    
    :param file_path: Path to the CSV file.
    :yield: Dictionary containing parsed question data.
    """
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            try:
                question_data = parse_csv_row(row)
                if question_data:
                    yield question_data
            except Exception as e:
                # Log error and continue with next row
                print(f"Error parsing row {row.get('id', 'unknown')}: {e}")
                continue


def parse_csv_row(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse a single CSV row into question data format.
    
    :param row: Dictionary representing a CSV row.
    :return: Dictionary with parsed question data, or None if row is invalid.
    """
    # Extract basic question info
    fast_id = row.get('fastID', '').strip()
    if not fast_id:
        # Use id if fastID is not available
        fast_id = f"CSV_{row.get('id', '').strip()}"
    
    # Validate that we have a question ID
    if not fast_id or fast_id == "CSV_":
        print(f"Skipping row with missing ID")
        return None
    
    question_content = row.get('question', '').strip()
    if not question_content:
        print(f"Skipping row {fast_id} with missing question content")
        return None
    
    solution = row.get('solution', '').strip()
    
    # Extract IRT parameters and clamp to database constraints
    discrimination = float(clamp_decimal(str_to_float(row.get('p1', ''), default=1.0)))
    difficulty = float(clamp_decimal(str_to_float(row.get('p2', ''), default=0.0)))
    guessing = float(clamp_decimal(str_to_float(row.get('p3', ''), default=0.0)))
    
    # Parse accuracy (percentage) to selection frequency (0-1) and clamp
    accuracy = str_to_float(row.get('accuracy', ''), default=0.0)
    selection_frequency = float(clamp_decimal(accuracy / 100.0 if accuracy > 0 else 0.0))
    
    # Parse correct answer option
    correct_q = row.get('correctQ', '').strip()
    
    # Parse response options
    options, option_frequencies, correct_option_index = parse_options(row, correct_q)
    
    # Validate we have options
    if not options:
        print(f"Skipping row {fast_id} with no valid options")
        return None
    
    # Clamp option frequencies
    clamped_frequencies = [str(float(clamp_decimal(str_to_float(freq)))) for freq in option_frequencies]
    
    return {
        'serial_number': fast_id,
        'content': question_content,
        'explanation': solution,
        'discrimination': discrimination,
        'difficulty': difficulty,
        'guessing': guessing,
        'selection_frequency': selection_frequency,
        'options': options,
        'option_selection_frequencies': clamped_frequencies,
        'answer': correct_option_index,
        'comments': '',  # CSV doesn't have comments
        'images': [],  # CSV doesn't have embedded images
        'unit': 'Chemical Kinetics',  # Default from mock data for CHEM 1AA3
        'subtopic': 'Rate laws',      # Default from mock data for CHEM 1AA3 / Chemical Kinetics
        'unit_number': 2,             # Default number from mock data for CHEM 1AA3 / Chemical Kinetics
    }


def parse_options(row: Dict[str, str], correct_q: str) -> tuple:
    """
    Parse response options from CSV row.
    
    :param row: Dictionary representing a CSV row.
    :param correct_q: Indicator of which option is correct (e.g., "2" for option 2).
    :return: Tuple of (options_list, frequencies_list, correct_index).
    """
    options = []
    frequencies = []
    correct_option_index = 0
    
    # Try to parse correct_q as an integer
    try:
        correct_option_num = int(correct_q) if correct_q else 1
    except ValueError:
        correct_option_num = 1
    
    # Parse up to 5 possible response options (can extend if needed)
    for i in range(1, 6):
        label_key = f'responseLabel{i}'
        score_key = f'responseScore{i}'
        n_key = f'responseN{i}'
        
        label = row.get(label_key, '').strip()
        
        if not label:
            # No more options
            break
        
        options.append(label)
        
        # Get selection frequency for this option
        n_value = str_to_float(row.get(n_key, ''), default=0.0)
        frequencies.append(str(n_value))
        
        # Determine if this is the correct answer
        # Check both responseScore (1 = correct) and correctQ indicator
        score = str_to_float(row.get(score_key, ''), default=0.0)
        if score == 1.0 or i == correct_option_num:
            correct_option_index = len(options) - 1
    
    # Convert correct_option_index to letter (A, B, C, etc.)
    correct_answer_letter = chr(ord('A') + correct_option_index) if options else 'A'
    
    return options, frequencies, correct_answer_letter
