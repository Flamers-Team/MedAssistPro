# Papel que a instância assume para o Session Manager funcionar.
# Sem isso não há terminal, porque não abrimos porta de SSH.
resource "aws_iam_role" "instancia" {
  name = "${var.nome}-instancia"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# Política gerenciada pela AWS: o mínimo que o agente do SSM precisa.
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.instancia.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "instancia" {
  name = "${var.nome}-instancia"
  role = aws_iam_role.instancia.name
}
