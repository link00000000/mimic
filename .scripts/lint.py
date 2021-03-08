"""
Lint all Python files in Mimic project.

All scripts prefixed with "lint-" will be executed.
"""
import os
import subprocess
import sys


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


env = os.environ.copy()
env["PIPENV_VERBOSITY"] = "-1"
process = subprocess.Popen(["pipenv", "scripts"],
                           stdout=subprocess.PIPE, env=env)
stdout, stderr = process.communicate()

lines = stdout.splitlines()
lines = list(filter(lambda line: len(line) > 0, lines))
lines = lines[2:]

decoded_lines = []
for line in lines:
    decoded_lines.append(line.decode('utf-8'))

PREFIX = "lint-"
lint_command_lines = list(
    filter(lambda line: line[0:len(PREFIX)] == PREFIX, decoded_lines))

for line in lint_command_lines:
    script_name = line.split()[0]

    print(bcolors.HEADER + f"Executing {script_name}..." + bcolors.ENDC)
    script_process = subprocess.Popen(
        ["pipenv", "run", script_name], env=env, stdout=subprocess.PIPE)

    script_stdout = script_process.communicate()[0]
    script_output = script_stdout.decode('utf-8').rstrip()
    if len(script_output) > 0:
        print(script_output)

    exit_code = script_process.returncode

    if(exit_code == 0):
        print(bcolors.OKGREEN +
              f"{script_name} completed successfully!" + bcolors.ENDC + '\n')
    else:
        print(bcolors.FAIL +
              f"There was an error executing {script_name}" + bcolors.ENDC + '\n')
        sys.exit()
