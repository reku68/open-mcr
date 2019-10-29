""""""
import csv
import pathlib
import typing

from grid_info import NUM_QUESTIONS, Field, RealOrVirtualField, VirtualField
import list_utils

# If you change these, also update the manual!
COLUMN_NAMES: typing.Dict[RealOrVirtualField, str] = {
    Field.LAST_NAME: "Last Name",
    Field.FIRST_NAME: "First Name",
    Field.MIDDLE_NAME: "Middle Name",
    Field.STUDENT_ID: "Student ID",
    Field.COURSE_ID: "Course ID",
    Field.TEST_FORM_CODE: "Test Form Code",
    VirtualField.SCORE: "Total Score (%)",
    VirtualField.POINTS: "Total Points"
}

KEY_NOT_FOUND_MESSAGE = "NO KEY FOUND"


class OutputSheet():
    """A lightweight matrix of data to be exported. Faster than a dataframe but
    can be easily converted to one when the need arises."""
    # Must be structured as: field_a, field_b, ..., 1, 2, 3, ...
    data: typing.List[typing.List[str]]
    field_columns: typing.List[RealOrVirtualField]
    num_questions: int = NUM_QUESTIONS
    row_count: int

    def __init__(self, columns: typing.List[RealOrVirtualField]):
        self.field_columns = columns
        field_column_names = [COLUMN_NAMES[column] for column in columns]
        answer_columns = [str(i + 1) for i in range(self.num_questions)]
        self.data = [field_column_names + answer_columns]
        self.row_count = 0

    def save(self, path: pathlib.PurePath):
        with open(str(path), 'w+', newline='') as output_file:
            writer = csv.writer(output_file)
            writer.writerows(self.data)

    def add(self, fields: typing.Dict[RealOrVirtualField, str],
            answers: typing.List[str]):
        row: typing.List[str] = []
        for column in self.field_columns:
            try:
                row.append(fields[column])
            except KeyError:
                row.append('')
        self.data.append(row + answers)
        self.row_count = len(self.data) - 1

    def add_file(self, csvfile: pathlib.Path):
        with open(str(csvfile), 'r', newline='') as file:
            reader = csv.reader(file)
            names = next(reader)
            keys: typing.List[RealOrVirtualField] = []
            for name in names:
                try:
                    key = next(key for key, value in COLUMN_NAMES.items()
                               if value == name)
                except StopIteration:
                    pass
                keys.append(key)
            first_answer_index = list_utils.find_index(names, "1")
            for row in reader:
                fields = {
                    key: value
                    for key, value in list(zip(keys, row))[:first_answer_index]
                }
                answers = row[first_answer_index:]
                self.add(fields, answers)


def save_reordered_version(sheet: OutputSheet, arrangement_file: pathlib.Path,
                           save_path: pathlib.Path):
    """Reorder the output sheet based on a key arrangement file and save CSV."""
    # order_map will be a dict matching form code keys to a list where the
    # new index of question `i` in `key` is `order_map[key][i]`
    order_map: typing.Dict[str, typing.List[int]] = {}
    with open(str(arrangement_file), 'r', newline='') as file:
        reader = csv.reader(file)
        names = next(reader)
        form_code_index = list_utils.find_index(
            names, COLUMN_NAMES[Field.TEST_FORM_CODE])
        first_answer_index = list_utils.find_index(names, "1")
        for form in reader:
            form_code = form[form_code_index]
            to_order_zero_ind = [int(n) - 1 for n in form[first_answer_index:]]
            order_map[form_code] = to_order_zero_ind
    sheet_form_code_index = list_utils.find_index(
        sheet.data[0], COLUMN_NAMES[Field.TEST_FORM_CODE])
    sheet_first_answer_index = list_utils.find_index(sheet.data[0], "1")
    sheet_total_score_index = list_utils.find_index(
        sheet.data[0], COLUMN_NAMES[VirtualField.SCORE])
    results = [sheet.data[0]]
    for row in sheet.data[1:]:
        if row[sheet_total_score_index] != KEY_NOT_FOUND_MESSAGE:
            form_code = row[sheet_form_code_index]
            row_reordered = row[:sheet_first_answer_index] + [
                row[ind + sheet_first_answer_index]
                for ind in order_map[form_code]
            ]
            results.append(row_reordered)
        else:
            results.append(row)
    with open(str(save_path), 'w+', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerows(results)
