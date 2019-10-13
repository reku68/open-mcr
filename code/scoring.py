import list_utils
import data_exporting
import grid_info
import math_utils
import typing


KEY_NOT_FOUND_MESSAGE = "NO KEY FOUND"


def establish_key_dict(answer_keys: data_exporting.OutputSheet
                       ) -> typing.Dict[str, typing.List[str]]:
    """Takes the matrix of answer keys and transforms it into a dictionary that
    maps the test form codes to the list of correct answers. 

    Treats the answer_keys data naively by assuming the following:
        * The column with the form codes comes before the answer columns.
        * The first answer column is named "1".
        * The answers are all in order.
    If these are wrong, the results will be incorrect.

    Also note: the returned list of answers matches the order of the questions,
    but the questions are named "1" through "75" and the answers are in indexes
    0 through 74.
    """
    keys = answer_keys.data
    form_code_column_name = data_exporting.COLUMN_NAMES[
        grid_info.Field.TEST_FORM_CODE]
    try:
        # Get the index of the column that had the test form codes
        form_code_index = list_utils.find_index(keys[0], form_code_column_name)
        # After the test form codes column, search for the 1st question column
        # index
        answers_start_index = list_utils.find_index(keys[0][form_code_index + 1:], "1") + form_code_index + 1
    except StopIteration:
        raise ValueError(
            "Invalid key matrix passed to scoring functions. Test form code column must be prior to answers columns, which must be named '1' through N."
        )

    return {
        key[form_code_index]: key[answers_start_index:]
        for key in keys[1:]
    }


def score_results(results: data_exporting.OutputSheet,
                  answer_keys: data_exporting.OutputSheet) -> data_exporting.OutputSheet:
    answers = results.data
    keys = establish_key_dict(answer_keys)
    form_code_column_name = data_exporting.COLUMN_NAMES[
        grid_info.Field.TEST_FORM_CODE]
    form_code_index = list_utils.find_index(answers[0], form_code_column_name)
    answers_start_index = list_utils.find_index(answers[0][form_code_index + 1:], "1") + form_code_index + 1
    columns = results.field_columns + [grid_info.VirtualField.SCORE]
    scored_results = data_exporting.OutputSheet(columns)

    for exam in answers[1:]:  # Skip header row
        fields = {k: v for k, v in zip(results.field_columns, exam[:answers_start_index])}
        form_code = exam[form_code_index]
        try:
            key = keys[form_code]
        except KeyError:
            fields[grid_info.VirtualField.SCORE] = KEY_NOT_FOUND_MESSAGE
            scored_answers = []
        else:
            scored_answers = [actual == correct for actual, correct in zip(exam[answers_start_index:], key)]
            fields[grid_info.VirtualField.SCORE] = str(round(math_utils.mean(scored_answers), 4))
        string_scored_answers = [str(s) for s in scored_answers]
        scored_results.add(fields, string_scored_answers)

    return scored_results