# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import traceback
import json
from pydantic_core import to_jsonable_python

def success_response(**kwargs) -> str:
    obj = {
        "status": "ok",
        **to_jsonable_python(kwargs),
    }
    return json.dumps(obj)


def error_response(exc) -> str:
    traceback.print_exc()
    return "Error!\n" + str(exc)