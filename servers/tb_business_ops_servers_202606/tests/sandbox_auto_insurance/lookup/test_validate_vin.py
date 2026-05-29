# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_auto_insurance.lookup.tools.validate_vin import (
    ValidateVinTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db(tmp_path):
    """Create an empty in-memory database for running the tool."""
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    return InMemoryDatabase(str(db_dir))


@pytest.fixture
def tool():
    """Instance of VIN validation tool."""
    return ValidateVinTool()


@pytest.mark.anyio
async def test_validate_vin_success_honda(tool, db):
    # VIN with Honda WMI (1HG) and year code 'A' at position 10 (index 9)
    request = {"vin": "1HGCM8263A0123456"}  # 'A' at position 10 = year 2010

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["valid"] is True
    assert result["make"] == "Honda"
    assert result["model"] == "Accord"
    assert result["year"] == 2010


@pytest.mark.anyio
async def test_validate_vin_success_no_known_mapping(tool, db):
    request = {"vin": "XYZCM82633Z999999"}  # unknown WMI & unknown year code

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["valid"] is True

    assert "make" not in result
    assert "model" not in result
    assert "year" not in result


@pytest.mark.anyio
async def test_validate_vin_error_short_vin(tool, db):
    request = {"vin": "123"}

    with pytest.raises(tool.ExecutionError, match="VIN must be exactly 17 characters"):
        await tool.run_with_validation(db, request)


@pytest.mark.anyio
async def test_validate_vin_error_long_vin(tool, db):
    request = {"vin": "1" * 20}

    with pytest.raises(tool.ExecutionError, match="VIN must be exactly 17 characters"):
        await tool.run_with_validation(db, request)


@pytest.mark.anyio
async def test_validate_vin_error_non_alphanumeric(tool, db):
    request = {"vin": "1HGCM8$633A123456"}

    with pytest.raises(
        tool.ExecutionError, match="must contain only letters and numbers"
    ):
        await tool.run_with_validation(db, request)


@pytest.mark.anyio
async def test_validate_vin_strips_whitespace(tool, db):
    request = {"vin": "   1HGCM8263A0123456   "}

    result = await tool.run_with_validation(db, request)

    assert result["valid"] is True
    assert result["make"] == "Honda"
    assert result["model"] == "Accord"
    assert result["year"] == 2010


@pytest.mark.anyio
async def test_validate_vin_lowercase_input(tool, db):
    request = {"vin": "1hgcm8263a0123456"}

    result = await tool.run_with_validation(db, request)

    assert result["valid"] is True
    assert result["make"] == "Honda"
    assert result["model"] == "Accord"
    assert result["year"] == 2010


@pytest.mark.anyio
async def test_validate_vin_year_2024(tool, db):
    """Test VIN with year code 'R' (2024) at correct position 10 (index 9)."""
    request = {"vin": "19XFL2H82RE000123"}  # 'R' at position 10 should decode to 2024

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["valid"] is True
    assert result["year"] == 2024  # Year code 'R' at position 10 (index 9)
    # WMI '19X' is not in the known mapping, so make/model fields excluded (None)
    assert "make" not in result
    assert "model" not in result
