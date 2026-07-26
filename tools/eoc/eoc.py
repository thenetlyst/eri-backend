from context import Context
from runner import Runner
from report import print_report

from checks.docker import DockerCheck





checks = [

    DockerCheck(),

]

context = Context()

runner = Runner(checks)

results = runner.execute(context)

print_report(results)