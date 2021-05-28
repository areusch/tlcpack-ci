# Networking Resources
resource "aws_vpc" "tvm-ci" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = "true"
  enable_dns_hostnames = "true"
  enable_classiclink = "false"

tags = {
    Name = "${var.name_prefix}tvm-ci-vpc"
    Environment = local.env
  }
}

# This provides internet connectivity for the public network
resource "aws_internet_gateway" "tvm-ci-gateway" {
  vpc_id = aws_vpc.tvm-ci.id
  tags = {
    Name = "${var.name_prefix}tvm-ci-gateway"
    Environment = local.env
  }

}

# public subnet
resource "aws_subnet" "tvm-ci-public" {
  vpc_id     = aws_vpc.tvm-ci.id
  cidr_block = "10.0.1.0/28"

  tags = {
    Name = "${var.name_prefix}tvm-ci-public"
    Environment = local.env
  }
}

# Make one subnet for each availability zone in the region.
data "aws_availability_zones" "executors" {
  state = "available"
  filter {
    name = "region-name"
    values = [var.aws_region]
  }
}

resource "aws_subnet" "executor-subnet" {
  count = length(data.aws_availability_zones.executors.names)

  vpc_id = aws_vpc.tvm-ci.id
  availability_zone = data.aws_availability_zones.executors.names[count.index]

  // Since we have to have 1 subnet per node, allocate the smallest possible subnet.
  cidr_block = "10.0.2.${(count.index + 1) * 16}/28"  // Minimum AWS CIDR is 28.

  tags = {
    Name = "{$var.name_prefix}executor_subnet_${data.aws_availability_zones.executors.names[count.index]}"
    Environment = local.env
  }
}

resource "aws_route_table" "tvm-ci-public" {
  vpc_id = aws_vpc.tvm-ci.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.tvm-ci-gateway.id
  }
  tags = {
    Name = "${var.name_prefix}tvm-ci-public"
    Environment = local.env
  }
}

resource "aws_route_table_association" "tvm-ci-public" {
  subnet_id      = aws_subnet.tvm-ci-public.id
  route_table_id = aws_route_table.tvm-ci-public.id
}


resource "aws_route_table_association" "executor-subnet" {
  count = length(aws_subnet.executor-subnet)

  subnet_id      = aws_subnet.executor-subnet[count.index].id
  route_table_id = aws_route_table.tvm-ci-public.id
}

locals {
  subnet_id_by_availability_zone = zipmap(data.aws_availability_zones.executors.names, [for s in aws_subnet.executor-subnet: s.id])
}

output "subnet_id_by_availability_zone" {
  value = local.subnet_id_by_availability_zone
}