# Grupo de segurança: nenhuma porta de SSH. O terminal vem do Session Manager,
# que sai da instância para a AWS, sem porta de entrada.
resource "aws_security_group" "instancia" {
  name        = "${var.nome}-instancia"
  description = "Acesso web ao assistente, restrito aos IPs liberados"
  vpc_id      = data.aws_vpc.padrao.id

  tags = { Name = "${var.nome}-instancia" }
}

# As regras de entrada (portas 80 e 443) NÃO são gerenciadas aqui.
# Quem abre e fecha é o medassist.sh (--liberar-publico / --liberar-ip), que
# usa a API da AWS. Assim o script e a esteira mudam o acesso sem rodar
# Terraform, e um `terraform apply` não desfaz a regra em vigor.
# A máquina nasce fechada: nenhuma porta de entrada até alguém liberar.

resource "aws_vpc_security_group_egress_rule" "saida" {
  security_group_id = aws_security_group.instancia.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Saida liberada: baixar modelo, pacotes e emitir certificado"
}
