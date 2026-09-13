# Rede: usa a VPC padrão da conta e escolhe uma sub-rede pública dela.
data "aws_vpc" "padrao" {
  default = true
}

data "aws_subnets" "padrao" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.padrao.id]
  }
}

# Imagem Deep Learning da AWS: já vem com driver Nvidia, CUDA e PyTorch.
# Busca sempre a mais recente, em vez de fixar um ID que envelhece.
data "aws_ami" "deep_learning" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.7 (Ubuntu 22.04)*"]
  }
}

data "aws_route53_zone" "zona" {
  name         = "${var.zona_dns}."
  private_zone = false
}
