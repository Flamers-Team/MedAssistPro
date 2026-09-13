# Preparação inicial da máquina: instala o Caddy e cria a pasta do projeto.
# O resto (clonar o repo, instalar dependências, baixar o modelo) é feito
# depois, pelo terminal do Session Manager.
locals {
  preparacao = <<-SCRIPT
    #!/bin/bash
    set -euxo pipefail

    apt-get update
    apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl

    # Repositório oficial do Caddy
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
      | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
      > /etc/apt/sources.list.d/caddy-stable.list
    apt-get update
    apt-get install -y caddy

    mkdir -p /opt/medassist
    chown ubuntu:ubuntu /opt/medassist
  SCRIPT
}

resource "aws_instance" "assistente" {
  ami                    = data.aws_ami.deep_learning.id
  instance_type          = var.tipo_instancia
  subnet_id              = data.aws_subnets.padrao.ids[0]
  vpc_security_group_ids = [aws_security_group.instancia.id]
  iam_instance_profile   = aws_iam_instance_profile.instancia.name
  user_data              = local.preparacao

  root_block_device {
    volume_size = var.tamanho_disco_gb
    volume_type = "gp3"
    encrypted   = true
    # O disco sobrevive ao desligamento; só some se a instância for destruída.
    delete_on_termination = true
  }

  tags = { Name = "${var.nome}-gpu" }

  # Trocar de imagem recria a máquina e apaga o disco. Como a imagem nova sai
  # toda semana, ignoramos a mudança: a atualização é decisão manual.
  lifecycle {
    ignore_changes = [ami]
  }
}
