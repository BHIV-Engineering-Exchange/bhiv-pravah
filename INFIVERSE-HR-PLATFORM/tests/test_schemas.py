import json
import glob
import os
import pytest
from jsonschema import Draft7Validator, ValidationError


SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'schemas')


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.mark.parametrize('schema_file', glob.glob(os.path.join(SCHEMA_DIR, '*.json')))
def test_schema_examples_validate(schema_file):
    schema = load_json(schema_file)
    validator = Draft7Validator(schema)

    examples = schema.get('examples') or []
    # If no examples are present, treat as a smoke check that schema parses
    if not examples:
        assert isinstance(schema, dict)
        return

    errors = []
    for ex in examples:
        errs = list(validator.iter_errors(ex))
        if errs:
            errors.append((ex, errs))

    if errors:
        msg_lines = [f"Schema: {os.path.basename(schema_file)} had {len(errors)} invalid example(s):"]
        for ex, errs in errors:
            msg_lines.append(f"Example: {json.dumps(ex)[:200]}")
            for e in errs:
                msg_lines.append(f" - {e.message}")
        pytest.fail('\n'.join(msg_lines))
