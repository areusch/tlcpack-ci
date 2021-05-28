
resource "aws_instance" "jenkins-head-node" {

  ami              = "ami-0996d3051b72b5b2c"  # ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20210129
  instance_type    = var.jenkins_master_ec2_instance_type
  subnet_id        = aws_subnet.tvm-ci-public.id
  vpc_security_group_ids  = [aws_security_group.all-nodes.id]
  key_name         = aws_key_pair.provisioner_ssh_key.key_name
  associate_public_ip_address = true
  root_block_device {
    volume_size = var.jenkins_master_root_ebs_volume_size_gb
  }
  timeouts {
    create = "60m"
    update = "60m"
  }

  tags = {
    Name         = "${var.name_prefix}jenkins-head-node"
    Application  = "jenkins-head-node"
    Environment  = local.env
    Project      = "ML/SYS"
    OS           = "Ubuntu"
  }
}
