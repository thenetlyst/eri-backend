import time


class Runner:

    def __init__(self, checks):

        self.checks = checks

    def execute(self, context):

        results = []

        for check in self.checks:

            start = time.perf_counter()

            result = check.execute(context)

            result.duration_ms = (
                time.perf_counter() - start
            ) * 1000

            results.append(result)

            if check.CRITICAL and not result.passed:

                break

        return results