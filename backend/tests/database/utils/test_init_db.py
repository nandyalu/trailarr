from unittest import TestCase
from unittest.mock import patch
from backend.core.base.database.utils.init_db import init_db


class TestInitDB(TestCase):
    @patch("backend.database.utils.init_db.SQLModel")
    @patch("backend.database.utils.init_db.engine")
    def test_init_db(self, mock_engine, mock_sqlmodel):
        init_db()
        mock_sqlmodel.metadata.create_all.assert_called_once_with(bind=mock_engine)
