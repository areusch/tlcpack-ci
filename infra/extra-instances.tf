
# Terraform for extra instances for tvm open source jenkins
# https://ci.tlcpack.ai/
# Region us-west-2

locals {
  env = "open-source-tvm"
}

# Executor network policy
resource "aws_security_group" "all-nodes" {
  name = "${var.name_prefix}all-nodes"
  vpc_id = aws_vpc.tvm-ci.id

  # egress to anywhere on any port/protocol
  egress {
      from_port = 0
      to_port = 0
      protocol = -1
      cidr_blocks = ["0.0.0.0/0"]
  }

  # ssh from anywhere
  ingress {
    from_port = 22
    protocol = "tcp"
    to_port = 22
    cidr_blocks = var.ssh_allowed_cidr
  }
  depends_on = [aws_internet_gateway.tvm-ci-gateway]
  tags = {
    Environment = local.env
  }
}

module "cpu_executor" {
  source = "./modules/executor"

  ami_id = "ami-0db9c72b57c9c81e4"  # amazon/Deep Learning AMI (Ubuntu 18.04) Version 43.0
  name_prefix = var.name_prefix
  environment = local.env
  instance_count = var.cpu_instances_count
  instance_type = "g4dn.xlarge"
  label = "cpu"
  root_block_device_size_gib = 400
  route53_zone_id = data.aws_route53_zone.primary.zone_id
  route53_zone_fqdn = data.aws_route53_zone.primary.name
  route53_ttl = 300
  ssh_key_name = aws_key_pair.provisioner_ssh_key.key_name
  subnet_id_by_availability_zone = local.subnet_id_by_availability_zone
  tvm_ci_config_path = var.tvm_ci_config_path
  vpc_security_group_ids = [aws_security_group.all-nodes.id]
}

output "cpu_executor_fqdn" {
  value = module.cpu_executor.fqdn
}

module "gpu_executor" {
  source = "./modules/executor"

  ami_id = "ami-0db9c72b57c9c81e4"  # amazon/Deep Learning AMI (Ubuntu 18.04) Version 43.0
  name_prefix = var.name_prefix
  environment = local.env
  instance_count = var.gpu_instances_count
  instance_type = "g4dn.xlarge"
  label = "gpu"
  root_block_device_size_gib = 400
  route53_zone_id = data.aws_route53_zone.primary.zone_id
  route53_zone_fqdn = data.aws_route53_zone.primary.name
  route53_ttl = 300
  ssh_key_name = aws_key_pair.provisioner_ssh_key.key_name
  subnet_id_by_availability_zone = local.subnet_id_by_availability_zone
  tvm_ci_config_path = var.tvm_ci_config_path
  vpc_security_group_ids = [aws_security_group.all-nodes.id]
}

output "gpu_executor_fqdn" {
  value = module.gpu_executor.fqdn
}

module "arm_executor" {
  source = "./modules/executor"

  ami_id = "ami-044db9359bb5a43b6"  # tvm_jenkins_image_arm64
  name_prefix = var.name_prefix
  environment = local.env
  instance_count = var.arm_instances_count
  instance_type = "m6g.xlarge"
  label = "arm"
  root_block_device_size_gib = 400
  route53_zone_id = data.aws_route53_zone.primary.zone_id
  route53_zone_fqdn = data.aws_route53_zone.primary.name
  route53_ttl = 300
  ssh_key_name = aws_key_pair.provisioner_ssh_key.key_name
  subnet_id_by_availability_zone = local.subnet_id_by_availability_zone
  tvm_ci_config_path = var.tvm_ci_config_path
  vpc_security_group_ids = [aws_security_group.all-nodes.id]
}

output "arm_executor_fqdn" {
  value = module.arm_executor.fqdn
}
