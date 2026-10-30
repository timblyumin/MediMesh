import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import read_patients
from app.models import Patient


class TestPatientSearch(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([
            Patient(name="Alice Smith", age=25, department="ER", acuity_level=2),
            Patient(name="Alice Jones", age=40, department="ICU", acuity_level=4),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_search_trims_extra_spaces(self):
        patients = read_patients(name="  Alice Smith\t", db=self.db)
        self.assertEqual([p.name for p in patients], ["Alice Smith"])

    def test_blank_search_returns_all_patients(self):
        for name in (None, "", "   "):
            with self.subTest(name=name):
                patients = read_patients(name=name, db=self.db)
                self.assertEqual(len(patients), 2)

    def test_unknown_name_returns_empty_list(self):
        self.assertEqual(read_patients(name="Unknown", db=self.db), [])

    def test_search_works_with_other_filters(self):
        patients = read_patients(
            name=" Alice ", department="ICU", acuity=4, db=self.db
        )
        self.assertEqual([p.name for p in patients], ["Alice Jones"])



    def test_rejects_negative_pagination(self):
        for skip, limit in ((-1, 1), (0, -1), (-1, -1)):
            with self.subTest(skip=skip, limit=limit):
                with self.assertRaises(HTTPException) as error:
                    read_patients(skip=skip, limit=limit, db=self.db)
                self.assertEqual(error.exception.status_code, 422)

    def test_pagination_returns_separate_pages(self):
        first = read_patients(name="Alice", skip=0, limit=1, db=self.db)
        second = read_patients(name="Alice", skip=1, limit=1, db=self.db)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertNotEqual(first[0].id, second[0].id)

    def test_empty_pages_return_empty_list(self):
        self.assertEqual(read_patients(limit=0, db=self.db), [])
        self.assertEqual(read_patients(skip=10, db=self.db), [])

if __name__ == "__main__":
    unittest.main()
