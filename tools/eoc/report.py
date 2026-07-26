def print_report(results):

    print()

    print("=" * 40)

    print("ERI Operations Center")

    print("=" * 40)

    for result in results:

        status = "PASS" if result.passed else "FAIL"

        print(
            f"{result.name:<20}"
            f"{status:<6}"
            f"{result.duration_ms:8.1f} ms"
        )

    print()