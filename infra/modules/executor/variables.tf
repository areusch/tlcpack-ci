variable "ami_id" {
  description = "ID of the AMI to use"
  type = string
}

variable "instance_type" {
  description = "AWS instance type"
  type = string
}

variable "environment" {
  description = "Value of the Environment tag"
}

variable "instance_count" {
  description = "Number of instances of this type to create"
  default = 1
  type = number
}

variable "label" {
  description = "Jenkins label of the node, used to form the FQDN and in instance labels."
}

variable "name_prefix" {
  description = "Prefix applied to all resources"
  default = ""
  type = string
}

variable "root_block_device_size_gib" {
  description = "Size of the root_block_device, in GiB"
  type = number
}

variable "route53_ttl" {
  description = "TTL of A records."
  type = number
}

variable "route53_zone_fqdn" {
  description = "FQDN of the zone containing the A record for the executors. Ignored when route53_zone_id is empty."
}

variable "route53_zone_id" {
  description = "If specified, ID of the Route 53 zone to update"
  default = ""
}

variable "ssh_key_name" {
  description = "The SSH key to use"
}

variable "subnet_id_by_availability_zone" {
  description = "Map from availability zone name to subnet id"
}

variable "tvm_ci_config_path" {
  description = "Path to CI config, used to lookup an availability zone."
  type = string
}

variable "vpc_security_group_ids" {
  description = "Security groups to use on the VPC"
}
