# IP fixo: o endereço não muda quando a instância é desligada e religada.
resource "aws_eip" "assistente" {
  domain   = "vpc"
  instance = aws_instance.assistente.id
  tags     = { Name = "${var.nome}-ip" }
}

resource "aws_route53_record" "assistente" {
  zone_id = data.aws_route53_zone.zona.zone_id
  name    = "${var.subdominio}.${var.zona_dns}"
  type    = "A"
  ttl     = 60
  records = [aws_eip.assistente.public_ip]
}
