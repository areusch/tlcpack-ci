# TVM CI Infrastructure-as-Code Repository

## What is this?

This repository contains scripts and configuration files that allow anyone to launch a copy of the
TLCPack Continuous Integration service using their AWS account. It serves as documentation that
fully describes all of the configuration settings needed to reproduce the TLCPack CI. The TLCPack CI
is used in conjunction with the Apache TVM Project for continuous integration testing.

Using this repository will cost money, as the only way to describe the CI in a universally-reproducible
way is to do it in terms of AWS-provided services. However, this repository makes it possible to
accomplish some rare tasks needed to maintain the TVM open-source project (testing modifications to the
CI, expanding CI coverage to devices outside of AWS, etc).

### Installing dependencies

Dependencies are:

### Locally

1. Provide credentials.

    1. Obtain an [AWS Access Key](https://console.aws.amazon.com/iam/home#/security_credentials), place in `config/secrets/aws-credentials`. Follow this format:
       ```
       [profile_name]
       aws_access_key_id = <access_key_id>
       aws_secret_access_key = <secret_access_key>
       ```

    2. Obtain a [GitHub Personal Access Token](https://github.com/settings/tokens), place in `config/secrets/github-personal-access-token`. The file should just contain exactly the token, no formatting needed.

2. Configure config/dev.yaml. In particular:
    1. Set `docker.jenkins_container_name` to `<your_docker_hub_account_id>/<container_name>`.
    2. Set `cluster.aws_profile_name` to `profile_name` from the `aws-credentials` file above.
    3. Set the number of each node type to create (currently only CPU supported).
    4. Set `cluster.name_prefix` to something that can be used to distinguish your nodes from others
       in the same AWS account. This will also be prepended to the DNS name.
    5. Set `cluster.dns_suffix_name` to the FQDN of the DNS zone which will hold all executor nodes'
       DNS names (in the same AWS account). This zone will not be created--it should already exist.
    5. Set `jenkins.review_bot_github_username` to the github username for the Personal Access Token
       in `config/secrets/github-personal-access-token`.

3. Sign in to docker with `docker login`.
4. Ensure `ssh-agent` is running and has your keys added (`ssh-add -L`). If not:
    1. `eval $(ssh-agent)`
    2. `ssh-add`

5. Bring up the cluster:
    1. Build the "crane" container which contains all dependencies: `./bootstrap.sh`
    2. Build docker container and run local planning: `stage-scripts/1-create-plan.sh`
    3. Apply Terraform plan to create AWS nodes: `stage-scripts/2-apply-plan.sh`
    4. Configure nodes to run Jenkins: `stage-scripts/3-provision-provision.sh`. You should see a
       play recap like so:
       ```
       PLAY RECAP ***************************************************************************************************************************************************************************
       areusch-jenkins-cpu-executor-0.tvm.octoml.ai : ok=9    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
       areusch-jenkins-cpu-executor-1.tvm.octoml.ai : ok=9    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
       areusch-jenkins.tvm.octoml.ai : ok=17   changed=15   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
       ```

        - Ensure you see 0's for failed and unreachable.
        - Sometimes SSH problems can foul this up. If so, rerun this command.

6. To access the Jenkins main page, you need to login to the "head node" over SSH: `tools/ssh.sh head`
7. Triggering a build:
    - For some reason, multibranch indexing seems to hang on launch and no builds are scheduled.
    - Navigate to the TVM project, then click Scan Repository Now in toolbar.
    - You need to create a branch named `test-pr` for test Jenkins to build it. Ensure it is up-to-date
      with the `main` branch in your repo.
