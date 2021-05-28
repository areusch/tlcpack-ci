data "external" "executor_subnet_id" {
  program = ["poetry", "run", "python", "-m", "tvm_ci.lookup_availability_zones",
             "--tvm-ci-config", var.tvm_ci_config_path, "--instance-type", var.instance_type]

  query = var.subnet_id_by_availability_zone
}

resource "aws_instance" "executor" {
  # number defined above
  count = var.instance_count

  ami = var.ami_id
  associate_public_ip_address = "true"
  instance_type = var.instance_type
  key_name = var.ssh_key_name
  subnet_id = data.external.executor_subnet_id.result["id"]
  vpc_security_group_ids = var.vpc_security_group_ids

  root_block_device {
    volume_size = var.root_block_device_size_gib
  }

  tags = {
    "role" = "jenkins-executor"
    "label" = var.label
    Environment = var.environment
    Name = "${var.name_prefix}cpu-executor-${count.index}"
  }
}

resource "aws_route53_record" "executor" {
  count =  var.route53_zone_id != "" ? var.instance_count : 0

  zone_id = var.route53_zone_id
  name    = "${var.name_prefix}jenkins-${var.label}-executor-${count.index}.${var.route53_zone_fqdn}"
  type    = "A"
  ttl     = var.route53_ttl
  records = [aws_instance.executor[count.index].public_ip]
}

output "fqdn" {
  value = [for e in aws_route53_record.executor: e.name]
}