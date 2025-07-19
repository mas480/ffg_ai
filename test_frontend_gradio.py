import os
import shutil
import tempfile
from frontend_gradio import clean_text, save_uploaded_files_locally

def test_clean_text_removes_surrogates():
    dirty_text = "valid text \ud83d"
    cleaned = clean_text(dirty_text)
    assert "\ud83d" not in cleaned

def test_save_uploaded_files_locally_creates_folder_and_copies():
    with tempfile.TemporaryDirectory() as tmpdir:
        original_file = os.path.join(tmpdir, "test.jpg")
        with open(original_file, "w") as f:
            f.write("dummy")

        saved = save_uploaded_files_locally("user1", "test_section", original_file)
        assert len(saved) == 1
        assert os.path.exists(saved[0])
        shutil.rmtree(os.path.dirname(saved[0]), ignore_errors=True)