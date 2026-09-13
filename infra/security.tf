# Grupo de segurança: nenhuma porta de SSH. O terminal vem do Session Manager,
# que sai da instância para a AWS, sem porta de entrada.
resource "aws_security_group" "instancia" {
  name        = "${var.nome}-instancia"
  description = "Acesso web ao assistente, restrito aos IPs liberados"
  vpc_id      = data.aws_vpc.padrao.id

  tags = { Name = "${var.nome}-instancia" }
}

# HTTPS: é por onde medassist.ia4.dev responde.
resource "aws_vpc_security_group_ingress_rule" "https" {
  for_each = toset(var.ips_liberados)

  security_group_id = aws_security_group.instancia.id
  cidr_ipv4         = each.value
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "HTTPS para ${each.value}"
}

# HTTP: redireciona para HTTPS e serve para o Caddy validar o certificado
# junto ao Let's Encrypt. Por isso acompanha a mesma liberação da 443.
resource "aws_vpc_security_group_ingress_rule" "http" {
  for_each = toset(var.ips_liberados)

  security_group_id = aws_security_group.instancia.id
  cidr_ipv4         = each.value
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  description       = "HTTP para ${each.value}"
}

resource "aws_vpc_security_group_egress_rule" "saida" {
  security_group_id = aws_security_group.instancia.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Saida liberada: baixar modelo, pacotes e emitir certificado"
}
