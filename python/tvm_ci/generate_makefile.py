# This script creates Makefile and .gitlab-ci.yml

import collections
import logging
import os
import pathlib
import re
import typing

import yaml

from . import utils


_LOG = logging.getLogger(__name__)


STAGE_SCRIPTS_DIR = utils.get_repo_root() / "stage-scripts"


STAGE_SCRIPT_RE = re.compile(r"^(?P<stage_name>[a-z0-9_]+)-(?P<step_number>[0-9]+)-"
                             r"(?P<step_name>[a-z0-9_]+)\.sh$")


def _check_script_name(expected_step_number_digits : int, m : re.Match) -> bool:
    step_number = int(m.group("step_number"))
    step_number_digits = len(m.group("step_number"))
    formatted_step_number = (
        "0" * (expected_step_number_digits - step_number_digits) + str(step_number))

    if formatted_step_number == m.group("step_number"):
        return False

    groups = m.groupdict()
    _LOG.error("Stage script \"%s\": expected %d digits in step number, got %d. "
               "Suggest rename to \"%s\"",
               m.group(0), expected_step_number_digits, step_number_digits,
               f"{groups['stage_name']}-{formatted_step_number}-{groups['step_name']}.sh")
    return True


class StageScriptNamingError(Exception):
   """Raised when naming errors exist in the stage-scripts directory."""


def build_stages(scripts_dir : pathlib.Path = STAGE_SCRIPTS_DIR) -> typing.Dict[str, typing.List[str]]:
    """Build a map of stage_name to list of scripts that make up that stage.

    This function calls glob() on stage-scripts directory and examines files that follow
    the following format:

        <stage_name>-<n>-<step_name>.sh

    Where:
     - <stage_name> is the name of the stage (underscores for spaces, no "-" allowed).
     - <n> is an incrementing integer and the number of digits is the same for all steps in the
       stage.
     - <step_name> is the name of the step (underscores for spaces, no "-" allowed).

    Parameters
    ----------
    scripts_dir : pathlib.Path
        Path to the stage-scripts directory. Parameterizable for testing.

    Returns
    -------
    Dict[str, list[str]] :
        A dict mapping <stage_name> to a list of scripts that make up that stage, in the order
        they are to be executed.
    """
    stage_scripts = {}
    for f in scripts_dir.glob("*.sh"):
        _LOG.debug("script: %s", f)
        m = STAGE_SCRIPT_RE.match(f.name)
        if not m:
            _LOG.debug("Skipping non-matching script: %s", f)
            continue

        stage_scripts.setdefault(m.group("stage_name"), [])
        stage_scripts[m.group("stage_name")].append(m)

    found_naming_error = False
    stages_by_name = {}
    for stage_name, matches in stage_scripts.items():
        expected_step_number_digits = max(len(m.group("step_number")) for m in matches)
        scripts_by_step_number = {}
        stages_by_name[stage_name] = []

        for m in matches:
            if _check_script_name(expected_step_number_digits, m):
                found_naming_error = True

            step_number = int(m.group("step_number"))
            if step_number in scripts_by_step_number:
                _LOG.error("Duplicate scripts for step number %d: %s and %s",
                           step_number, scripts_by_step_number[step_number],
                           m.group(0))
                found_naming_error = True
                continue

            scripts_by_step_number[step_number] = m.group(0)
            stages_by_name[stage_name].append(m.group(0))

        stages_by_name[stage_name].sort()

    if found_naming_error:
        _LOG.error("Naming errors were found in the script filenames in directory \"%s\". "
                   "Consult previous log messages.",
                   scripts_dir)
        raise StageScriptNamingError()

    return stages_by_name


class MakefileTemplateError(Exception):
    """Raised when an error occurs templating the makefile."""


MAKEFILE_DEFINE_STAGES_LINE = "# TEMPLATE: DEFINE STAGES\n"


MAKEFILE_END_DEFINE_LINE = "# TEMPLATE: END STAGES\n"


STAGE_DEP_RE = re.compile(
    r"^(?P<stage_name>[a-z0-9_]+): *(?P<stage_deps>(?:(?:[a-z0-9_]+) )*)$")


def _done_path(script_name):
    return pathlib.Path(f"$(BUILD_DIR)/{os.path.splitext(script_name)[0]}.log.done")


def generate_makefile(stages_by_name, stage_order):
    with open(utils.get_repo_root() / "template.mk") as makefile_f:
        template = makefile_f.read()

    stage_rules = []
    stage_deps = []
    for stage_name in stage_order:
        stage_rules.append(f"##### Stage: {stage_name} -->")
        last_done_path = ""
        for script in stages_by_name[stage_name]:
            done_path = _done_path(script)
            log_path = os.path.splitext(done_path)[0]
            stage_dep_logs = " ".join(str(_done_path(stages_by_name[n][-1])) for n in stage_deps)
            stage_rules.append(f"{done_path}: {last_done_path} {stage_dep_logs}")
            stage_relpath = STAGE_SCRIPTS_DIR.relative_to(utils.get_repo_root())
            stage_rules.append(f"\t$(QUIET){stage_relpath}/run-stage-script.sh $(BUILD_DIR) {script}")
            last_done_path = done_path

        stage_rules.append(f"{stage_name}: {last_done_path}")
        stage_rules.append(f".PHONY: {stage_name}")
        stage_rules.append("##### <-- End Stage: {stage_name}")
        stage_rules.append("")

        stage_deps.append(stage_name)

    with open(utils.get_repo_root() / "Makefile", "w") as makefile_f:
        makefile_f.write("# AUTOGENERATED DO NOT EDIT\n")
        makefile_f.write(f"# See template.mk and/or {__file__} for more details.\n")
        makefile_f.write("\n")

        makefile_f.write(template.format(STAGE_RULES="\n".join(stage_rules)))


# See https://docs.gitlab.com/ee/ci/yaml/README.html#unavailable-names-for-jobs
GITLAB_NON_JOBS = (
    "image",
    "services",
    "stages",
    "types",
    "before_script",
    "after_script",
    "variables",
    "cache",
    "include",
)


JOB_DEFINITION_RE = re.compile(r"^(?P<job_name>\.{0,1}(?P<stage_name>[a-z0-9_]+)):.*$")


def _validate_gitlab_ci_yml(stages_by_name, gitlab_ci):
    """Ensure .gitlab-ci.yml is well-formed enough for us to work with it.

    In particular, want to enforce the following:
    1. All stages defined in scripts are stages here in the same order
    2. Each stage has exactly one job defined named after it. Jobs can be disabled, in which
       case the name should be just prefixed with a ".".

    This will probably change as we evolve this repo.


    Parameters
    ----------
    stages_by_name : dict[str, list[str]]
        A list mapping stage name to a list of scripts which make up that stage.

    gitlab_ci : dict
        The parsed .gitlab-ci.yml file.

    Raises
    ------
    GitLabCiValidationError:
        When a problem is detected with .gitlab-ci.yml. Before raising, the problem described on
        _LOG.error().
    """
    gitlab_stages = gitlab_ci["stages"]

    found_stage_error = False
    for stage in stages_by_name:
        if stage not in gitlab_stages:
            _LOG.error("Stage not found in .gitlab-ci.yml: %s", stage)
            found_stage_error = True

    if found_stage_error:
        _LOG.error(".gitlab-ci.yml \"stages\" key doesn't list all stages. See preceding errors.")
        raise GitLabCiValidationError()

    # Now, just enforce that each stage has one job.
    found_job_error = False
    jobs_by_stage = {stage: [] for stage in stages_by_name}
    for key, value in gitlab_ci.items():
        if key in GITLAB_NON_JOBS:
            continue

        # See default documented at https://docs.gitlab.com/ee/ci/yaml/README.html#stage
        stage = value.get("stage", "test")
        if stage not in stages_by_name:
            _LOG.debug("Ignoring job \"%s\" in stage \"%s\": not part of a released stage",
                       key, stage)
            continue

        jobs_by_stage[stage].append(key)
        if "script" not in value:
            _LOG.error("Job \"%s\" does not define a \"script\" key.", key)
            found_job_error = True
            continue

    for stage, jobs in jobs_by_stage.items():
        if len(jobs) != 1:
            _LOG.error("Stage \"%s\" has <> 1 job defined: %s", stage, ", ".join(jobs))
            found_job_error = True
            continue

        gitlab_ci[jobs[0]]["script"] = [f"{STAGE_SCRIPTS_DIR}/{s}" for s in stages_by_name[stage]]

    if found_job_error:
        raise GitLabCiValidationError()


SCRIPT_KEY_RE = re.compile(r"^(?P<indent>[ ]+)script:.*$")


SCRIPT_LINE_RE = re.compile(r"^^[ ]+- .*$")


def _update_job_scripts(job_name, old_lines, i, scripts, new_lines):
    """Update the "script" key for a .gitlab-ci.yml job description.

    Parameters
    ----------
    job_name : str
        Name of the .gitlab-ci.yml job to update.
    old_lines : list[str
        A list of the lines in .gitlab-ci.yml.
    i : int
        The index in old_list where the job definition starts.
    scripts : list[str]
        A list of script filenames (relative to stage-scripts/) which make up this stage (and job).
    new_lines : list[str]
        A list which will be appended with the updated lines.

    Returns
    -------
    int :
        Index into old_lines of the next line to consume. May also return i == len(old_lines), in
        which case this function consumed all input from old_lines. All consumed input other than
        the "script" key will be appended to new_lines.

    Raises
    ------
    GitLabCiValidationError :
        If there is a problem finding the "script" key.
    """
    new_lines.append(old_lines[i])
    i += 1
    found_scripts_key = False
    while i < len(old_lines):
        line = old_lines[i]
        i += 1

        new_lines.append(line)
        m = SCRIPT_KEY_RE.match(line)
        if m is not None:
            found_scripts_key = True
            indent = m.group("indent")
            break

        if line and line[0] != " ":
            break

    if not found_scripts_key:
        _LOG.error("Job \"%s\" has no script: key", job_name)
        raise GitLabCiValidationError()

    for s in scripts:
        new_lines.append(f"{indent} - {s}")

    while i < len(old_lines):
        line = old_lines[i]
        i += 1
        if not SCRIPT_LINE_RE.match(line):
            break

    # NOTE: even if we didn't get all the way through the section, it will be written out by calling
    # function.
    return i


def process_gitlab_ci(stages_by_name):
    """Read .gitlab-ci.yml to deduce stage ordering, and update job "scripts" keywords."""
    gitlab_ci_yml_path = utils.get_repo_root() / ".gitlab-ci.yml"
    with open(gitlab_ci_yml_path) as gitlab_ci_yml_f:
        gitlab_ci_yml_contents = gitlab_ci_yml_f.read()

    gitlab_ci_yml = yaml.safe_load(gitlab_ci_yml_contents)

    _validate_gitlab_ci_yml(stages_by_name, gitlab_ci_yml)

    # Finally, update the scripts attached to each job. Do this in plaintext to avoid messing with
    # indentation.
    old_lines = gitlab_ci_yml_contents.split("\n")
    new_lines = []
    i = 0
    while i < len(old_lines):
        line = old_lines[i]
        # Search for a job definition:
        m = JOB_DEFINITION_RE.match(line)
        if not m:
            i += 1
            continue

        if m.group("stage_name") in stages_by_name:
            i = _update_job_scripts(m.group("stage_name"), old_lines, i, stages_by_name[m.group("stage_name")], new_lines)
        else:
            _LOG.debug("Ignoring job \"%s\" which is not shared with the Makefile", m.group("job_name"))
            i += 1

    return [x for x in gitlab_ci_yml["stages"] if x in stages_by_name]


def main():
    logging.basicConfig(level="DEBUG")
    stages_by_name = build_stages()
    _LOG.info("Found stages: %s", ", ".join(stages_by_name))
    stage_order = process_gitlab_ci(stages_by_name)
    generate_makefile(stages_by_name, stage_order)


if __name__ == '__main__':
    main()
