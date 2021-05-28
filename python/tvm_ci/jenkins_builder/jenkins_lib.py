import argparse
import contextlib
import logging
import pathlib
import subprocess
import threading
import time
import typing


from .. import utils


_LOG = logging.getLogger(__name__)


def add_arguments(parser):
    parser.add_argument("--jenkins-container", default="tvm_ci.jenkins:latest",
                        help="Container name to run")
    parser.add_argument("--jenkins-homedir", type=pathlib.Path,
                        help="Path to a non-existent Jenkins homedir to build.")
    parser.add_argument("--jenkins-port", type=int, default=8080,
                        help="Port number on local machine where the Jenkins HTTP port will be published")


def container_exists(container_id):
    proc = subprocess.Popen(["docker", "inspect", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    proc.wait()
    return proc.returncode == 0


def follow_logs(container_id : str, up_and_running : threading.Condition):
    proc = subprocess.Popen(["docker", "logs", "-f", container_id],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="UTF-8")
    did_set_condition = False
    for line in proc.stdout:
        _LOG.info("build.sh: %s", line[:-1])
        if not did_set_condition:
            if "Jenkins is fully up and running" in line:
                up_and_running.acquire()
                try:
                    up_and_running.notify()
                finally:
                    up_and_running.release()
                _LOG.info("----> Jenkins healthcheck passed")
                did_set_condition = True



def add_jenkins_args(parsed_args : argparse.Namespace, docker_args : list):
    docker_args.extend(["-v", f"{utils.get_repo_root() / 'jenkins-builder'}:/jenkins-builder"])
    docker_args.extend(["-v", f"{parsed_args.jenkins_homedir.absolute()}:/var/jenkins_home"])
    docker_args.extend(["-p", f"{parsed_args.jenkins_port}:8080"])


class JenkinsHealthCheckTimeoutError(Exception):
    """Raised when the health check is not passed within the given timeout."""


# Maximum number of seconds to wait for Jenkins to pass healthcheck. If it fails before this,
# assume it is busted.
JENKINS_LAUNCH_TIMEOUT_SEC = 5 * 60


@contextlib.contextmanager
def launch_jenkins(args : argparse.Namespace, cmd_line_args : list,
                   extra_docker_opts : typing.Optional[list] = None):
    docker_args = (["docker", "run", "--rm", "--detach"] +
                   (extra_docker_opts if extra_docker_opts is not None else []))
    add_jenkins_args(args, docker_args)
    docker_args.extend([args.jenkins_container] + cmd_line_args)
    container_id = str(subprocess.check_output(docker_args, cwd=utils.get_repo_root())[:-1], "utf-8")
    print('container', container_id)
    up_and_running = threading.Condition(threading.Lock())
    try:
        threading.Thread(target=follow_logs, args=(container_id, up_and_running), daemon=True).start()
        up_and_running.acquire()
        did_notify = up_and_running.wait(JENKINS_LAUNCH_TIMEOUT_SEC)
        if did_notify:
            yield container_id
        else:
            raise JenkinsHealthCheckTimeoutError(
                f"Jenkins did not pass healthcheck within {JENKINS_LAUNCH_TIMEOUT_SEC} seconds")
    finally:
        signal = "TERM"
        if container_exists(container_id):
            subprocess.check_call(["docker", "kill", "-s", "TERM", container_id])
            time.sleep(0.5)
            if container_exists(container_id):
                proc = subprocess.run(["docker", "kill", "-s", "KILL", container_id],
                                      capture_output=True)
                if proc.returncode != 0 and "No such container" not in proc.stderr:
                    proc.check_returncode()
