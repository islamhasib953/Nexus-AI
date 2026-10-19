import os

# Set default test environment so unit and regression tests run deterministically
# with mock provider and local isolation, independent of personal .env.local credentials.
os.environ["MODEL_PROVIDER"] = "mock"
os.environ["MODEL_NAME"] = "mock-chat"
os.environ["LLM_PRIMARY_MODEL_ID"] = "mock-chat"
