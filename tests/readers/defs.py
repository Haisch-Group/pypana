from pathlib import Path

from pypana.readers.palas.palas_usmps import PALASUSMPSInstrumentReader
from pypana.readers.palas.palas_welas import PALASWelasInstrumentReader
from pypana.readers.tsi.tsi_aps3321 import TSIAPS3321InstrumentReader
from pypana.readers.tsi.tsi_las3340a import TSILAS3340AInstrumentReader
from pypana.readers.tsi.tsi_smps3071 import TSISMPS3071InstrumentReader

EXAMPLE_FILES_DIR = Path(__file__).resolve().parents[2] / "ExampleFiles"

NON_EXISTING_FILE = EXAMPLE_FILES_DIR / "non_existing_file"
NON_INSTRUMENT_FILE = Path(__file__).resolve().parents[2] / "pyproject.toml"
TSILAS3340A_FILE = EXAMPLE_FILES_DIR / "20240704_TSI_LAS3340A"
TSISMPS3071_FILE = EXAMPLE_FILES_DIR / "20211111_TSI_SMPS3071.txt"
TSIAPS3321_FILE1 = EXAMPLE_FILES_DIR / "20250932_TSI_APS3321.txt"
TSIAPS3321_FILE2 = EXAMPLE_FILES_DIR / "20230516_TSI_APS3321.TXT"
PALASWELAS_FILE1 = EXAMPLE_FILES_DIR / "20250822_PALAS_WELAS.txt"
PALASUSMPS_FILE1 = EXAMPLE_FILES_DIR / "20240625_PALAS_USMPS.txt"
PALASUSMPS_FILE2 = EXAMPLE_FILES_DIR / "20221215_PALAS_USMPS.txt"
PALASUSMPS_FILE3 = EXAMPLE_FILES_DIR / "20230704_PALAS_USMPS.txt"

INSTRUMENT_READER_TEST_CASES = [
    (TSILAS3340A_FILE, TSILAS3340AInstrumentReader),
    (TSISMPS3071_FILE, TSISMPS3071InstrumentReader),
    (TSIAPS3321_FILE1, TSIAPS3321InstrumentReader),
    (TSIAPS3321_FILE2, TSIAPS3321InstrumentReader),
    (PALASWELAS_FILE1, PALASWelasInstrumentReader),
    (PALASUSMPS_FILE1, PALASUSMPSInstrumentReader),
    (PALASUSMPS_FILE2, PALASUSMPSInstrumentReader),
    (PALASUSMPS_FILE3, PALASUSMPSInstrumentReader),
]
