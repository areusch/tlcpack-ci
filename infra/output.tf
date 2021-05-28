output "jenkins_head_node_public_ip" {
  value = aws_instance.jenkins-head-node.public_ip
}

output "zone_ns_output" {
  value = data.aws_route53_zone.primary.name_servers
}
