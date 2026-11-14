import os
import tempfile

os.environ.setdefault("JWT_SECRET", "segredo-de-teste-com-mais-de-trinta-e-dois-caracteres")
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/teste.db"
