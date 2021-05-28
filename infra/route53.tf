data "aws_route53_zone" "primary" {
  name = var.tvm_ci_dns_zone_name
}


resource "aws_route53_record" "jenkins-head-node" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "${var.name_prefix}jenkins.${var.tvm_ci_dns_zone_name}"
  type    = "A"
  ttl     = "300"
  records = [aws_instance.jenkins-head-node.public_ip]
}

output "jenkins_head_node_fqdn" {
  value = aws_route53_record.jenkins-head-node.fqdn
}
