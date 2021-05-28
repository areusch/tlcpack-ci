resource "aws_key_pair" "provisioner_ssh_key" {
  key_name = "${var.name_prefix}tvm-ci-provisioner"
  public_key = file(var.provisioner_ssh_pubkey_file)
}
