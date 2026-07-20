from adapter.intelligence_adapter import IntelligenceAdapter


def main():

    adapter = IntelligenceAdapter()

    # Case 1 — FAIL
    review1 = {
        "score": 20,
        "missing": ["logic"],
        "track": "backend"
    }

    # Case 2 — BORDERLINE
    review2 = {
        "score": 55,
        "missing": [],
        "track": "backend"
    }

    # Case 3 — PASS
    review3 = {
        "score": 85,
        "missing": [],
        "track": "backend"
    }

    print("Fail Case:")
    print(adapter.process(review1))

    print("\nBorderline Case:")
    print(adapter.process(review2))

    print("\nPass Case:")
    print(adapter.process(review3))


if __name__ == "__main__":
    main()