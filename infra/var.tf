##### AWS Provider Configuration --->

variable "aws_region" {
}

variable "aws_credentials_file" {
}

variable "aws_credentials_profile" {
}

##### Shared Configuration --->

# A prefix applied to all names of AWS resources created by this TF logic.
variable "name_prefix" {
  default = "areusch-"
}

##### <--- Shared Configuration

##### Jenkins Master Configuration -->

variable "jenkins_master_ec2_instance_type" {
  description = "EC2 Instance Type used to run the Jenkins master container."
  default = "t3.xlarge"
}

variable "jenkins_master_root_ebs_volume_size_gb" {
  description = "Disk size on the Jenkins master node."
  default = "500"
}

variable "tvm_ci_dns_zone_name" {
  description = "Name of the DNS zone under which the TVM node will live"
  default = "tvm.octoml.ai"
}

##### <-- Jenkins Master Configuration

##### SSH Configuration --->

variable "provisioner_ssh_pubkey_file" {
  description = "SSH Public Key file used to provision Jenkins and executor nodes."
}

variable "provisioner_ssh_private_key_file" {
  description = "SSH Private Key file used to provision Jenkins and executor nodes."
}

variable "ssh_allowed_cidr" {
  description = "CIDR block from which SSH connections are allowed."
  type    = list(string)
  default = ["0.0.0.0/0"]
}

##### <--- SSH Configuration


##### Permanent Worker Node Configuration --->

variable "arm_instances_count" {
  description = "Number of instances assigned the 'ARM' label in jenkins"
  type        = number
  default     = 1
}

variable "cpu_instances_count" {
  description = "Number of instances assigned the 'CPU' label in jenkins"
  type        = number
  default     = 1
}

variable "gpu_instances_count" {
  description = "Number of instances assigned the 'GPU' label in jenkins"
  type        = number
  default     = 1
}

##### <--- Permanent Worker Node Configuration

variable "tvm_ci_config_path" {
  description = "Path to the ci-config yaml file, used for sub-utilities"
  type = string
}