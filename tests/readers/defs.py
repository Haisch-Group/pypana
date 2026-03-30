from pathlib import Path

from pypana.readers.tsi.tsi_las3340a import TSILAS3340AInstrumentReader
from pypana.readers.tsi.tsi_smps3071 import TSISMPS3071InstrumentReader

EXAMPLE_FILES_DIR = Path(__file__).resolve().parents[2] / "ExampleFiles"

NON_EXISTING_FILE = EXAMPLE_FILES_DIR / "non_existing_file"
NON_INSTRUMENT_FILE = Path(__file__).resolve().parents[2] / "pyproject.toml"
TSILAS3340A_FILE = EXAMPLE_FILES_DIR / "20240704_TSI_LAS3340A"
TSISMPS3071_FILE = EXAMPLE_FILES_DIR / "20211111_TSI_SMPS3071.txt"

INSTRUMENT_READER_TEST_CASES = [
    (TSILAS3340A_FILE, TSILAS3340AInstrumentReader),
    (TSISMPS3071_FILE, TSISMPS3071InstrumentReader),
]
