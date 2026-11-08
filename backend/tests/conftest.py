from pathlib import Path

import pytest

from app.services.catalogue.loader import load_catalogue


@pytest.fixture
def catalogue():
    path = (
        Path(__file__).resolve().parents[2]
        / "YTL_TrackA_Udyam_Digital_Data"
        / "product_catalogue.csv"
    )
    return load_catalogue(path)
