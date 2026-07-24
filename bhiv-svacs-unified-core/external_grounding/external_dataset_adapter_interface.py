class DatasetAdapter:

    def connect(self):
        return "CONNECTED"

adapter = DatasetAdapter()

print(adapter.connect())
print("EXTERNAL_GROUNDING_READY")
